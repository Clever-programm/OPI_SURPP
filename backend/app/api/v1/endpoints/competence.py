from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.crud.competence import crud_competence
from app.schemas.competence import (
    CompetenceCreate,
    CompetenceRead,
    CompetenceUpdate,
)
from app.models.competence import Competence

router = APIRouter(prefix="/competences", tags=["competences"])


@router.get(
    "/",
    response_model=dict,
    summary="Получить список компетенций",
    description="Возвращает список всех компетенций с пагинацией, сортировкой и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком компетенций"},
    }
)
async def get_competences(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    sort_by: Optional[str] = Query(default="name", description="Поле для сортировки"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$", description="Порядок сортировки"),
    name: Optional[str] = Query(default=None, description="Фильтр по названию"),
) -> dict:
    """
    Получить список компетенций с пагинацией и фильтрацией.
    """
    filters = {}
    if name:
        filters["name"] = name
    
    result = await crud_competence.get_multi(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters
    )
    
    items = [
        CompetenceRead.model_validate(item) 
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
    "/{competence_id}",
    response_model=CompetenceRead,
    summary="Получить компетенцию по ID",
    description="Возвращает детальную информацию о компетенции по её ID.",
    responses={
        200: {"description": "Успешный ответ с данными компетенции"},
        404: {"description": "Компетенция не найдена"},
    }
)
async def get_competence(
    competence_id: int,
    db: AsyncSession = Depends(get_db),
) -> Competence:
    """
    Получить компетенцию по ID.
    """
    competence = await crud_competence.get(db, id=competence_id)
    
    if not competence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Компетенция с ID {competence_id} не найдена"
        )
    
    return competence


@router.post(
    "/",
    response_model=CompetenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую компетенцию",
    description="Создаёт новую запись о компетенции в системе.",
    responses={
        201: {"description": "Компетенция успешно создана"},
        409: {"description": "Конфликт - компетенция с таким именем уже существует"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_competence(
    obj_in: CompetenceCreate,
    db: AsyncSession = Depends(get_db),
) -> Competence:
    """
    Создать новую компетенцию.
    """
    return await crud_competence.create(db, obj_in=obj_in)


@router.put(
    "/{competence_id}",
    response_model=CompetenceRead,
    summary="Полностью обновить компетенцию",
    description="Обновляет все поля компетенции. Поля, не указанные в запросе, будут сброшены.",
    responses={
        200: {"description": "Компетенция успешно обновлена"},
        404: {"description": "Компетенция не найдена"},
        409: {"description": "Конфликт - новое имя уже занято"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_competence(
    competence_id: int,
    obj_in: CompetenceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Competence:
    """
    Обновить компетенцию по ID.
    """
    competence = await crud_competence.get(db, id=competence_id)
    
    if not competence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Компетенция с ID {competence_id} не найдена"
        )
    
    return await crud_competence.update(db, db_obj=competence, obj_in=obj_in)


@router.delete(
    "/{competence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить компетенцию",
    description="Удаляет запись о компетенции из системы.",
    responses={
        204: {"description": "Компетенция успешно удалена"},
        404: {"description": "Компетенция не найдена"},
    }
)
async def delete_competence(
    competence_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить компетенцию по ID.
    """
    competence = await crud_competence.get(db, id=competence_id)
    
    if not competence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Компетенция с ID {competence_id} не найдена"
        )
    
    await crud_competence.remove(db, id=competence_id)
    
    return None