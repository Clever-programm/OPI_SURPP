from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.api.v1.deps import get_db
from app.crud.order import crud_order
from app.schemas.order import (
    OrderCreate,
    OrderRead,
    OrderUpdate,
    OrderStatusUpdate,
    OrderWithItems,
)
from app.schemas.order_item import (
    OrderItemCreate,
    OrderItemRead,
    OrderItemUpdate,
)

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get(
    "/",
    response_model=dict,
    summary="Получить список заказов",
    description="Возвращает список всех заказов с пагинацией, сортировкой и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком заказов"},
    }
)
async def get_orders(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    sort_by: Optional[str] = Query(default="due_date", description="Поле для сортировки"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$", description="Порядок сортировки"),
    order_status: Optional[str] = Query(default=None, description="Фильтр по статусу"),
    due_date_from: Optional[date] = Query(default=None, description="Дата выполнения от"),
    due_date_to: Optional[date] = Query(default=None, description="Дата выполнения до"),
) -> dict:
    """
    Получить список заказов с пагинацией и фильтрацией.
    """
    #TODO: Фильтр по дате от и до
    filters = {}
    if order_status:
        filters["status"] = order_status
    
    result = await crud_order.get_multi(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters
    )
    
    items = [
        OrderRead.model_validate(item) 
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
    "/{order_id}",
    response_model=OrderWithItems,
    summary="Получить заказ с деталями",
    description="Возвращает детальную информацию о заказе включая позиции.",
    responses={
        200: {"description": "Успешный ответ с данными заказа"},
        404: {"description": "Заказ не найден"},
    }
)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> OrderWithItems:
    """
    Получить заказ по ID с полным составом позиций.
    """
    order = await crud_order.get_with_items(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    return order


@router.post(
    "/",
    response_model=OrderWithItems,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый заказ",
    description="Создаёт новый производственный заказ с позициями.",
    responses={
        201: {"description": "Заказ успешно создан"},
        400: {"description": "Ошибка валидации (дата в прошлом)"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_order(
    obj_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderWithItems:
    """
    Создать новый производственный заказ.
    """
    return await crud_order.create(db, obj_in=obj_in)


@router.put(
    "/{order_id}",
    response_model=OrderRead,
    summary="Полностью обновить заказ",
    description="Обновляет основные поля заказа. Для изменения позиций используйте вложенные эндпоинты.",
    responses={
        200: {"description": "Заказ успешно обновлён"},
        400: {"description": "Ошибка валидации (дата в прошлом)"},
        404: {"description": "Заказ не найден"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_order(
    order_id: int,
    obj_in: OrderUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """
    Обновить заказ по ID.
    """
    order = await crud_order.get(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    return await crud_order.update(db, db_obj=order, obj_in=obj_in)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Изменить статус заказа",
    description="Обновляет статус заказа (new → planned → in_progress → done).",
    responses={
        200: {"description": "Статус успешно обновлён"},
        404: {"description": "Заказ не найден"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_order_status(
    order_id: int,
    obj_in: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderRead:
    """
    Изменить статус заказа.
    """
    return await crud_order.update_status(
        db, 
        id=order_id, 
        status_new=obj_in.status
    )


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заказ",
    description="Удаляет заказ и все связанные позиции (каскад).",
    responses={
        204: {"description": "Заказ успешно удалён"},
        404: {"description": "Заказ не найден"},
    }
)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить заказ по ID (каскадное удаление).
    """
    order = await crud_order.get(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    await crud_order.remove(db, id=order_id)
    
    return None

@router.get(
    "/{order_id}/items",
    response_model=list[OrderItemRead],
    summary="Получить позиции заказа",
    description="Возвращает список всех позиций данного заказа.",
    responses={
        200: {"description": "Успешный ответ со списком позиций"},
        404: {"description": "Заказ не найден"},
    }
)
async def get_order_items(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[OrderItemRead]:
    """
    Получить позиции заказа.
    """
    order = await crud_order.get(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    items = await crud_order.get_items_for_order(db, order_id=order_id)
    return [OrderItemRead.model_validate(item) for item in items]


@router.post(
    "/{order_id}/items",
    response_model=OrderItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить позицию в заказ",
    description="Добавляет новую позицию (изделие) в заказ.",
    responses={
        201: {"description": "Позиция успешно добавлена"},
        404: {"description": "Заказ не найден"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def add_item_to_order(
    order_id: int,
    obj_in: OrderItemCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderItemRead:
    """
    Добавить позицию в заказ.
    """
    order = await crud_order.get(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    return await crud_order.add_item_to_order(
        db, 
        order_id=order_id, 
        obj_in=obj_in
    )


@router.put(
    "/{order_id}/items/{item_id}",
    response_model=OrderItemRead,
    summary="Обновить позицию в заказе",
    description="Обновляет параметры позиции заказа (рецептура, количество).",
    responses={
        200: {"description": "Позиция успешно обновлена"},
        404: {"description": "Заказ или позиция не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_item_in_order(
    order_id: int,
    item_id: int,
    obj_in: OrderItemUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderItemRead:
    """
    Обновить позицию в заказе.
    """
    order = await crud_order.get(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    return await crud_order.update_item_in_order(
        db,
        order_id=order_id,
        item_id=item_id,
        obj_in=obj_in.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{order_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить позицию из заказа",
    description="Удаляет позицию из заказа.",
    responses={
        204: {"description": "Позиция успешно удалена"},
        404: {"description": "Заказ или позиция не найдена"},
    }
)
async def remove_item_from_order(
    order_id: int,
    item_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить позицию из заказа.
    """
    order = await crud_order.get(db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ с ID {order_id} не найден"
        )
    
    removed = await crud_order.remove_item_from_order(
        db,
        order_id=order_id,
        item_id=item_id
    )
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция заказа не найдена"
        )
    
    return None