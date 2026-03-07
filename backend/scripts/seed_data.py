"""
Скрипт заполнения базы данных тестовыми данными для СУРПП.
Идемпотентен — можно запускать без дублирования данных.

Запуск:
    docker-compose exec backend python -m scripts.seed_data.py
"""

import logging
import sys
import os
from datetime import datetime, date, timedelta
from typing import List

sys.path.insert(0, '/app/backend')

from app.models.ingredient import Ingredient
from app.models.equipment import Equipment
from app.models.competence import Competence
from app.models.employee import Employee
from app.models.employee_competence import EmployeeCompetence
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.operation import Operation
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.stock import Stock
from app.models.schedule import Schedule

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SEED_DATA")

# Конфигурация БД
DATABASE_URL = os.getenv("DB_SYNC")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def check_table_empty(session: Session, model) -> bool:
    """Проверяет, пуста ли таблица модели"""
    return session.query(model).count() == 0


def get_or_create(session: Session, model, **kwargs):
    """Получает существующую запись или создаёт новую"""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    instance = model(**kwargs)
    session.add(instance)
    session.flush()
    return instance, True


# ============================================================================
# ФУНКЦИИ ЗАПОЛНЕНИЯ
# ============================================================================

def seed_ingredients(session: Session) -> List[Ingredient]:
    """Заполнение справочника ингредиентов"""
    logger.info("Заполнение ингредиентов...")
    
    if not check_table_empty(session, Ingredient):
        logger.info("  ✓ Ингредиенты уже существуют")
        return session.query(Ingredient).all()
    
    ingredients_data = [
        {"name": "Мука пшеничная", "unit": "кг", "shelf_life_days": 365},
        {"name": "Сахар", "unit": "кг", "shelf_life_days": 730},
        {"name": "Яйца куриные", "unit": "шт", "shelf_life_days": 30},
        {"name": "Масло сливочное", "unit": "кг", "shelf_life_days": 90},
        {"name": "Какао-порошок", "unit": "кг", "shelf_life_days": 365},
        {"name": "Молоко", "unit": "л", "shelf_life_days": 14},
        {"name": "Сливки 33%", "unit": "л", "shelf_life_days": 10},
        {"name": "Шоколад тёмный", "unit": "кг", "shelf_life_days": 365},
        {"name": "Ванильный сахар", "unit": "г", "shelf_life_days": 730},
        {"name": "Разрыхлитель теста", "unit": "г", "shelf_life_days": 365},
        {"name": "Соль", "unit": "г", "shelf_life_days": 1095},
        {"name": "Джем клубничный", "unit": "кг", "shelf_life_days": 180},
    ]
    
    ingredients = []
    for data in ingredients_data:
        ingredient, created = get_or_create(session, Ingredient, name=data["name"])
        if created:
            ingredient.unit = data["unit"]
            ingredient.shelf_life_days = data["shelf_life_days"]
            logger.info(f"  + {ingredient.name}")
        ingredients.append(ingredient)
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(ingredients)} ингредиентов")
    return ingredients


def seed_equipment(session: Session) -> List[Equipment]:
    """Заполнение справочника оборудования"""
    logger.info("Заполнение оборудования...")
    
    if not check_table_empty(session, Equipment):
        logger.info("  ✓ Оборудование уже существует")
        return session.query(Equipment).all()
    
    equipment_data = [
        {"name": "Тестомесильная машина", "quantity": 2},
        {"name": "Пекарский шкаф", "quantity": 3},
        {"name": "Холодильный шкаф", "quantity": 2},
        {"name": "Миксер промышленный", "quantity": 2},
        {"name": "Расстоечный шкаф", "quantity": 1},
        {"name": "Взбивальная машина", "quantity": 1},
        {"name": "Кондитерский стол", "quantity": 4},
    ]
    
    equipment_list = []
    for data in equipment_data:
        equipment, created = get_or_create(session, Equipment, name=data["name"])
        if created:
            equipment.quantity = data["quantity"]
            logger.info(f"  + {equipment.name} ({equipment.quantity} шт)")
        equipment_list.append(equipment)
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(equipment_list)} единиц оборудования")
    return equipment_list


