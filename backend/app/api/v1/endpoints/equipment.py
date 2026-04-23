from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.crud.equipment import crud_equipment
from app.schemas.equipment import (
    EquipmentCreate,
    EquipmentRead,
    EquipmentUpdate,
    EquipmentQuantityUpdate,
)
from app.models.equipment import Equipment

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get(
    "/",
    response_model=dict,
    summary="Получить список оборудования",
    description="Возвращает список всего оборудования с пагинацией, сортировкой и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком оборудования"},
    }
)
async def get_equipment_list(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    sort_by: Optional[str] = Query(default="name", description="Поле для сортировки"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$", description="Порядок сортировки"),
    name: Optional[str] = Query(default=None, description="Фильтр по названию"),
) -> dict:
    """
    Получить список оборудования с пагинацией и фильтрацией.
    """
    filters = {}
    if name:
        filters["name"] = name
    
    result = await crud_equipment.get_multi(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters
    )
    
    items = [
        EquipmentRead.model_validate(item) 
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
    "/available",
    response_model=list[EquipmentRead],
    summary="Получить доступное оборудование",
    description="Возвращает только оборудование с quantity > 0.",
    responses={
        200: {"description": "Успешный ответ со списком доступного оборудования"},
    }
)
async def get_available_equipment(
    db: AsyncSession = Depends(get_db),
) -> list[Equipment]:
    """
    Получить только доступное оборудование.
    """
    equipment_list = await crud_equipment.get_available(db)
    return [EquipmentRead.model_validate(item) for item in equipment_list]


@router.get(
    "/{equipment_id}",
    response_model=EquipmentRead,
    summary="Получить оборудование по ID",
    description="Возвращает детальную информацию об оборудовании по его ID.",
    responses={
        200: {"description": "Успешный ответ с данными оборудования"},
        404: {"description": "Оборудование не найдено"},
    }
)
async def get_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
) -> Equipment:
    """
    Получить оборудование по ID.
    """
    equipment = await crud_equipment.get(db, id=equipment_id)
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Оборудование с ID {equipment_id} не найдено"
        )
    
    return equipment


@router.post(
    "/",
    response_model=EquipmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое оборудование",
    description="Создаёт новую запись об оборудовании в системе.",
    responses={
        201: {"description": "Оборудование успешно создано"},
        409: {"description": "Конфликт - оборудование с таким именем уже существует"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_equipment(
    obj_in: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
) -> Equipment:
    """
    Создать новое оборудование.
    """
    return await crud_equipment.create(db, obj_in=obj_in)


@router.put(
    "/{equipment_id}",
    response_model=EquipmentRead,
    summary="Полностью обновить оборудование",
    description="Обновляет все поля оборудования. Поля, не указанные в запросе, будут сброшены.",
    responses={
        200: {"description": "Оборудование успешно обновлено"},
        404: {"description": "Оборудование не найдено"},
        409: {"description": "Конфликт - новое имя уже занято"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_equipment(
    equipment_id: int,
    obj_in: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> Equipment:
    """
    Обновить оборудование по ID.
    """
    equipment = await crud_equipment.get(db, id=equipment_id)
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Оборудование с ID {equipment_id} не найдено"
        )
    
    return await crud_equipment.update(db, db_obj=equipment, obj_in=obj_in)


@router.patch(
    "/{equipment_id}/quantity",
    response_model=EquipmentRead,
    summary="Изменить количество оборудования",
    description="Обновляет только количество единиц оборудования.",
    responses={
        200: {"description": "Количество успешно обновлено"},
        404: {"description": "Оборудование не найдено"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_equipment_quantity(
    equipment_id: int,
    obj_in: EquipmentQuantityUpdate,
    db: AsyncSession = Depends(get_db),
) -> Equipment:
    """
    Обновить количество оборудования.
    """
    return await crud_equipment.update_quantity(
        db, 
        id=equipment_id, 
        quantity=obj_in.quantity
    )


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить оборудование",
    description="Удаляет запись об оборудовании из системы.",
    responses={
        204: {"description": "Оборудование успешно удалено"},
        404: {"description": "Оборудование не найдено"},
    }
)
async def delete_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить оборудование по ID.
    """
    equipment = await crud_equipment.get(db, id=equipment_id)
    
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Оборудование с ID {equipment_id} не найдено"
        )
    
    await crud_equipment.remove(db, id=equipment_id)
    
    return None


@router.post(
    "/import",
    response_model=dict,
    summary="Массовый импорт оборудования",
    description="Парсит оборудование из CSV/JSON и сохраняет в БД.",
    responses={
        200: {"description": "Импорт выполнен успешно"},
    }
)
async def import_equipment(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Массовый импорт оборудования.
    """
    # TODO: Реализовать парсинг CSV/JSON и массовое создание записей
    return {"status": "ok", "imported": 0, "message": "Функционал в разработке"}