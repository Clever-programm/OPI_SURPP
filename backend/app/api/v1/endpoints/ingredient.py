from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.crud.ingredient import crud_ingredient
from app.schemas.ingredient import (
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
)
from app.models.ingredient import Ingredient

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get(
    "/",
    response_model=dict,
    summary="Получить список ингредиентов",
    description="Возвращает список всех ингредиентов с пагинацией, сортировкой и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком ингредиентов"},
    }
)
async def get_ingredients(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    sort_by: Optional[str] = Query(default="name", description="Поле для сортировки"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$", description="Порядок сортировки"),
    name: Optional[str] = Query(default=None, description="Фильтр по названию"),
    unit: Optional[str] = Query(default=None, description="Фильтр по единице измерения"),
) -> dict:
    """
    Получить список ингредиентов с пагинацией и фильтрацией.
    """
    filters = {}
    if name:
        filters["name"] = name
    if unit:
        filters["unit"] = unit
    
    result = await crud_ingredient.get_multi(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters
    )
    
    items = [
        IngredientRead.model_validate(item) 
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
    "/{ingredient_id}",
    response_model=IngredientRead,
    summary="Получить ингредиент по ID",
    description="Возвращает детальную информацию об ингредиенте по его ID.",
    responses={
        200: {"description": "Успешный ответ с данными ингредиента"},
        404: {"description": "Ингредиент не найден"},
    }
)
async def get_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
) -> Ingredient:
    """
    Получить ингредиент по ID.
    """
    ingredient = await crud_ingredient.get(db, id=ingredient_id)
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ингредиент с ID {ingredient_id} не найден"
        )
    
    return ingredient


@router.post(
    "/",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый ингредиент",
    description="Создаёт новую запись об ингредиенте в системе.",
    responses={
        201: {"description": "Ингредиент успешно создан"},
        409: {"description": "Конфликт - ингредиент с таким именем уже существует"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_ingredient(
    obj_in: IngredientCreate,
    db: AsyncSession = Depends(get_db),
) -> Ingredient:
    """
    Создать новый ингредиент.
    """
    return await crud_ingredient.create(db, obj_in=obj_in)


@router.put(
    "/{ingredient_id}",
    response_model=IngredientRead,
    summary="Полностью обновить ингредиент",
    description="Обновляет все поля ингредиента. Поля, не указанные в запросе, будут сброшены.",
    responses={
        200: {"description": "Ингредиент успешно обновлён"},
        404: {"description": "Ингредиент не найден"},
        409: {"description": "Конфликт - новое имя уже занято"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_ingredient(
    ingredient_id: int,
    obj_in: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
) -> Ingredient:
    """
    Обновить ингредиент по ID.
    """
    ingredient = await crud_ingredient.get(db, id=ingredient_id)
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ингредиент с ID {ingredient_id} не найден"
        )
    
    return await crud_ingredient.update(db, db_obj=ingredient, obj_in=obj_in)


@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить ингредиент",
    description="Удаляет запись об ингредиенте из системы.",
    responses={
        204: {"description": "Ингредиент успешно удалён"},
        404: {"description": "Ингредиент не найден"},
    }
)
async def delete_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить ингредиент по ID.
    """
    ingredient = await crud_ingredient.get(db, id=ingredient_id)
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ингредиент с ID {ingredient_id} не найден"
        )
    
    await crud_ingredient.remove(db, id=ingredient_id)
    
    return None


@router.get(
    "/check/{name}",
    response_model=dict,
    summary="Проверить существование ингредиента",
    description="Проверяет, существует ли ингредиент с указанным названием.",
    responses={
        200: {"description": "Результат проверки"},
    }
)
async def check_ingredient_exists(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Проверить существование ингредиента по названию.
    """
    ingredient = await crud_ingredient.get_by_name(db, name=name)
    
    return {
        "exists": ingredient is not None,
        "name": name,
        "id": ingredient.id if ingredient else None,
    }


@router.post(
    "/import",
    response_model=dict,
    summary="Массовый импорт ингредиентов",
    description="Парсит ингредиенты из CSV/JSON и сохраняет в БД.",
    responses={
        200: {"description": "Импорт выполнен успешно"},
    }
)
async def import_ingredients(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Массовый импорт ингредиентов.
    """
    # TODO: Реализовать парсинг CSV/JSON и массовое создание записей
    return {"status": "ok", "imported": 0, "message": "Функционал в разработке"}