def seed_competences(session: Session) -> List[Competence]:
    """Заполнение справочника компетенций"""
    logger.info("Заполнение компетенций...")
    
    if not check_table_empty(session, Competence):
        logger.info("  ✓ Компетенции уже существуют")
        return session.query(Competence).all()
    
    competences_data = [
        {"name": "Кондитер 3 разряда", "description": "Базовые операции: замес, выпечка простых изделий"},
        {"name": "Кондитер 4 разряда", "description": "Изготовление тортов и пирожных средней сложности"},
        {"name": "Кондитер 5 разряда", "description": "Изготовление сложных тортов, декорирование, руководство"},
        {"name": "Помощник кондитера", "description": "Подготовительные операции, уборка"},
    ]
    
    competences = []
    for data in competences_data:
        competence, created = get_or_create(session, Competence, name=data["name"])
        if created:
            competence.description = data["description"]
            logger.info(f"  + {competence.name}")
        competences.append(competence)
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(competences)} компетенций")
    return competences


def seed_employees(session: Session, competences: List[Competence]) -> List[Employee]:
    """Заполнение справочника сотрудников"""
    logger.info("Заполнение сотрудников...")
    
    if not check_table_empty(session, Employee):
        logger.info("  ✓ Сотрудники уже существуют")
        return session.query(Employee).all()
    
    employees_data = [
        {"name": "Иванов Алексей Андреевич", "competence_names": ["Кондитер 3 разряда"]},
        {"name": "Петров Борис Борисович", "competence_names": ["Кондитер 4 разряда"]},
        {"name": "Сидоров Виктор Викторович", "competence_names": ["Кондитер 5 разряда"]},
        {"name": "Кузнецова Елена Дмитриевна", "competence_names": ["Кондитер 4 разряда"]},
        {"name": "Смирнов Иван Петрович", "competence_names": ["Помощник кондитера"]},
    ]
    
    employees = []
    for data in employees_data:
        employee, created = get_or_create(session, Employee, name=data["name"])
        if created:
            employee.active = True
            logger.info(f"  + {employee.name}")
        employees.append(employee)
        
        # Назначаем компетенции
        for comp_name in data["competence_names"]:
            competence = next((c for c in competences if c.name == comp_name), None)
            if competence:
                emp_comp, _ = get_or_create(
                    session, EmployeeCompetence,
                    employee_id=employee.employee_id,
                    competence_id=competence.competence_id
                )
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(employees)} сотрудников")
    return employees


