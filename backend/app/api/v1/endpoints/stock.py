from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.api.v1.deps import get_db
from app.crud.stock import crud_stock
from app.crud.recipe import crud_recipe
from app.schemas.stock import (
    StockRead,
    StockReceive,
    StockWriteOff,
    StockCheckRequest,
    StockCheckResponse,
    StockExpiringResponse,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient

router = APIRouter(prefix="/stock", tags=["stock"])

@router.get(
    "/",
    response_model=dict,
    summary="Получить список складских остатков",
    description="Возвращает список всех складских остатков с пагинацией и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком остатков"},
    }
)
async def get_stock(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    ingredient_id: Optional[int] = Query(default=None, description="Фильтр по ингредиенту"),
    expiring_days: Optional[int] = Query(default=None, ge=1, description="Показать истекающие через N дней"),
) -> dict:
    """
    Получить список складских остатков.
    """
    result = await crud_stock.get_all_stock(
        db,
        page=page,
        limit=limit,
        ingredient_id=ingredient_id,
        expiring_days=expiring_days
    )
    
    items = [
        StockRead.model_validate(item) 
        for item in result["items"]
    ]
    
    return {
        "items": items,
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
        "pages": result["pages"],
    }

@router.get(
    "/expiring-soon",
    response_model=StockExpiringResponse,
    summary="Получить истекающие ингредиенты",
    description="Возвращает список ингредиентов с истекающим сроком годности.",
    responses={
        200: {"description": "Успешный ответ со списком истекающих ингредиентов"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_expiring_soon(
    days: int = Query(default=7, ge=1, le=30, description="Порог в днях для фильтрации"),
    db: AsyncSession = Depends(get_db),
) -> StockExpiringResponse:
    """
    Получить ингредиенты с истекающим сроком годности.
    
    Бизнес-логика:
    - Возвращает ингредиенты, истекающие в ближайшие N дней
    - Сортировка по сроку годности (самые срочные первыми)
    - Используется для FIFO-учёта и предотвращения порчи сырья
    
    Пример использования:
    Ежедневная проверка склада для выявления ингредиентов,
    которые нужно использовать в первую очередь.
    """
    expiring_list = await crud_stock.get_expiring_soon(db, days=days)
    
    return StockExpiringResponse(
        expiring_soon=expiring_list,
        threshold_days=days
    )

@router.get(
    "/history",
    response_model=dict,
    summary="Получить историю операций со складом",
    description="Возвращает историю поступлений и списаний сырья.",
    responses={
        200: {"description": "Успешный ответ с историей операций"},
    }
)
async def get_stock_history(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    ingredient_id: Optional[int] = Query(default=None, description="Фильтр по ингредиенту"),
    operation_type: Optional[str] = Query(default=None, regex="^(receive|write-off)$", description="Тип операции"),
    date_from: Optional[date] = Query(default=None, description="Дата от"),
    date_to: Optional[date] = Query(default=None, description="Дата до"),
) -> dict:
    """
    Получить историю операций со складом.
    
    Примечание:
    На данном этапе реализована заглушка. Для полноценной реализации
    требуется модель StockTransaction для хранения истории операций.
    """
    # TODO: Реализовать полноценную историю операций
    return {
        "items": [],
        "total": 0,
        "page": page,
        "limit": limit,
        "pages": 0,
        "message": "Функционал истории операций в разработке"
    }

@router.post(
    "/receive",
    response_model=StockRead,
    status_code=status.HTTP_201_CREATED,
    summary="Поступление сырья на склад",
    description="Регистрирует поступление новой партии сырья на склад.",
    responses={
        201: {"description": "Сырьё успешно принято на склад"},
        400: {"description": "Ошибка валидации (срок годности в прошлом)"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def receive_stock(
    obj_in: StockReceive,
    db: AsyncSession = Depends(get_db),
) -> StockRead:
    """
    Зарегистрировать поступление сырья на склад.

    Бизнес-логика:
    - Проверка срока годности (не может быть в прошлом)
    - Если запись уже есть — обновляется количество и срок
    - Если нет — создаётся новая запись
    """
    return await crud_stock.receive_stock(db, obj_in=obj_in)

@router.post(
    "/write-off",
    response_model=StockRead,
    status_code=status.HTTP_200_OK,
    summary="Списание сырья со склада",
    description="Регистрирует списание сырья (для производства или по другим причинам).",
    responses={
        200: {"description": "Сырьё успешно списано"},
        404: {"description": "Ингредиент не найден на складе"},
        409: {"description": "Недостаточно сырья на складе"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def write_off_stock(
    obj_in: StockWriteOff,
    db: AsyncSession = Depends(get_db),
) -> StockRead:
    """
    Зарегистрировать списание сырья со склада.
    
    Бизнес-логика:
    - Проверка достаточности количества (нельзя списать больше, чем есть)
    - Списание по FIFO (сначала партии с ближайшим сроком годности)
    """
    return await crud_stock.write_off_stock(db, obj_in=obj_in)

@router.post(
    "/check-availability",
    response_model=StockCheckResponse,
    summary="Проверить достаточность сырья",
    description="Проверяет наличие достаточного количества сырья для выполнения заказов.",
    responses={
        200: {"description": "Проверка выполнена успешно"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def check_availability(
    obj_in: StockCheckRequest,
    db: AsyncSession = Depends(get_db),
) -> StockCheckResponse:
    """
    Проверить достаточность сырья для выполнения заказов.
    
    Бизнес-логика:
    - Проверка каждого ингредиента из запроса
    - Расчёт дефицита
    - Предупреждения о сроках годности (если до истечения ≤ 7 дней)
    
    Пример использования:
    Перед формированием производственного плана планировщик проверяет,
    хватит ли сырья для выполнения всех активных заказов.
    """
    return await crud_stock.check_availability(db, obj_in=obj_in)


@router.post(
    "/calculate-requirement",
    response_model=dict,
    summary="Рассчитать потребность в сырье",
    description="Рассчитывает потребность в ингредиентах на основе рецептур и количества продукции.",
    responses={
        200: {"description": "Расчёт выполнен успешно"},
        404: {"description": "Рецептура не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def calculate_requirement(
    recipe_id: int = Query(..., gt=0, description="ID рецептуры"),
    quantity: int = Query(..., gt=0, description="Количество изделий для производства"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Рассчитать потребность в ингредиентах для производства.
    """
    
    # Жадная загрузка рецептуры с ингредиентами и вложенными ингредиентами
    query = (
        select(Recipe)
        .options(
            selectinload(Recipe.ingredients)
            .selectinload(RecipeIngredient.ingredient)  # ← Ключевое исправление!
        )
        .where(Recipe.id == recipe_id)
    )
    result = await db.execute(query)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура ID {recipe_id} не найдена"
        )
    
    # Рассчитываем потребность
    requirements = []
    for ingredient_link in recipe.ingredients:
        requirements.append({
            "ingredient_id": ingredient_link.ingredient_id,
            "ingredient_name": ingredient_link.ingredient.name,  # ← Теперь работает!
            "quantity_per_unit": ingredient_link.quantity,
            "total_required": ingredient_link.quantity * quantity,
            "unit": ingredient_link.ingredient.unit,  # ← Также доступно
        })
    
    return {
        "recipe_id": recipe_id,
        "recipe_name": recipe.name,
        "production_quantity": quantity,
        "requirements": requirements,
    }

@router.get(
    "/{ingredient_id}",
    response_model=StockRead,
    summary="Получить остаток по ингредиенту",
    description="Возвращает складской остаток для конкретного ингредиента.",
    responses={
        200: {"description": "Успешный ответ с данными остатка"},
        404: {"description": "Ингредиент не найден на складе"},
    }
)
async def get_stock_by_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
) -> StockRead:
    """
    Получить складской остаток по ID ингредиента.
    """
    stock = await crud_stock.get_stock_by_ingredient(db, ingredient_id=ingredient_id)
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ингредиент ID {ingredient_id} не найден на складе"
        )
    
    return stock


@router.get(
    "/{ingredient_id}/total",
    response_model=dict,
    summary="Получить общее количество ингредиента",
    description="Возвращает суммарное количество ингредиента по всем партиям.",
    responses={
        200: {"description": "Успешный ответ с общим количеством"},
    }
)
async def get_total_quantity(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Получить общее количество ингредиента на складе (сумма всех партий).
    """
    total = await crud_stock.get_total_quantity(db, ingredient_id=ingredient_id)
    
    return {
        "ingredient_id": ingredient_id,
        "total_quantity": total,
    }