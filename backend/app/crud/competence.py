from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.competence import Competence
from app.schemas.competence import CompetenceCreate, CompetenceUpdate


class CRUDCompetence(CRUDBase[Competence, CompetenceCreate, CompetenceUpdate]):
    """
    Специфичный CRUD для компетенций.
    Наследуется от базового класса, добавляет обработку уникальности name.
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: CompetenceCreate
    ) -> Competence:
        """
        Создать новую компетенцию.
        
        Args:
            db: Сессия базы данных
            obj_in: Схема для создания
        
        Returns:
            Созданный объект компетенции
        
        Raises:
            HTTPException 409: Если компетенция с таким именем уже существует
        """
        obj_data = obj_in.model_dump()
        db_obj = self.model(**obj_data)
        
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Компетенция с названием '{obj_in.name}' уже существует"
            )

    async def get_by_name(
        self, 
        db: AsyncSession, 
        *, 
        name: str
    ) -> Optional[Competence]:
        """
        Получить компетенцию по названию.
        
        Args:
            db: Сессия базы данных
            name: Название компетенции
        
        Returns:
            Объект компетенции или None
        """
        query = select(self.model).where(self.model.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Competence, 
        obj_in: CompetenceUpdate
    ) -> Competence:
        """
        Обновить компетенцию с обработкой дубликатов.
        
        Args:
            db: Сессия базы данных
            db_obj: Существующий объект компетенции из БД
            obj_in: Схема для обновления
        
        Returns:
            Обновлённый объект компетенции
        
        Raises:
            HTTPException 409: Если новое имя уже занято другой компетенцией
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
                    detail=f"Компетенция с названием '{obj_data['name']}' уже существует"
                )
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj


crud_competence = CRUDCompetence(Competence)