def seed_recipes(session: Session, ingredients: List[Ingredient], 
                 equipment: List[Equipment], competences: List[Competence]) -> List[Recipe]:
    """Заполнение рецептур изделий"""
    logger.info("Заполнение рецептур...")
    
    if not check_table_empty(session, Recipe):
        logger.info("  ✓ Рецептуры уже существуют")
        return session.query(Recipe).all()
    
    recipes_data = [
        {
            "name": "Торт «Прага»",
            "ingredients": [
                {"name": "Мука пшеничная", "quantity": 2.0},
                {"name": "Сахар", "quantity": 1.0},
                {"name": "Яйца куриные", "quantity": 10.0},
                {"name": "Масло сливочное", "quantity": 0.5},
                {"name": "Какао-порошок", "quantity": 0.3},
                {"name": "Джем клубничный", "quantity": 0.2},
            ],
            "operations": [
                {"name": "Замес бисквитного теста", "duration_minutes": 30, 
                 "equipment_name": "Тестомесильная машина", "competence_name": "Кондитер 3 разряда"},
                {"name": "Выпечка бисквита", "duration_minutes": 45, 
                 "equipment_name": "Пекарский шкаф", "competence_name": "Кондитер 3 разряда"},
                {"name": "Охлаждение бисквита", "duration_minutes": 60, 
                 "equipment_name": "Холодильный шкаф", "competence_name": None},
                {"name": "Приготовление крема", "duration_minutes": 20, 
                 "equipment_name": "Миксер промышленный", "competence_name": "Кондитер 4 разряда"},
                {"name": "Сборка и пропитка коржей", "duration_minutes": 30, 
                 "equipment_name": "Кондитерский стол", "competence_name": "Кондитер 4 разряда"},
                {"name": "Декорирование торта", "duration_minutes": 30, 
                 "equipment_name": None, "competence_name": "Кондитер 5 разряда"},
            ]
        },
        {
            "name": "Пирожное «Картошка»",
            "ingredients": [
                {"name": "Мука пшеничная", "quantity": 0.5},
                {"name": "Сахар", "quantity": 0.3},
                {"name": "Масло сливочное", "quantity": 0.2},
                {"name": "Какао-порошок", "quantity": 0.1},
                {"name": "Молоко", "quantity": 0.2},
            ],
            "operations": [
                {"name": "Замес теста", "duration_minutes": 20, 
                 "equipment_name": "Тестомесильная машина", "competence_name": "Кондитер 3 разряда"},
                {"name": "Выпечка основы", "duration_minutes": 25, 
                 "equipment_name": "Пекарский шкаф", "competence_name": "Кондитер 3 разряда"},
                {"name": "Приготовление крема", "duration_minutes": 15, 
                 "equipment_name": "Миксер промышленный", "competence_name": "Кондитер 3 разряда"},
                {"name": "Формовка пирожных", "duration_minutes": 30, 
                 "equipment_name": "Кондитерский стол", "competence_name": "Кондитер 3 разряда"},
            ]
        },
        {
            "name": "Кекс ванильный",
            "ingredients": [
                {"name": "Мука пшеничная", "quantity": 1.0},
                {"name": "Сахар", "quantity": 0.5},
                {"name": "Яйца куриные", "quantity": 5.0},
                {"name": "Масло сливочное", "quantity": 0.3},
                {"name": "Молоко", "quantity": 0.3},
                {"name": "Ванильный сахар", "quantity": 20.0},
                {"name": "Разрыхлитель теста", "quantity": 15.0},
            ],
            "operations": [
                {"name": "Замес теста", "duration_minutes": 15, 
                 "equipment_name": "Миксер промышленный", "competence_name": "Кондитер 3 разряда"},
                {"name": "Выпечка кекса", "duration_minutes": 40, 
                 "equipment_name": "Пекарский шкаф", "competence_name": "Кондитер 3 разряда"},
                {"name": "Охлаждение", "duration_minutes": 30, 
                 "equipment_name": "Холодильный шкаф", "competence_name": None},
            ]
        },
    ]
    
    recipes = []
    for recipe_data in recipes_data:
        recipe, created = get_or_create(session, Recipe, name=recipe_data["name"])
        if created:
            logger.info(f"  + {recipe.name}")
        recipes.append(recipe)
        
        # Добавляем ингредиенты рецептуры
        for ing_data in recipe_data["ingredients"]:
            ingredient = next((i for i in ingredients if i.name == ing_data["name"]), None)
            if ingredient:
                rec_ing, _ = get_or_create(
                    session, RecipeIngredient,
                    recipe_id=recipe.recipe_id,
                    ingredient_id=ingredient.ingredient_id
                )
                rec_ing.quantity = ing_data["quantity"]
        
        # Добавляем технологические операции
        for idx, op_data in enumerate(recipe_data["operations"]):
            equip = None
            if op_data["equipment_name"]:
                equip = next((e for e in equipment if e.name == op_data["equipment_name"]), None)
            
            comp = None
            if op_data["competence_name"]:
                comp = next((c for c in competences if c.name == op_data["competence_name"]), None)
            
            operation = Operation(
                recipe_id=recipe.recipe_id,
                name=op_data["name"],
                sequence_number=idx + 1,
                duration_minutes=op_data["duration_minutes"],
                equipment_id=equip.equipment_id if equip else None,
                competence_id=comp.competence_id if comp else None
            )
            session.add(operation)
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(recipes)} рецептур")
    return recipes


