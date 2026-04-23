from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.crud.recipe import crud_recipe
from app.schemas.recipe import (
    RecipeCreate,
    RecipeRead,
    RecipeUpdate,
    RecipeWithDetails,
)
from app.schemas.recipe_ingredient import (
    RecipeIngredientCreate,
    RecipeIngredientRead,
)
from app.schemas.operation import (
    OperationCreate,
    OperationRead,
    OperationUpdate,
)
from pydantic import BaseModel, Field


class RecipeIngredientQuantityUpdate(BaseModel):
    """Схема для обновления количества ингредиента в рецептуре."""
    quantity: float = Field(..., gt=0, description="Новое количество ингредиента")

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.get(
    "/",
    response_model=dict,
    summary="Получить список рецептур",
    description="Возвращает список всех рецептур с пагинацией, сортировкой и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком рецептур"},
    }
)
async def get_recipes(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    sort_by: Optional[str] = Query(default="name", description="Поле для сортировки"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$", description="Порядок сортировки"),
    name: Optional[str] = Query(default=None, description="Фильтр по названию"),
) -> dict:
    """
    Получить список рецептур с пагинацией и фильтрацией.
    """
    filters = {}
    if name:
        filters["name"] = name
    
    result = await crud_recipe.get_multi(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters
    )
    
    items = [
        RecipeRead.model_validate(item) 
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
    "/{recipe_id}",
    response_model=RecipeWithDetails,
    summary="Получить рецептуру с деталями",
    description="Возвращает детальную информацию о рецептуре включая ингредиенты и операции.",
    responses={
        200: {"description": "Успешный ответ с данными рецептуры"},
        404: {"description": "Рецептура не найдена"},
    }
)
async def get_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
) -> RecipeWithDetails:
    """
    Получить рецептуру по ID с полным составом.
    """
    recipe = await crud_recipe.get_with_details(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    return recipe


@router.post(
    "/",
    response_model=RecipeWithDetails,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую рецептуру",
    description="Создаёт новую рецептуру с ингредиентами и технологическими операциями.",
    responses={
        201: {"description": "Рецептура успешно создана"},
        409: {"description": "Конфликт - рецептура с таким именем уже существует"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_recipe(
    obj_in: RecipeCreate,
    db: AsyncSession = Depends(get_db),
) -> RecipeWithDetails:
    """
    Создать новую рецептуру.
    """
    return await crud_recipe.create(db, obj_in=obj_in)


@router.put(
    "/{recipe_id}",
    response_model=RecipeRead,
    summary="Полностью обновить рецептуру",
    description="Обновляет основные поля рецептуры. Для изменения состава используйте вложенные эндпоинты.",
    responses={
        200: {"description": "Рецептура успешно обновлена"},
        404: {"description": "Рецептура не найдена"},
        409: {"description": "Конфликт - новое имя уже занято"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_recipe(
    recipe_id: int,
    obj_in: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
) -> RecipeRead:
    """
    Обновить рецептуру по ID.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    return await crud_recipe.update(db, db_obj=recipe, obj_in=obj_in)


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить рецептуру",
    description="Удаляет рецептуру и все связанные ингредиенты и операции (каскад).",
    responses={
        204: {"description": "Рецептура успешно удалена"},
        404: {"description": "Рецептура не найдена"},
    }
)
async def delete_recipe(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить рецептуру по ID (каскадное удаление).
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    await crud_recipe.remove(db, id=recipe_id)
    
    return None

@router.get(
    "/{recipe_id}/ingredients",
    response_model=list[RecipeIngredientRead],
    summary="Получить ингредиенты рецептуры",
    description="Возвращает список всех ингредиентов данной рецептуры.",
    responses={
        200: {"description": "Успешный ответ со списком ингредиентов"},
        404: {"description": "Рецептура не найдена"},
    }
)
async def get_recipe_ingredients(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[RecipeIngredientRead]:
    """
    Получить ингредиенты рецептуры.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    ingredients = await crud_recipe.get_ingredients_for_recipe(db, recipe_id=recipe_id)
    return [RecipeIngredientRead.model_validate(item) for item in ingredients]


@router.post(
    "/{recipe_id}/ingredients",
    response_model=RecipeIngredientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить ингредиент в рецептуру",
    description="Добавляет новый ингредиент в состав рецептуры.",
    responses={
        201: {"description": "Ингредиент успешно добавлен"},
        404: {"description": "Рецептура не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def add_ingredient_to_recipe(
    recipe_id: int,
    obj_in: RecipeIngredientCreate,
    db: AsyncSession = Depends(get_db),
) -> RecipeIngredientRead:
    """
    Добавить ингредиент в рецептуру.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    return await crud_recipe.add_ingredient_to_recipe(
        db, 
        recipe_id=recipe_id, 
        obj_in=obj_in
    )


@router.put(
    "/{recipe_id}/ingredients/{ingredient_link_id}",
    response_model=RecipeIngredientRead,
    summary="Обновить ингредиент в рецептуре",
    description="Обновляет количество ингредиента в составе рецептуры.",
    responses={
        200: {"description": "Ингредиент успешно обновлён"},
        404: {"description": "Рецептура или связь не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_ingredient_in_recipe(
    recipe_id: int,
    ingredient_link_id: int,
    obj_in: RecipeIngredientQuantityUpdate,
    db: AsyncSession = Depends(get_db),
) -> RecipeIngredientRead:
    """
    Обновить количество ингредиента в рецептуре.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    return await crud_recipe.update_ingredient_in_recipe(
        db,
        recipe_id=recipe_id,
        ingredient_link_id=ingredient_link_id,
        quantity=obj_in.quantity
    )


@router.delete(
    "/{recipe_id}/ingredients/{ingredient_link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить ингредиент из рецептуры",
    description="Удаляет ингредиент из состава рецептуры.",
    responses={
        204: {"description": "Ингредиент успешно удалён"},
        404: {"description": "Рецептура или связь не найдена"},
    }
)
async def remove_ingredient_from_recipe(
    recipe_id: int,
    ingredient_link_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить ингредиент из рецептуры.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    removed = await crud_recipe.remove_ingredient_from_recipe(
        db,
        recipe_id=recipe_id,
        ingredient_link_id=ingredient_link_id
    )
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Связь рецепт-ингредиент не найдена"
        )
    
    return None

@router.get(
    "/{recipe_id}/operations",
    response_model=list[OperationRead],
    summary="Получить операции рецептуры",
    description="Возвращает список технологических операций данной рецептуры в порядке выполнения.",
    responses={
        200: {"description": "Успешный ответ со списком операций"},
        404: {"description": "Рецептура не найдена"},
    }
)
async def get_recipe_operations(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[OperationRead]:
    """
    Получить операции рецептуры.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    operations = await crud_recipe.get_operations_for_recipe(db, recipe_id=recipe_id)
    return [OperationRead.model_validate(item) for item in operations]


@router.post(
    "/{recipe_id}/operations",
    response_model=OperationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить операцию в рецептуру",
    description="Добавляет новую технологическую операцию в рецептуру.",
    responses={
        201: {"description": "Операция успешно добавлена"},
        404: {"description": "Рецептура не найдена"},
        409: {"description": "Конфликт - sequence_order уже занят"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def add_operation_to_recipe(
    recipe_id: int,
    obj_in: OperationCreate,
    db: AsyncSession = Depends(get_db),
) -> OperationRead:
    """
    Добавить операцию в рецептуру.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    return await crud_recipe.add_operation_to_recipe(
        db, 
        recipe_id=recipe_id, 
        obj_in=obj_in
    )


@router.put(
    "/{recipe_id}/operations/{operation_id}",
    response_model=OperationRead,
    summary="Обновить операцию в рецептуре",
    description="Обновляет параметры технологической операции.",
    responses={
        200: {"description": "Операция успешно обновлена"},
        404: {"description": "Рецептура или операция не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_operation_in_recipe(
    recipe_id: int,
    operation_id: int,
    obj_in: OperationUpdate,
    db: AsyncSession = Depends(get_db),
) -> OperationRead:
    """
    Обновить операцию в рецептуре.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    return await crud_recipe.update_operation(
        db,
        recipe_id=recipe_id,
        operation_id=operation_id,
        obj_in=obj_in.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{recipe_id}/operations/{operation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить операцию из рецептуры",
    description="Удаляет технологическую операцию из рецептуры.",
    responses={
        204: {"description": "Операция успешно удалена"},
        404: {"description": "Рецептура или операция не найдена"},
    }
)
async def remove_operation_from_recipe(
    recipe_id: int,
    operation_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить операцию из рецептуры.
    """
    recipe = await crud_recipe.get(db, id=recipe_id)
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Рецептура с ID {recipe_id} не найдена"
        )
    
    removed = await crud_recipe.remove_operation_from_recipe(
        db,
        recipe_id=recipe_id,
        operation_id=operation_id
    )
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Операция не найдена"
        )
    
    return None