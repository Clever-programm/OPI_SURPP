from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.schedule import Schedule
from app.models.operation import Operation
from app.models.order import Order
from app.models.equipment import Equipment
from app.models.employee import Employee
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate


class CRUDSchedule(CRUDBase[Schedule, ScheduleCreate, ScheduleUpdate]):
    """
    CRUD-операции для производственного расписания.
    """
    
    async def get_with_details(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[Schedule]:
        """Получить запись расписания с деталями (жадная загрузка)."""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.operation),
                selectinload(self.model.order),
                selectinload(self.model.equipment),
                selectinload(self.model.employee)
            )
            .where(self.model.id == id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_with_details(
        self, 
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 50,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        equipment_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        order_id: Optional[int] = None,
    ) -> dict:
        """Получить все записи расписания с пагинацией и фильтрацией."""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.operation),
                selectinload(self.model.order),
                selectinload(self.model.equipment),
                selectinload(self.model.employee)
            )
        )
        count_query = select(func.count()).select_from(Schedule)
        
        # Фильтры
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.where(self.model.start_time >= start_datetime)
            count_query = count_query.where(self.model.start_time >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.where(self.model.start_time <= end_datetime)
            count_query = count_query.where(self.model.start_time <= end_datetime)
        
        if equipment_id:
            query = query.where(self.model.equipment_id == equipment_id)
            count_query = count_query.where(self.model.equipment_id == equipment_id)
        
        if employee_id:
            query = query.where(self.model.employee_id == employee_id)
            count_query = count_query.where(self.model.employee_id == employee_id)
        
        if order_id:
            query = query.where(self.model.order_id == order_id)
            count_query = count_query.where(self.model.order_id == order_id)
        
        # Сортировка и пагинация
        query = query.order_by(self.model.start_time.asc())
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        
        result = await db.execute(query)
        total_result = await db.execute(count_query)
        
        items = result.scalars().all()
        total = total_result.scalar()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: ScheduleCreate
    ) -> Schedule:
        """Создать новую запись в расписании с валидацией связей."""
        # Валидация времени
        if obj_in.end_time <= obj_in.start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Время окончания должно быть позже времени начала"
            )
        
        # Проверка существования связанных объектов
        await self._validate_relations(db, obj_in)
        
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Schedule, 
        obj_in: ScheduleUpdate
    ) -> Schedule:
        """Обновить запись в расписании."""
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Валидация времени
        if "start_time" in obj_data and "end_time" in obj_data:
            if obj_data["end_time"] <= obj_data["start_time"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Время окончания должно быть позже времени начала"
                )
        
        # Проверка связей если они меняются
        await self._validate_relations(db, obj_in, exclude_current=True)
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def delete(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> bool:
        """Удалить запись из расписания."""
        obj = await self.get(db, id=id)
        
        if not obj:
            return False
        
        await db.delete(obj)
        await db.commit()
        
        return True

    async def get_by_order(
        self, 
        db: AsyncSession, 
        *, 
        order_id: int
    ) -> List[Schedule]:
        """Получить все записи расписания для заказа."""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.operation),
                selectinload(self.model.equipment),
                selectinload(self.model.employee)
            )
            .where(self.model.order_id == order_id)
            .order_by(self.model.start_time.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_equipment(
        self, 
        db: AsyncSession, 
        *, 
        equipment_id: int,
        start_date: date,
        end_date: date
    ) -> List[Schedule]:
        """Получить расписание загрузки оборудования за период."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        query = (
            select(self.model)
            .options(
                selectinload(self.model.operation),
                selectinload(self.model.order)
            )
            .where(
                self.model.equipment_id == equipment_id,
                self.model.start_time >= start_datetime,
                self.model.start_time <= end_datetime
            )
            .order_by(self.model.start_time.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_employee(
        self, 
        db: AsyncSession, 
        *, 
        employee_id: int,
        start_date: date,
        end_date: date
    ) -> List[Schedule]:
        """Получить расписание загрузки сотрудника за период."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        query = (
            select(self.model)
            .options(
                selectinload(self.model.operation),
                selectinload(self.model.order)
            )
            .where(
                self.model.employee_id == employee_id,
                self.model.start_time >= start_datetime,
                self.model.start_time <= end_datetime
            )
            .order_by(self.model.start_time.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _validate_relations(self, db: AsyncSession, obj_in, exclude_current: bool = False):
        """Проверить существование связанных объектов."""
        if hasattr(obj_in, 'operation_id') and obj_in.operation_id:
            operation = await db.get(Operation, obj_in.operation_id)
            if not operation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Операция ID {obj_in.operation_id} не найдена"
                )
        
        if hasattr(obj_in, 'order_id') and obj_in.order_id:
            order = await db.get(Order, obj_in.order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Заказ ID {obj_in.order_id} не найден"
                )
        
        if hasattr(obj_in, 'equipment_id') and obj_in.equipment_id:
            equipment = await db.get(Equipment, obj_in.equipment_id)
            if not equipment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Оборудование ID {obj_in.equipment_id} не найдено"
                )
        
        if hasattr(obj_in, 'employee_id') and obj_in.employee_id:
            employee = await db.get(Employee, obj_in.employee_id)
            if not employee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Сотрудник ID {obj_in.employee_id} не найден"
                )


# Экземпляр для использования в роутах
crud_schedule = CRUDSchedule(Schedule)