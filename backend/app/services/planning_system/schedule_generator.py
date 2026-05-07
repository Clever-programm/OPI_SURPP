import random
import copy
from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.recipe import Recipe
from app.models.operation import Operation
from app.models.equipment import Equipment
from app.models.employee import Employee
from app.models.stock import Stock
from app.models.recipe_ingredient import RecipeIngredient
from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleGenerateRequest, ScheduleGenerateResponse, ScheduleConflict

# Коэффициенты штрафов (теперь без просрочки ингредиентов, т.к. это блокирующее условие)
PENALTY_WEIGHTS = {
    "tardiness": 2000,
    "earliness": 50,
    "process_gap": 20,
    "idle_time": 2
}

class Task:
    def __init__(self, op_id: int, order_id: int, equipment_id: Optional[int], 
                 competence_id: Optional[int], duration: int, recipe_name: str, 
                 op_name: str, due_date: date, recipe_id: int):
        self.op_id = op_id
        self.order_id = order_id
        self.equipment_id = equipment_id
        self.competence_id = competence_id
        self.duration = duration
        self.display_name = f"{recipe_name}: {op_name}"
        self.due_date = datetime.combine(due_date, datetime.max.time())
        self.recipe_id = recipe_id

class ResourceManager:
    def __init__(self, equipment: List[Equipment], employees: List[Employee], stocks: List[Stock], 
                 recipe_ingredients: Dict[int, List[Dict[str, Any]]]):
        self.equipment_capacity = {e.id: e.quantity for e in equipment}
        self.equipment_names = {e.id: e.name for e in equipment}
        self.equipment_usage: Dict[int, List[Tuple[datetime, datetime]]] = {e.id: [] for e in equipment}
        
        self.employee_competences = {emp.id: {ec.competence_id for ec in emp.competences} for emp in employees}
        self.employee_busy_until: Dict[int, datetime] = {emp.id: datetime.min for emp in employees}
        
        # Виртуальный склад: {ingredient_id: [Stock(qty, exp_date)]}
        self.stocks: Dict[int, List[Stock]] = {}
        for s in stocks:
            if s.ingredient_id not in self.stocks:
                self.stocks[s.ingredient_id] = []
            self.stocks[s.ingredient_id].append(copy.copy(s))
            
        # Требования рецептов: {recipe_id: [{ing_id, qty}]}
        self.recipe_reqs = recipe_ingredients

    def check_and_consume_ingredients(self, recipe_id: int, time_at: datetime, consume: bool = False) -> Tuple[bool, Optional[str]]:
        """Проверяет наличие непросроченных ингредиентов. Если consume=True, вычитает их."""
        reqs = self.recipe_reqs.get(recipe_id, [])
        for req in reqs:
            ing_id = req["ingredient_id"]
            needed = req["quantity"]
            ing_name = req["ingredient_name"]
            
            # Ищем на складе непросроченные партии
            available_qty = 0
            valid_batches = []
            if ing_id in self.stocks:
                for batch in self.stocks[ing_id]:
                    batch_exp = datetime.combine(batch.expiration_date, datetime.max.time()) if batch.expiration_date else datetime.max
                    if batch_exp >= time_at and batch.quantity > 0:
                        available_qty += batch.quantity
                        valid_batches.append(batch)
            
            if available_qty < needed:
                return False, f"Дефицит ингредиента '{ing_name}' (нужно {needed}, доступно {available_qty})"
            
            if consume:
                # Вычитаем из партий (сначала те, что портятся быстрее)
                valid_batches.sort(key=lambda x: x.expiration_date or date.max)
                remaining = needed
                for batch in valid_batches:
                    take = min(batch.quantity, remaining)
                    batch.quantity -= take
                    remaining -= take
                    if remaining <= 0: break
                    
        return True, None

    def is_equipment_available(self, equipment_id: int, start: datetime, duration_mins: int) -> bool:
        if not equipment_id: return True
        limit = self.equipment_capacity.get(equipment_id, 0)
        end = start + timedelta(minutes=duration_mins)
        overlap = sum(1 for s, e in self.equipment_usage[equipment_id] if not (end <= s or start >= e))
        return overlap < limit

    def find_available_employee(self, competence_id: int, start: datetime) -> Optional[int]:
        eligible = [eid for eid, comps in self.employee_competences.items() if not competence_id or competence_id in comps]
        # Ищем того, кто свободен к моменту start
        best_emp = None
        for eid in eligible:
            if self.employee_busy_until[eid] <= start:
                return eid
        return None

class Individual:
    def __init__(self, chromosome: List[int]):
        self.chromosome = chromosome
        self.fitness = float('inf')
        self.schedule_entries: List[Schedule] = []
        self.failed_orders: Dict[int, str] = {} # {order_id: reason}
        self.metrics = {}

