from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.employee import Employee
from app.models.employee_competence import EmployeeCompetence
from app.models.competence import Competence
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.schemas.employee_competence import EmployeeCompetenceCreate


class CRUDEmployee(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    """
    CRUD-операции для сотрудников.
    
    Реализует требования ТЗ:
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: EmployeeCreate
    ) -> Employee:
        """Создать нового сотрудника с компетенциями."""
        
        obj_data = obj_in.model_dump(exclude={'competences'})
        db_obj = self.model(**obj_data)
        
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Сотрудник с именем '{obj_in.name}' уже существует"
            )
        
        # Создаём вложенные компетенции
        if obj_in.competences:
            for competence_data in obj_in.competences:
                await self.add_competence_to_employee(
                    db, 
                    employee_id=db_obj.id, 
                    obj_in=competence_data
                )
        
        # Жадная загрузка компетенций перед возвратом
        query = (
            select(self.model)
            .options(selectinload(self.model.competences))
            .where(self.model.id == db_obj.id)
        )
        result = await db.execute(query)
        db_obj = result.scalar_one()
        
        return db_obj

    async def get_with_competences(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[Employee]:
        """
        Получить сотрудника с компетенциями.
        
        Args:
            db: Сессия базы данных
            id: ID сотрудника
        
        Returns:
            Объект сотрудника с подгруженными связями или None
        """
        query = (
            select(self.model)
            .options(selectinload(self.model.competences))
            .where(self.model.id == id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Employee, 
        obj_in: EmployeeUpdate
    ) -> Employee:
        """
        Обновить сотрудника с обработкой дубликатов.
        
        Args:
            db: Сессия базы данных
            db_obj: Существующий объект сотрудника из БД
            obj_in: Схема для обновления
        
        Returns:
            Обновлённый объект сотрудника
        
        Raises:
            HTTPException 409: Если новое имя уже занято другим сотрудником
        """
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Если меняется name, проверяем уникальность
        if "name" in obj_data and obj_data["name"] != db_obj.name:
            exists = await self.exists(
                db, 
                field="name", 
                value=obj_data["name"], 
                exclude_id=db_obj.id
            )
            if exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Сотрудник с именем '{obj_data['name']}' уже существует"
                )
        
        # Обновляем поля
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_available(
        self, 
        db: AsyncSession
    ) -> List[Employee]:
        """Получить только активных сотрудников."""
        
        query = (
            select(self.model)
            .options(selectinload(self.model.competences))
            .where(self.model.active == True)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def add_competence_to_employee(
        self, 
        db: AsyncSession, 
        *, 
        employee_id: int, 
        obj_in: EmployeeCompetenceCreate
    ) -> EmployeeCompetence:
        """
        Добавить компетенцию сотруднику.
        
        Args:
            db: Сессия базы данных
            employee_id: ID сотрудника
            obj_in: Схема для создания связи
        
        Returns:
            Созданный объект связи
        
        Raises:
            HTTPException 409: Если компетенция уже назначена сотруднику
        """
        # Проверяем, не назначена ли уже эта компетенция
        exists_query = select(EmployeeCompetence).where(
            EmployeeCompetence.employee_id == employee_id,
            EmployeeCompetence.competence_id == obj_in.competence_id
        )
        exists_result = await db.execute(exists_query)
        if exists_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Компетенция ID {obj_in.competence_id} уже назначена сотруднику ID {employee_id}"
            )
        
        # Проверяем существование компетенции
        competence_query = select(Competence).where(Competence.id == obj_in.competence_id)
        competence_result = await db.execute(competence_query)
        if not competence_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Компетенция ID {obj_in.competence_id} не найдена"
            )
        
        # Создаём связь
        db_obj = EmployeeCompetence(
            employee_id=employee_id,
            **obj_in.model_dump(exclude={'employee_id'})
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_competences_for_employee(
        self, 
        db: AsyncSession, 
        *, 
        employee_id: int
    ) -> List[EmployeeCompetence]:
        """
        Получить все компетенции сотрудника.
        
        Args:
            db: Сессия базы данных
            employee_id: ID сотрудника
        
        Returns:
            Список связей сотрудник-компетенция
        """
        query = select(EmployeeCompetence).where(
            EmployeeCompetence.employee_id == employee_id
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def remove_competence_from_employee(
        self, 
        db: AsyncSession, 
        *, 
        employee_id: int,
        competence_id: int
    ) -> bool:
        """
        Удалить компетенцию у сотрудника.
        
        Args:
            db: Сессия базы данных
            employee_id: ID сотрудника
            competence_id: ID компетенции
        
        Returns:
            True если удалено, False если не найдено
        """
        query = select(EmployeeCompetence).where(
            EmployeeCompetence.employee_id == employee_id,
            EmployeeCompetence.competence_id == competence_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            return False
        
        await db.delete(db_obj)
        await db.commit()
        
        return True

    async def get_employees_by_competence(
        self, 
        db: AsyncSession, 
        *, 
        competence_id: int,
        active_only: bool = True
    ) -> List[Employee]:
        """
        Получить сотрудников с определённой компетенцией.
        
        Args:
            db: Сессия базы данных
            competence_id: ID компетенции
            active_only: Только активные сотрудники
        
        Returns:
            Список сотрудников с указанной компетенцией
        """
        query = (
            select(Employee)
            .join(EmployeeCompetence, Employee.id == EmployeeCompetence.employee_id)
            .where(EmployeeCompetence.competence_id == competence_id)
        )
        
        if active_only:
            query = query.where(Employee.active == True)
        
        result = await db.execute(query)
        return result.scalars().all()


# Экземпляр для использования в роутах
crud_employee = CRUDEmployee(Employee)