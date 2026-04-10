from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.v1.deps import get_db
from app.crud.employee import crud_employee
from app.models.competence import Competence
from app.models.employee import Employee

from app.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeUpdate,
    EmployeeWithCompetences,
)
from app.schemas.employee_competence import (
    EmployeeCompetenceCreate,
    EmployeeCompetenceRead,
)

router = APIRouter(prefix="/employees", tags=["employees"])

@router.get(
    "/",
    response_model=dict,
    summary="Получить список сотрудников",
    description="Возвращает список всех сотрудников с пагинацией и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком сотрудников"},
    }
)
async def get_employees(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    active: Optional[bool] = Query(default=None, description="Фильтр по статусу активности"),
    name: Optional[str] = Query(default=None, description="Поиск по ФИО"),
) -> dict:
    """
    Получить список сотрудников.
    
    Параметры фильтрации:
    - `active`: Только активные (`true`) или неактивные (`false`) сотрудники
    - `name`: Поиск по частичному совпадению ФИО
    """
    
    query = select(Employee)
    count_query = select(func.count()).select_from(Employee)
    
    # Фильтр по статусу
    if active is not None:
        query = query.where(Employee.active == active)
        count_query = count_query.where(Employee.active == active)
    
    # Поиск по имени
    if name:
        query = query.where(Employee.name.ilike(f"%{name}%"))
        count_query = count_query.where(Employee.name.ilike(f"%{name}%"))
    
    # Пагинация
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    total_result = await db.execute(count_query)
    
    items = result.scalars().all()
    total = total_result.scalar()
    
    return {
        "items": [EmployeeRead.model_validate(item) for item in items],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


@router.get(
    "/available",
    response_model=list[EmployeeRead],
    summary="Получить доступных сотрудников",
    description="Возвращает только активных сотрудников (active=True).",
    responses={
        200: {"description": "Успешный ответ со списком активных сотрудников"},
    }
)
async def get_available_employees(
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeRead]:
    """
    Получить только активных сотрудников.
    
    Бизнес-логика:
    Используется при формировании производственного расписания (Сценарий 3)
    для выбора доступных кондитеров.
    """
    employees = await crud_employee.get_available(db)
    return [EmployeeRead.model_validate(emp) for emp in employees]


@router.get(
    "/{employee_id}",
    response_model=EmployeeWithCompetences,
    summary="Получить сотрудника с компетенциями",
    description="Возвращает детальную информацию о сотруднике включая квалификации.",
    responses={
        200: {"description": "Успешный ответ с данными сотрудника"},
        404: {"description": "Сотрудник не найден"},
    }
)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
) -> EmployeeWithCompetences:
    """
    Получить сотрудника по ID с полным списком компетенций.
    
    Бизнес-логика:
    Отображение квалификации кондитера для назначения на технологические операции.
    """
    employee = await crud_employee.get_with_competences(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    return employee


@router.post(
    "/",
    response_model=EmployeeWithCompetences,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить нового сотрудника",
    description="Создаёт новую запись о сотруднике с указанием компетенций (разрядов).",
    responses={
        201: {"description": "Сотрудник успешно добавлен"},
        409: {"description": "Конфликт - сотрудник с таким именем уже существует"},
        404: {"description": "Компетенция не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_employee(
    obj_in: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeWithCompetences:
    """
    Создать нового сотрудника.
    
    Бизнес-логика:
    - Проверка уникальности имени сотрудника
    - Валидация существования компетенций
    - Поддержка вложенного создания компетенций "всё в одном запросе"
    """
    return await crud_employee.create(db, obj_in=obj_in)


@router.put(
    "/{employee_id}",
    response_model=EmployeeRead,
    summary="Редактировать сотрудника",
    description="Обновляет информацию о сотруднике (ФИО, статус активности).",
    responses={
        200: {"description": "Сотрудник успешно обновлён"},
        404: {"description": "Сотрудник не найден"},
        409: {"description": "Конфликт - новое имя уже занято"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_employee(
    employee_id: int,
    obj_in: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeRead:
    """
    Обновить информацию о сотруднике.
    
    Бизнес-логика:
    - Проверка уникальности нового имени
    - Частичное обновление (только указанные поля)
    """
    employee = await crud_employee.get(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    return await crud_employee.update(db, db_obj=employee, obj_in=obj_in)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сотрудника",
    description="Удаляет запись о сотруднике из системы.",
    responses={
        204: {"description": "Сотрудник успешно удалён"},
        404: {"description": "Сотрудник не найден"},
    }
)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить сотрудника по ID.
    
    Бизнес-логика:
    - Каскадное удаление связанных компетенций
    - Рекомендуется деактивировать (active=False) вместо удаления
    """
    employee = await crud_employee.get(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    await crud_employee.remove(db, id=employee_id)
    
    return None

@router.patch(
    "/{employee_id}/active",
    response_model=EmployeeRead,
    summary="Изменить статус активности сотрудника",
    description="Изменяет статус занятости сотрудника (active/inactive).",
    responses={
        200: {"description": "Статус успешно обновлён"},
        404: {"description": "Сотрудник не найден"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_employee_active(
    employee_id: int,
    active: bool = Query(..., description="Новый статус активности"),
    db: AsyncSession = Depends(get_db),
) -> EmployeeRead:
    """
    Изменить статус активности сотрудника.
    
    Бизнес-логика:
    - Деактивация вместо удаления (сохранение истории)
    - Неактивные сотрудники не отображаются в планировании (Сценарий 3)
    """
    employee = await crud_employee.get(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    employee.active = active
    await db.commit()
    await db.refresh(employee)
    
    return employee

@router.get(
    "/{employee_id}/competences",
    response_model=list[EmployeeCompetenceRead],
    summary="Получить компетенции сотрудника",
    description="Возвращает список всех квалификаций (разрядов) сотрудника.",
    responses={
        200: {"description": "Успешный ответ со списком компетенций"},
        404: {"description": "Сотрудник не найден"},
    }
)
async def get_employee_competences(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeCompetenceRead]:
    """
    Получить компетенции сотрудника.
    
    Бизнес-логика:
    Используется для проверки соответствия кондитера технологическим операциям
    при формировании расписания (Сценарий 3).
    """
    employee = await crud_employee.get(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    competences = await crud_employee.get_competences_for_employee(db, employee_id=employee_id)
    
    # enrich с названием компетенции
    
    result_list = []
    for comp_link in competences:
        comp_query = select(Competence).where(Competence.id == comp_link.competence_id)
        comp_result = await db.execute(comp_query)
        comp = comp_result.scalar_one_or_none()
        
        result_list.append(EmployeeCompetenceRead(
            id=comp_link.id,
            employee_id=comp_link.employee_id,
            competence_id=comp_link.competence_id,
            competence_name=comp.name if comp else "Unknown"
        ))
    
    return result_list


@router.post(
    "/{employee_id}/competences",
    response_model=EmployeeCompetenceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить компетенцию сотруднику",
    description="Назначает сотруднику новую квалификацию (разряд).",
    responses={
        201: {"description": "Компетенция успешно добавлена"},
        404: {"description": "Сотрудник или компетенция не найдена"},
        409: {"description": "Конфликт - компетенция уже назначена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def add_competence_to_employee(
    employee_id: int,
    obj_in: EmployeeCompetenceCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeCompetenceRead:
    """
    Добавить компетенцию сотруднику.
    
    Бизнес-логика:
    - Проверка существования компетенции в справочнике
    - Проверка отсутствия дубликата (одна компетенция не может быть назначена дважды)
    """
    employee = await crud_employee.get(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    return await crud_employee.add_competence_to_employee(
        db, 
        employee_id=employee_id, 
        obj_in=obj_in
    )


@router.delete(
    "/{employee_id}/competences/{competence_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить компетенцию у сотрудника",
    description="Удаляет квалификацию (разряд) у сотрудника.",
    responses={
        204: {"description": "Компетенция успешно удалена"},
        404: {"description": "Сотрудник или компетенция не найдена"},
    }
)
async def remove_competence_from_employee(
    employee_id: int,
    competence_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить компетенцию у сотрудника.
    
    Бизнес-логика:
    - Проверка существования связи
    - Каскадное обновление при планировании
    """
    employee = await crud_employee.get(db, id=employee_id)
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник с ID {employee_id} не найден"
        )
    
    removed = await crud_employee.remove_competence_from_employee(
        db,
        employee_id=employee_id,
        competence_id=competence_id
    )
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Компетенция ID {competence_id} не найдена у сотрудника ID {employee_id}"
        )
    
    return None

@router.get(
    "/by-competence/{competence_id}",
    response_model=list[EmployeeRead],
    summary="Найти сотрудников по компетенции",
    description="Возвращает всех сотрудников с указанной квалификацией (разрядом).",
    responses={
        200: {"description": "Успешный ответ со списком сотрудников"},
        404: {"description": "Компетенция не найдена"},
    }
)
async def get_employees_by_competence(
    competence_id: int,
    active_only: bool = Query(default=True, description="Только активные сотрудники"),
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeRead]:
    """
    Найти сотрудников с определённой компетенцией.
    
    Бизнес-логика:
    Используется при формировании производственного расписания для поиска
    кондитеров, способных выполнить конкретную технологическую операцию.
    """
    employees = await crud_employee.get_employees_by_competence(
        db,
        competence_id=competence_id,
        active_only=active_only
    )
    
    return [EmployeeRead.model_validate(emp) for emp in employees]