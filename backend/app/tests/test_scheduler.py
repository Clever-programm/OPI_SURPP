import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.planning_system.schedule_generator import ScheduleGeneratorService
from app.schemas.schedule import ScheduleGenerateRequest
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.recipe import Recipe
from app.models.operation import Operation
from app.models.equipment import Equipment
from app.models.employee import Employee
from app.models.stock import Stock
from app.models.recipe_ingredient import RecipeIngredient

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.mark.asyncio
async def test_generate_schedule_success(mock_db):
    # Подготовка данных
    start_date = date(2026, 4, 15)
    request = ScheduleGenerateRequest(
        start_date=start_date,
        end_date=date(2026, 4, 21),
        order_ids=[1]
    )
    
    # Мок заказа
    mock_order = MagicMock(spec=Order)
    mock_order.id = 1
    mock_order.status = "new"
    mock_order.due_date = date(2026, 4, 20)
    
    # Мок рецепта и операции
    mock_recipe = MagicMock(spec=Recipe)
    mock_recipe.id = 1
    mock_recipe.name = "Тестовый торт"
    
    mock_op = MagicMock(spec=Operation)
    mock_op.id = 1
    mock_op.name = "Замес"
    mock_op.duration_minutes = 30
    mock_op.sequence_number = 1
    mock_op.equipment_id = 1
    mock_op.competence_id = None
    
    mock_recipe.operations = [mock_op]
    
    mock_item = MagicMock(spec=OrderItem)
    mock_item.recipe_id = 1
    mock_item.recipe = mock_recipe
    mock_order.items = [mock_item]
    
    # Мок оборудования и сотрудников
    mock_equip = MagicMock(spec=Equipment)
    mock_equip.id = 1
    mock_equip.name = "Миксер"
    mock_equip.quantity = 1
    
    mock_emp = MagicMock(spec=Employee)
    mock_emp.id = 1
    mock_emp.active = True
    mock_emp.competences = []
    
    # Мок ингредиентов и склада
    mock_stock = MagicMock(spec=Stock)
    mock_stock.ingredient_id = 1
    mock_stock.quantity = 100
    mock_stock.expiration_date = date(2026, 5, 1) # Свежий
    
    mock_ri = MagicMock(spec=RecipeIngredient)
    mock_ri.ingredient_id = 1
    mock_ri.quantity = 1
    mock_ri.ingredient = MagicMock(name="Мука")
    mock_ri.ingredient.name = "Мука"

    # Настройка возвращаемых значений DB
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_order])), # Orders
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_equip])), # Equipment
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_emp])),   # Employees
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_stock])), # Stocks
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_ri])),    # RecipeIngredients
    ]
    
    service = ScheduleGeneratorService(mock_db)
    response = await service.generate(request)
    
    assert response.success is True
    assert response.orders_planned == 1
    assert response.scheduled_count > 0
    assert len(response.conflicts) == 0

@pytest.mark.asyncio
async def test_generate_schedule_ingredient_deficit(mock_db):
    # Тот же сценарий, но склад пустой
    start_date = date(2026, 4, 15)
    request = ScheduleGenerateRequest(start_date=start_date, end_date=date(2026, 4, 21), order_ids=[1])
    
    # ... (сокращенная настройка моков)
    mock_order = MagicMock(id=1, status="new", due_date=date(2026, 4, 20), items=[MagicMock(recipe_id=1, recipe=MagicMock(operations=[MagicMock(duration_minutes=10, sequence_number=1, equipment_id=1, competence_id=None, name="Op", id=1)], name="Cake"))])
    
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_order])), # Orders
        MagicMock(scalars=lambda: MagicMock(all=lambda: [MagicMock(id=1, quantity=1, name="Eq")])), # Equipment
        MagicMock(scalars=lambda: MagicMock(all=lambda: [MagicMock(id=1, active=True, competences=[])])), # Employees
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # EMPTY STOCK
        MagicMock(scalars=lambda: MagicMock(all=lambda: [MagicMock(ingredient_id=1, quantity=1, ingredient=MagicMock(name="Яйца"))])), # Req
    ]
    
    service = ScheduleGeneratorService(mock_db)
    response = await service.generate(request)
    
    assert response.orders_planned == 0
    assert response.orders_failed == 1
    assert "Дефицит" in response.conflicts[0].message

@pytest.mark.asyncio
async def test_generate_schedule_no_operations(mock_db):
    request = ScheduleGenerateRequest(start_date=date(2026, 4, 15), end_date=date(2026, 4, 21), order_ids=[1])
    
    # Заказ без операций в рецепте
    mock_order = MagicMock(id=1, status="new", due_date=date(2026, 4, 20))
    mock_item = MagicMock(recipe_id=1, recipe=MagicMock(operations=[])) # ПУСТО
    mock_order.items = [mock_item]
    
    mock_db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(all=lambda: [mock_order])), # Orders
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # Equipment
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # Employees
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # Stocks
        MagicMock(scalars=lambda: MagicMock(all=lambda: [])), # RecipeIngredients (ADDED)
    ]
    
    service = ScheduleGeneratorService(mock_db)
    response = await service.generate(request)
    
    assert response.orders_failed == 1
    assert "отсутствуют технологические операции" in response.conflicts[0].message
