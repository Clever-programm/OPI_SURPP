from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.api.v1.deps import get_db
from app.crud.schedule import crud_schedule
from app.services.planning_system.schedule_generator import ScheduleGeneratorService, ConflictCheckerService
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleRead,
    ScheduleUpdate,
    ScheduleWithDetails,
    ScheduleGenerateRequest,
    ScheduleGenerateResponse,
    ScheduleConflict,
)
from app.models.equipment import Equipment
from app.models.employee import Employee
from app.models.order import Order
from sqlalchemy import select
from collections import defaultdict

router = APIRouter(prefix="/schedule", tags=["schedule"])

@router.post(
    "/generate",
    response_model=ScheduleGenerateResponse,
    summary="Сформировать производственное расписание",
    description="Формирует производственное расписание на основе заказов и доступных ресурсов.",
    responses={
        200: {"description": "Расписание успешно сформировано"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def generate_schedule(
    obj_in: ScheduleGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ScheduleGenerateResponse:
    """
    Сформировать производственное расписание.
    
    ⚠️ **На данном этапе реализована заглушка алгоритма.**
    
    Бизнес-логика:
    - Анализирует активные заказы в указанном периоде
    - Учитывает доступные ресурсы (оборудование, сотрудники)
    - Формирует последовательность операций для каждого заказа
    - Проверяет конфликты ресурсов (заглушка)
    
    Пример использования:
    Инженер по планированию нажимает "Сформировать план" в разделе "Планирование".
    Система создаёт расписание на неделю вперёд.
    """
    generator = ScheduleGeneratorService(db)
    return await generator.generate(obj_in)


@router.get(
    "/conflicts",
    response_model=List[ScheduleConflict],
    summary="Проверить конфликты ресурсов",
    description="Возвращает список конфликтов оборудования, сотрудников или сырья в расписании.",
    responses={
        200: {"description": "Проверка выполнена успешно"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def check_conflicts(
    start_date: Optional[date] = Query(default=None, description="Дата начала периода проверки"),
    end_date: Optional[date] = Query(default=None, description="Дата окончания периода проверки"),
    db: AsyncSession = Depends(get_db),
) -> List[ScheduleConflict]:
    """
    Проверить конфликты в расписании.
    
    ⚠️ **На данном этапе реализована заглушка.**
    
    Типы конфликтов:
    - `equipment`: Два назначения на одно оборудование в одно время
    - `employee`: Один кондитер назначен на две операции одновременно
    - `ingredient`: Недостаточно сырья для запланированных операций
    - `sequence`: Нарушение последовательности технологических операций
    
    Пример использования:
    Перед утверждением плана планировщик проверяет, нет ли конфликтов.
    """
    checker = ConflictCheckerService(db)
    return await checker.check(start_date=start_date, end_date=end_date)


@router.get(
    "/calendar",
    response_model=dict,
    summary="Календарный вид расписания",
    description="Возвращает расписание в формате календаря (по дням или неделям).",
    responses={
        200: {"description": "Успешный ответ с календарём"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_schedule_calendar(
    start_date: date = Query(..., description="Дата начала периода"),
    end_date: date = Query(..., description="Дата окончания периода"),
    resource_type: str = Query(default="equipment", regex="^(equipment|employee)$", description="Тип ресурса для группировки"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Получить расписание в календарном виде.
    
    Бизнес-логика:
    - Группировка записей по дням
    - Фильтрация по типу ресурса (оборудование или сотрудники)
    - Сортировка по времени начала
    
    Пример использования:
    Отображение недельного плана в календаре на фронтенде.
    """
    result = await crud_schedule.get_all_with_details(
        db,
        page=1,
        limit=1000,  # Большой лимит для календаря
        start_date=start_date,
        end_date=end_date
    )
    
    # Группировка по дням
    calendar = defaultdict(list)
    for item in result["items"]:
        day_key = item.start_time.date().isoformat()
        calendar[day_key].append({
            "id": item.id,
            "title": item.name or f"{item.operation.name} (Заказ #{item.order_id})",
            "start": item.start_time.isoformat(),
            "end": item.end_time.isoformat(),
            "resource_type": resource_type,
            "resource_id": item.equipment_id if resource_type == "equipment" else item.employee_id,
            "order_id": item.order_id,
        })
    
    return {
        "calendar": dict(calendar),
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "total_items": result["total"],
    }


@router.get(
    "/equipment/{equipment_id}",
    response_model=List[ScheduleRead],
    summary="Расписание загрузки оборудования",
    description="Возвращает все операции для указанного оборудования за период.",
    responses={
        200: {"description": "Успешный ответ со списком операций"},
        404: {"description": "Оборудование не найдено"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_equipment_schedule(
    equipment_id: int,
    start_date: date = Query(..., description="Дата начала периода"),
    end_date: date = Query(..., description="Дата окончания периода"),
    db: AsyncSession = Depends(get_db),
) -> List[ScheduleRead]:
    """
    Получить расписание загрузки оборудования.
    
    Бизнес-логика:
    - Фильтрация по оборудованию
    - Проверка существования оборудования
    - Сортировка по времени начала
    """
    
    equipment_query = select(Equipment).where(Equipment.id == equipment_id)
    equipment_result = await db.execute(equipment_query)
    if not equipment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Оборудование ID {equipment_id} не найдено"
        )
    
    schedules = await crud_schedule.get_by_equipment(
        db,
        equipment_id=equipment_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return [ScheduleRead.model_validate(s) for s in schedules]


@router.get(
    "/employee/{employee_id}",
    response_model=List[ScheduleRead],
    summary="Расписание загрузки сотрудника",
    description="Возвращает все операции для указанного сотрудника за период.",
    responses={
        200: {"description": "Успешный ответ со списком операций"},
        404: {"description": "Сотрудник не найден"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_employee_schedule(
    employee_id: int,
    start_date: date = Query(..., description="Дата начала периода"),
    end_date: date = Query(..., description="Дата окончания периода"),
    db: AsyncSession = Depends(get_db),
) -> List[ScheduleRead]:
    """
    Получить расписание загрузки сотрудника.
    
    Бизнес-логика:
    - Фильтрация по сотруднику
    - Проверка существования сотрудника
    - Сортировка по времени начала
    """
    
    employee_query = select(Employee).where(Employee.id == employee_id)
    employee_result = await db.execute(employee_query)
    if not employee_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Сотрудник ID {employee_id} не найден"
        )
    
    schedules = await crud_schedule.get_by_employee(
        db,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return [ScheduleRead.model_validate(s) for s in schedules]


@router.get(
    "/order/{order_id}",
    response_model=List[ScheduleRead],
    summary="Расписание по заказу",
    description="Возвращает все операции для указанного заказа.",
    responses={
        200: {"description": "Успешный ответ со списком операций"},
        404: {"description": "Заказ не найден"},
    }
)
async def get_order_schedule(
    order_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[ScheduleRead]:
    """
    Получить расписание для конкретного заказа.
    
    Бизнес-логика:
    - Фильтрация по заказу
    - Проверка существования заказа
    - Сортировка по времени начала (последовательность операций)
    """
    
    order_query = select(Order).where(Order.id == order_id)
    order_result = await db.execute(order_query)
    if not order_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Заказ ID {order_id} не найден"
        )
    
    schedules = await crud_schedule.get_by_order(db, order_id=order_id)
    
    return [ScheduleRead.model_validate(s) for s in schedules]


@router.get(
    "/",
    response_model=dict,
    summary="Получить список расписания",
    description="Возвращает список всех записей расписания с пагинацией и фильтрацией.",
    responses={
        200: {"description": "Успешный ответ со списком расписания"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_schedule(
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    limit: int = Query(default=50, ge=1, le=100, description="Количество записей на странице"),
    start_date: Optional[date] = Query(default=None, description="Дата начала периода (от)"),
    end_date: Optional[date] = Query(default=None, description="Дата окончания периода (до)"),
    equipment_id: Optional[int] = Query(default=None, description="Фильтр по оборудованию"),
    employee_id: Optional[int] = Query(default=None, description="Фильтр по сотруднику"),
    order_id: Optional[int] = Query(default=None, description="Фильтр по заказу"),
) -> dict:
    """
    Получить список записей производственного расписания.
    
    Параметры фильтрации:
    - `start_date` / `end_date`: Период планирования
    - `equipment_id`: Только операции для указанного оборудования
    - `employee_id`: Только операции для указанного сотрудника
    - `order_id`: Только операции для указанного заказа
    
    Пример использования:
    Основная страница раздела "Планирование" с таблицей расписания.
    """
    result = await crud_schedule.get_all_with_details(
        db,
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        equipment_id=equipment_id,
        employee_id=employee_id,
        order_id=order_id
    )
    
    items = [
        ScheduleWithDetails.model_validate(item) 
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
    "/load/equipment/{equipment_id}",
    response_model=dict,
    summary="Загрузка оборудования за период",
    description="Рассчитывает процент загрузки оборудования за указанный период.",
    responses={
        200: {"description": "Успешный ответ со статистикой"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_equipment_load(
    equipment_id: int,
    start_date: date = Query(..., description="Дата начала периода"),
    end_date: date = Query(..., description="Дата окончания периода"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Получить статистику загрузки оборудования.
    
    Бизнес-логика:
    - Суммарное время операций за период
    - Расчёт процента от доступного времени (8 часов/день)
    - Используется для выявления узких мест производства
    """
    return await crud_schedule.get_equipment_load(
        db,
        equipment_id=equipment_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get(
    "/load/employee/{employee_id}",
    response_model=dict,
    summary="Загрузка сотрудника за период",
    description="Рассчитывает процент загрузки сотрудника за указанный период.",
    responses={
        200: {"description": "Успешный ответ со статистикой"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def get_employee_load(
    employee_id: int,
    start_date: date = Query(..., description="Дата начала периода"),
    end_date: date = Query(..., description="Дата окончания периода"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Получить статистику загрузки сотрудника.
    
    Бизнес-логика:
    - Суммарное время операций за период
    - Расчёт процента от доступного времени (8 часов/день)
    - Используется для равномерного распределения нагрузки
    """
    return await crud_schedule.get_employee_load(
        db,
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date
    )


@router.post(
    "/",
    response_model=ScheduleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить запись в расписание",
    description="Создаёт новую запись в производственном расписании (ручное добавление операции).",
    responses={
        201: {"description": "Запись успешно добавлена"},
        400: {"description": "Ошибка валидации времени"},
        404: {"description": "Связанный объект не найден"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def create_schedule(
    obj_in: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
) -> ScheduleRead:
    """
    Создать новую запись в расписании.
    
    Бизнес-логика:
    - Проверка: end_time > start_time
    - Валидация существования operation_id, order_id, equipment_id, employee_id
    - Используется для ручной корректировки плана после автогенерации
    """
    return await crud_schedule.create(db, obj_in=obj_in)


@router.get(
    "/{schedule_id}",
    response_model=ScheduleWithDetails,
    summary="Получить запись расписания с деталями",
    description="Возвращает детальную информацию о записи расписания включая названия операций, заказов, оборудования и сотрудников.",
    responses={
        200: {"description": "Успешный ответ с данными расписания"},
        404: {"description": "Запись расписания не найдена"},
    }
)
async def get_schedule_detail(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
) -> ScheduleWithDetails:
    """
    Получить запись расписания по ID с полным набором деталей.
    
    Бизнес-логика:
    - Жадная загрузка всех связанных объектов (operation, order, equipment, employee)
    - Возврат человекочитаемых названий для UI
    """
    schedule = await crud_schedule.get_with_details(db, id=schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запись расписания ID {schedule_id} не найдена"
        )
    
    return schedule


@router.put(
    "/{schedule_id}",
    response_model=ScheduleRead,
    summary="Редактировать запись расписания",
    description="Обновляет параметры записи расписания (время, ресурсы, примечания).",
    responses={
        200: {"description": "Запись успешно обновлена"},
        400: {"description": "Ошибка валидации времени"},
        404: {"description": "Запись расписания не найдена"},
        422: {"description": "Ошибка валидации данных"},
    }
)
async def update_schedule(
    schedule_id: int,
    obj_in: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
) -> ScheduleRead:
    """
    Обновить запись в расписании.
    
    Бизнес-логика:
    - Частичное обновление (только указанные поля)
    - Проверка: end_time > start_time (если оба поля указаны)
    - Валидация связанных объектов при изменении
    """
    schedule = await crud_schedule.get(db, id=schedule_id)
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запись расписания ID {schedule_id} не найдена"
        )
    
    return await crud_schedule.update(db, db_obj=schedule, obj_in=obj_in)


@router.delete(
    "/{schedule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить запись из расписания",
    description="Удаляет запись из производственного расписания.",
    responses={
        204: {"description": "Запись успешно удалена"},
        404: {"description": "Запись расписания не найдена"},
    }
)
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Удалить запись из расписания.
    
    Бизнес-логика:
    - Проверка существования записи
    - Каскадное удаление (если настроено в БД)
    - Используется для удаления ошибочных или отменённых операций
    """
    removed = await crud_schedule.delete(db, id=schedule_id)
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Запись расписания ID {schedule_id} не найдена"
        )
    
    return None