def seed_stock(session: Session, ingredients: List[Ingredient]) -> List[Stock]:
    """Заполнение складских остатков"""
    logger.info("Заполнение складских остатков...")
    
    stock_data = {
        "Мука пшеничная": {"quantity": 50.0, "days_offset": 0},
        "Сахар": {"quantity": 30.0, "days_offset": 0},
        "Яйца куриные": {"quantity": 200.0, "days_offset": 0},
        "Масло сливочное": {"quantity": 10.0, "days_offset": 0},
        "Какао-порошок": {"quantity": 5.0, "days_offset": 0},
        "Молоко": {"quantity": 20.0, "days_offset": 0},
        "Сливки 33%": {"quantity": 10.0, "days_offset": 0},
        "Шоколад тёмный": {"quantity": 8.0, "days_offset": 0},
        "Ванильный сахар": {"quantity": 500.0, "days_offset": 0},
        "Разрыхлитель теста": {"quantity": 1000.0, "days_offset": 0},
        "Соль": {"quantity": 2000.0, "days_offset": 0},
        "Джем клубничный": {"quantity": 5.0, "days_offset": 0},
    }
    
    stocks = []
    for ing in ingredients:
        if ing.name in stock_data:
            data = stock_data[ing.name]
            stock, created = get_or_create(
                session, Stock,
                ingredient_id=ing.ingredient_id
            )
            if created:
                stock.quantity = data["quantity"]
                stock.received_at = datetime.now()
                stock.expiration_date = date.today() + timedelta(days=ing.shelf_life_days - data["days_offset"])
                logger.info(f"  + {ing.name}: {stock.quantity} {ing.unit}")
            stocks.append(stock)
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(stocks)} складских позиций")
    return stocks


def seed_orders(session: Session, recipes: List[Recipe]) -> List[Order]:
    """Заполнение производственных заказов"""
    logger.info("Заполнение заказов...")
    
    if not check_table_empty(session, Order):
        logger.info("  ✓ Заказы уже существуют")
        return session.query(Order).all()
    
    orders_data = [
        {
            "recipe_name": "Торт «Прага»",
            "quantity": 2,
            "due_date_offset": 1,
            "priority": 1
        },
        {
            "recipe_name": "Пирожное «Картошка»",
            "quantity": 50,
            "due_date_offset": 2,
            "priority": 2
        },
        {
            "recipe_name": "Кекс ванильный",
            "quantity": 20,
            "due_date_offset": 3,
            "priority": 3
        },
        {
            "recipe_name": "Торт «Прага»",
            "quantity": 5,
            "due_date_offset": 5,
            "priority": 1
        },
    ]
    
    orders = []
    for order_data in orders_data:
        recipe = next((r for r in recipes if r.name == order_data["recipe_name"]), None)
        if recipe:
            order = Order(
                due_date=date.today() + timedelta(days=order_data["due_date_offset"]),
                priority=order_data["priority"],
                status="new"
            )
            session.add(order)
            session.flush()
            
            order_item = OrderItem(
                order_id=order.order_id,
                recipe_id=recipe.recipe_id,
                quantity=order_data["quantity"]
            )
            session.add(order_item)
            orders.append(order)
            logger.info(f"  + Заказ #{order.order_id}: {recipe.name} x{order_data['quantity']} (до {order.due_date})")
    
    session.commit()
    logger.info(f"  ✓ Добавлено {len(orders)} заказов")
    return orders


# ============================================================================
# ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Основная функция заполнения БД"""
    logger.info("=" * 60)
    logger.info("Запуск заполнения базы данных тестовыми данными")
    logger.info("=" * 60)
    
    try:
        # Проверка подключения к БД
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Подключение к базе данных установлено")
        
        session = SessionLocal()
        
        try:
            # Последовательное заполнение таблиц
            ingredients = seed_ingredients(session)
            equipment = seed_equipment(session)
            competences = seed_competences(session)
            employees = seed_employees(session, competences)
            recipes = seed_recipes(session, ingredients, equipment, competences)
            stock = seed_stock(session, ingredients)
            orders = seed_orders(session, recipes)
            
            logger.info("=" * 60)
            logger.info("✓ Заполнение базы данных завершено успешно")
            logger.info("=" * 60)
            
            # Статистика
            logger.info("Статистика заполненных данных:")
            logger.info(f"  - Ингредиенты: {len(ingredients)}")
            logger.info(f"  - Оборудование: {len(equipment)}")
            logger.info(f"  - Компетенции: {len(competences)}")
            logger.info(f"  - Сотрудники: {len(employees)}")
            logger.info(f"  - Рецептуры: {len(recipes)}")
            logger.info(f"  - Складские позиции: {len(stock)}")
            logger.info(f"  - Заказы: {len(orders)}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"✗ Ошибка при заполнении БД: {e}", exc_info=True)
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"✗ Ошибка подключения к БД: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()