class GAOptimizer:
    def __init__(self, tasks_by_order: Dict[int, List[Task]], 
                 equipment: List[Equipment], employees: List[Employee], 
                 stocks: List[Stock], recipe_reqs: Dict[int, List[Dict[str, Any]]],
                 planning_start: datetime, pop_size=50, generations=100):
        self.tasks_by_order = tasks_by_order
        self.equipment = equipment
        self.employees = employees
        self.stocks = stocks
        self.recipe_reqs = recipe_reqs
        self.planning_start = planning_start
        self.pop_size = pop_size
        self.generations = generations

    def _decode(self, individual: Individual):
        res_manager = ResourceManager(self.equipment, self.employees, self.stocks, self.recipe_reqs)
        order_last_end: Dict[int, datetime] = {oid: self.planning_start for oid in self.tasks_by_order}
        order_op_idx: Dict[int, int] = {oid: 0 for oid in self.tasks_by_order}
        
        entries = []
        tardiness_h = 0
        earliness_h = 0
        gap_h = 0
        
        # Сначала проверяем ингредиенты для всего заказа (упрощенно: в момент старта первой операции)
        # Но в реальности лучше проверять перед постановкой каждой операции
        
        for order_id in individual.chromosome:
            if order_id in individual.failed_orders: continue
            
            idx = order_op_idx[order_id]
            task = self.tasks_by_order[order_id][idx]
            
            # Если это первая операция заказа, проверяем и резервируем ингредиенты
            if idx == 0:
                can_start, reason = res_manager.check_and_consume_ingredients(task.recipe_id, order_last_end[order_id], consume=True)
                if not can_start:
                    individual.failed_orders[order_id] = reason
                    continue

            # Поиск окна
            current_t = order_last_end[order_id]
            scheduled = False
            while not scheduled:
                if res_manager.is_equipment_available(task.equipment_id, current_t, task.duration):
                    emp_id = res_manager.find_available_employee(task.competence_id, current_t)
                    if emp_id:
                        actual_end = current_t + timedelta(minutes=task.duration)
                        entries.append(Schedule(
                            order_id=task.order_id, operation_id=task.op_id, equipment_id=task.equipment_id,
                            employee_id=emp_id, start_time=current_t, end_time=actual_end,
                            duration_minutes=task.duration, name=task.display_name
                        ))
                        # Занимаем ресурсы
                        if task.equipment_id: res_manager.equipment_usage[task.equipment_id].append((current_t, actual_end))
                        res_manager.employee_busy_until[emp_id] = actual_end
                        order_last_end[order_id] = actual_end
                        order_op_idx[order_id] += 1
                        scheduled = True
                        break
                current_t += timedelta(minutes=15)
                if current_t > self.planning_start + timedelta(days=30): # Лимит поиска
                    individual.failed_orders[order_id] = "Не удалось найти временное окно для ресурсов"
                    break

            # Расчет штрафов при завершении заказа
            if order_op_idx[order_id] == len(self.tasks_by_order[order_id]):
                finish_t = order_last_end[order_id]
                if finish_t > task.due_date:
                    tardiness_h += (finish_t - task.due_date).total_seconds() / 3600
                fresh_limit = task.due_date - timedelta(hours=6)
                if finish_t < fresh_limit:
                    earliness_h += (fresh_limit - finish_t).total_seconds() / 3600

        # Fitness = Штрафы + Огромный штраф за каждый проваленный заказ
        fitness = (tardiness_h * PENALTY_WEIGHTS["tardiness"] + 
                   earliness_h * PENALTY_WEIGHTS["earliness"] +
                   len(individual.failed_orders) * 100000) # Максимальный приоритет выполнения
        
        individual.fitness = fitness
        individual.schedule_entries = entries
        individual.metrics = {"tardiness": tardiness_h, "earliness": earliness_h, "failed": len(individual.failed_orders)}

    def optimize(self) -> Individual:
        base_gene = []
        for oid, tasks in self.tasks_by_order.items(): base_gene.extend([oid] * len(tasks))
        population = [Individual(random.sample(base_gene, len(base_gene))) for _ in range(self.pop_size)]
        for ind in population: self._decode(ind)
        
        for gen in range(self.generations):
            population.sort(key=lambda x: x.fitness)
            new_pop = population[:5]
            while len(new_pop) < self.pop_size:
                p1 = min(random.sample(population, 3), key=lambda x: x.fitness)
                p2 = min(random.sample(population, 3), key=lambda x: x.fitness)
                child = Individual(self._crossover(p1.chromosome, p2.chromosome))
                if random.random() < 0.2: self._mutate(child.chromosome)
                self._decode(child)
                new_pop.append(child)
            population = new_pop
        return min(population, key=lambda x: x.fitness)

    def _crossover(self, g1, g2):
        size = len(g1)
        child = [None] * size
        indices = sorted(random.sample(range(size), size // 2))
        for i in indices: child[i] = g1[i]
        counts = {oid: g1.count(oid) for oid in self.tasks_by_order}
        cur_counts = {oid: 0 for oid in self.tasks_by_order}
        for val in child:
            if val is not None: cur_counts[val] += 1
        # Собираем оставшиеся гены из g2, соблюдая количество вхождений
        g2_rem = []
        cur_counts_rem = {oid: 0 for oid in self.tasks_by_order}
        for val in child:
            if val is not None: cur_counts_rem[val] += 1
            
        for val in g2:
            if cur_counts_rem[val] < counts[val]:
                g2_rem.append(val)
                cur_counts_rem[val] += 1
        
        r_idx = 0
        for i in range(size):
            if child[i] is None:
                child[i] = g2_rem[r_idx]
                r_idx += 1
        return child

    def _mutate(self, gene):
        if len(gene) < 2:
            return
        idx1, idx2 = random.sample(range(len(gene)), 2)
        gene[idx1], gene[idx2] = gene[idx2], gene[idx1]

class ScheduleGeneratorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, request: ScheduleGenerateRequest) -> ScheduleGenerateResponse:
        planning_start = datetime.combine(request.start_date, datetime.min.time())
        
        # 1. Загрузка данных
        orders_query = (
            select(Order)
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.recipe)
                .selectinload(Recipe.operations)
            )
        )
        
        if request.order_ids:
            # Если указаны конкретные ID, берем их все, кроме уже выполненных
            orders_query = orders_query.where(Order.id.in_(request.order_ids))
            orders_query = orders_query.where(Order.status != "completed")
        else:
            # Иначе берем новые/запланированные и фильтруем по дате
            orders_query = orders_query.where(Order.status.in_(["new", "planned"]))
            orders_query = orders_query.where(Order.due_date >= request.start_date)
        
        orders = (await self.db.execute(orders_query)).scalars().all()
        
        equipment = (await self.db.execute(select(Equipment))).scalars().all()
        employees = (await self.db.execute(select(Employee).options(selectinload(Employee.competences)).where(Employee.active == True))).scalars().all()
        stocks = (await self.db.execute(select(Stock).where(Stock.quantity > 0))).scalars().all()
        
        # Подготовка данных о требованиях рецептов
        recipe_reqs = {}
        for order in orders:
            for item in order.items:
                if item.recipe_id not in recipe_reqs:
                    ri_query = select(RecipeIngredient).options(selectinload(RecipeIngredient.ingredient)).where(RecipeIngredient.recipe_id == item.recipe_id)
                    ri_result = (await self.db.execute(ri_query)).scalars().all()
                    recipe_reqs[item.recipe_id] = [
                        {"ingredient_id": ri.ingredient_id, "quantity": ri.quantity, "ingredient_name": ri.ingredient.name}
                        for ri in ri_result
                    ]

        tasks_by_order = {}
        pre_planning_failed_orders = {}
        
        for order in orders:
            order_tasks = [
                Task(op.id, order.id, op.equipment_id, op.competence_id, op.duration_minutes, item.recipe.name, op.name, order.due_date, item.recipe_id)
                for item in order.items for op in sorted(item.recipe.operations, key=lambda x: x.sequence_number)
            ]
            if order_tasks:
                tasks_by_order[order.id] = order_tasks
            else:
                pre_planning_failed_orders[order.id] = "В рецепте изделия отсутствуют технологические операции"

        if not tasks_by_order:
            # Если вообще нечего планировать, возвращаем ошибки только из пред-проверки
            conflicts = [
                ScheduleConflict(
                    conflict_type="sequence",
                    message=f"Заказ #{oid} не запланирован: {reason}",
                    affected_orders=[oid]
                ) for oid, reason in pre_planning_failed_orders.items()
            ]
            return ScheduleGenerateResponse(
                success=True, orders_planned=0, orders_failed=len(pre_planning_failed_orders),
                scheduled_count=0, conflicts=conflicts, message="Нет доступных задач для планирования"
            )

        # 2. Оптимизация
        optimizer = GAOptimizer(tasks_by_order, list(equipment), list(employees), list(stocks), recipe_reqs, planning_start)
        best = optimizer.optimize()
        
        # Объединяем ошибки
        all_failed_orders = {**pre_planning_failed_orders, **best.failed_orders}

        # 3. Сохранение и формирование ответа
        conflicts = []
        for oid, reason in all_failed_orders.items():
            conflicts.append(ScheduleConflict(
                conflict_type="ingredient" if "ингредиента" in reason else "sequence",
                message=f"Заказ #{oid} не запланирован: {reason}",
                affected_orders=[oid]
            ))

        if not request.dry_run:
            for s in best.schedule_entries: self.db.add(s)
            for order in orders:
                if order.id not in all_failed_orders: order.status = "planned"
            await self.db.commit()

        msg = f"Планирование завершено. Успешно: {len(orders)-len(all_failed_orders)}. Ошибок: {len(all_failed_orders)}."
        return ScheduleGenerateResponse(
            success=True, 
            orders_planned=len(orders)-len(all_failed_orders), 
            orders_failed=len(all_failed_orders),
            scheduled_count=len(best.schedule_entries),
            conflicts=conflicts, 
            message=msg
        )


class ConflictCheckerService:
    """
    Сервис проверки расписания на наличие накладок.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[ScheduleConflict]:
        # TODO: Реализовать логику выявления пересечений в БД
        return []

