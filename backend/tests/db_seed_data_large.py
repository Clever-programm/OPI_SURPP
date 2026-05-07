"""
Расширенный скрипт заполнения базы данных для СУРПП.
Создает большой объем данных для проверки качества генетического планировщика.
"""

import logging
import sys
import os
from datetime import datetime, date, timedelta
from typing import List

sys.path.insert(0, '/app')

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
from app.core.config import settings

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SEED_LARGE")

DATABASE_URL = (
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def clear_data(session: Session):
    """Очистка всех таблиц перед заполнением"""
    logger.info("Очистка существующих данных...")
    session.execute(text("TRUNCATE TABLE schedule, stock, order_items, orders, operations, recipe_ingredients, recipes, employee_competences, employees, competences, equipment, ingredients RESTART IDENTITY CASCADE"))
    session.commit()

def seed_everything(session: Session):
    # 1. Ингредиенты
    ing_data = [
        ("Мука пшеничная", "кг"), ("Сахар", "кг"), ("Яйца куриные", "шт"), 
        ("Масло сливочное", "кг"), ("Какао", "кг"), ("Молоко", "л"),
        ("Сливки 33%", "л"), ("Шоколад", "кг"), ("Ваниль", "г"), 
        ("Соль", "г"), ("Дрожжи", "г"), ("Мед", "кг")
    ]
    ingredients = [Ingredient(name=n, unit=u, shelf_life_days=365) for n, u in ing_data]
    session.add_all(ingredients)
    session.flush()

    # 2. Оборудование (увеличенное количество)
    eq_data = [
        ("Промышленный миксер", 5), ("Пекарская печь", 4), 
        ("Расстоечный шкаф", 3), ("Холодильная камера", 3), 
        ("Стол для сборки", 8), ("Машина для замеса", 2)
    ]
    equipment = [Equipment(name=n, quantity=q) for n, q in eq_data]
    session.add_all(equipment)
    session.flush()

    # 3. Компетенции
    comp_data = ["Замес и выпечка", "Кремы и начинки", "Сборка и декор", "Упаковка"]
    competences = [Competence(name=n) for n in comp_data]
    session.add_all(competences)
    session.flush()

    # 4. Сотрудники (10 человек)
    employees = [
        Employee(name=f"Мастер {i}", active=True) for i in range(1, 11)
    ]
    session.add_all(employees)
    session.flush()
    
    # Назначаем по 2 компетенции каждому
    for i, emp in enumerate(employees):
        # Чередуем компетенции
        c1 = competences[i % 4]
        c2 = competences[(i + 1) % 4]
        session.add(EmployeeCompetence(employee_id=emp.id, competence_id=c1.id))
        session.add(EmployeeCompetence(employee_id=emp.id, competence_id=c2.id))

    # 5. Рецепты
    recipes = [
        Recipe(name="Свадебный торт"), Recipe(name="Круассаны"), 
        Recipe(name="Шоколадные капкейки"), Recipe(name="Медовик классический")
    ]
    session.add_all(recipes)
    session.flush()

    # Связи рецептов и операции
    # 0: Торт, 1: Круассаны, 2: Капкейки, 3: Медовик
    
    # Свадебный торт
    session.add(RecipeIngredient(recipe_id=recipes[0].id, ingredient_id=ingredients[0].id, quantity=2.0))
    session.add(RecipeIngredient(recipe_id=recipes[0].id, ingredient_id=ingredients[2].id, quantity=20.0))
    session.add(RecipeIngredient(recipe_id=recipes[0].id, ingredient_id=ingredients[3].id, quantity=1.0))
    
    op_data_0 = [
        ("Замес основы", 40, equipment[5].id, competences[0].id),
        ("Выпечка коржей", 60, equipment[1].id, competences[0].id),
        ("Охлаждение", 120, equipment[3].id, None),
        ("Приготовление крема", 30, equipment[0].id, competences[1].id),
        ("Сборка ярусов", 90, equipment[4].id, competences[2].id),
        ("Декорирование", 120, equipment[4].id, competences[2].id)
    ]
    for idx, (name, dur, eq_id, comp_id) in enumerate(op_data_0):
        session.add(Operation(recipe_id=recipes[0].id, name=name, sequence_number=idx+1, duration_minutes=dur, equipment_id=eq_id, competence_id=comp_id))

    # Круассаны (Замес, Расстойка, Выпечка)
    session.add(RecipeIngredient(recipe_id=recipes[1].id, ingredient_id=ingredients[0].id, quantity=5.0))
    session.add(RecipeIngredient(recipe_id=recipes[1].id, ingredient_id=ingredients[3].id, quantity=2.0))
    
    op_data_1 = [
        ("Замес слоеного теста", 50, equipment[5].id, competences[0].id),
        ("Расстойка", 90, equipment[2].id, None),
        ("Выпечка", 25, equipment[1].id, competences[0].id),
        ("Упаковка", 15, None, competences[3].id)
    ]
    for idx, (name, dur, eq_id, comp_id) in enumerate(op_data_1):
        session.add(Operation(recipe_id=recipes[1].id, name=name, sequence_number=idx+1, duration_minutes=dur, equipment_id=eq_id, competence_id=comp_id))

    # Капкейки
    session.add(RecipeIngredient(recipe_id=recipes[2].id, ingredient_id=ingredients[0].id, quantity=1.0))
    session.add(RecipeIngredient(recipe_id=recipes[2].id, ingredient_id=ingredients[2].id, quantity=6.0))
    
    op_data_2 = [
        ("Замес теста", 20, equipment[0].id, competences[0].id),
        ("Выпечка", 20, equipment[1].id, competences[0].id),
        ("Украшение кремом", 40, equipment[4].id, competences[2].id)
    ]
    for idx, (name, dur, eq_id, comp_id) in enumerate(op_data_2):
        session.add(Operation(recipe_id=recipes[2].id, name=name, sequence_number=idx+1, duration_minutes=dur, equipment_id=eq_id, competence_id=comp_id))

    # Медовик
    session.add(RecipeIngredient(recipe_id=recipes[3].id, ingredient_id=ingredients[11].id, quantity=0.5)) # Мед
    session.add(RecipeIngredient(recipe_id=recipes[3].id, ingredient_id=ingredients[0].id, quantity=1.5))
    
    op_data_3 = [
        ("Варка медовой основы", 30, None, competences[1].id),
        ("Выпечка коржей", 40, equipment[1].id, competences[0].id),
        ("Промазка кремом", 45, equipment[4].id, competences[1].id),
        ("Пропитка", 240, equipment[3].id, None)
    ]
    for idx, (name, dur, eq_id, comp_id) in enumerate(op_data_3):
        session.add(Operation(recipe_id=recipes[3].id, name=name, sequence_number=idx+1, duration_minutes=dur, equipment_id=eq_id, competence_id=comp_id))

    # 6. Склад (МНОГО ВСЕГО)
    for ing in ingredients:
        session.add(Stock(
            ingredient_id=ing.id, 
            quantity=1000.0, 
            received_at=datetime.now(),
            expiration_date=date.today() + timedelta(days=365)
        ))

    # 7. Заказы (20 штук)
    for i in range(1, 21):
        order = Order(
            due_date=date.today() + timedelta(days=random_offset(i)),
            priority=(i % 3) + 1,
            status="new"
        )
        session.add(order)
        session.flush()
        # Половина заказов - торты, половина - круассаны (заглушка)
        rid = recipes[0].id if i % 2 == 0 else recipes[2].id
        session.add(OrderItem(order_id=order.id, recipe_id=rid, quantity=random_qty(i)))

    session.commit()

def random_offset(i): return (i % 7) + 1
def random_qty(i): return (i % 5) + 1

if __name__ == "__main__":
    s = SessionLocal()
    try:
        clear_data(s)
        seed_everything(s)
        logger.info("✓ База данных заполнена расширенным набором данных")
    finally:
        s.close()
