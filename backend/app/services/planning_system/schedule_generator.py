from typing import List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schedule import Schedule
from app.models.order import Order
from app.models.operation import Operation
from app.models.equipment import Equipment
from app.models.employee import Employee
from app.schemas.schedule import ScheduleGenerateRequest, ScheduleGenerateResponse, ScheduleConflict


class ScheduleGeneratorService:
    """
    Сервис генерации производственного расписания.
    
    ⚠️ На данном этапе реализована ЗАГЛУШКА.
    В будущей версии здесь будет полноценный алгоритм планирования.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate(
        self, 
        obj_in: ScheduleGenerateRequest
    ) -> ScheduleGenerateResponse:
        """
        Сформировать производственное расписание.
        
        ⚠️ ЗАГЛУШКА — возвращает mock-данные.
        
        TODO: Реализовать полноценный алгоритм планирования
        (генетический, или на основе ограничений)
        """
        # Получаем заказы для планирования
        orders_query = select(Order).where(
            Order.due_date >= obj_in.start_date,
            Order.due_date <= obj_in.end_date
        )
        if obj_in.order_ids:
            orders_query = orders_query.where(Order.id.in_(obj_in.order_ids))
        
        result = await self.db.execute(orders_query)
        orders = result.scalars().all()
        
        # Получаем ресурсы
        result = await self.db.execute(select(Operation))
        operations = result.scalars().all()
        
        result = await self.db.execute(select(Equipment).where(Equipment.quantity > 0))
        equipment_list = result.scalars().all()
        
        result = await self.db.execute(select(Employee).where(Employee.active == True))
        employees = result.scalars().all()
        
        # Создаём mock-записи (демонстрация структуры)
        mock_count = min(len(orders), 5)  # Ограничиваем для демонстрации
        
        return ScheduleGenerateResponse(
            success=True,
            schedule_id=None,  # Будет установлено после сохранения
            orders_planned=mock_count,
            orders_failed=max(0, len(orders) - mock_count),
            conflicts=[],  # Заглушка: нет конфликтов
            generated_at=datetime.now()
        )


class ConflictCheckerService:
    """
    Сервис проверки конфликтов ресурсов.
    
    ⚠️ На данном этапе реализована ЗАГЛУШКА.
    
    TODO: Реализовать полноценную проверку:
    - Конфликты оборудования (две операции в одно время)
    - Конфликты сотрудников (один кондитер на двух операциях)
    - Конфликты сырья (недостаточно ингредиентов)
    - Нарушение последовательности операций
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[ScheduleConflict]:
        """
        Проверить конфликты в расписании.
        
        ⚠️ ЗАГЛУШКА — возвращает пустой список.
        """
        # TODO: Реализовать логику проверки пересечений
        return []