from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate


class CRUDEquipment(CRUDBase[Equipment, EquipmentCreate, EquipmentUpdate]):
    """
    Специфичный CRUD для оборудования.
    Наследуется от базового класса, добавляет обработку уникальности name.
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: EquipmentCreate
    ) -> Equipment:
        """
        Создать новую единицу оборудования.
        
        Args:
            db: Сессия базы данных
            obj_in: Схема для создания
        
        Returns:
            Созданный объект оборудования
        
        Raises:
            HTTPException 409: Если оборудование с таким именем уже существует
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
                detail=f"Оборудование с названием '{obj_in.name}' уже существует"
            )

    async def get_by_name(
        self, 
        db: AsyncSession, 
        *, 
        name: str
    ) -> Optional[Equipment]:
        """
        Получить оборудование по названию.
        
        Args:
            db: Сессия базы данных
            name: Название оборудования
        
        Returns:
            Объект оборудования или None
        """
        query = select(self.model).where(self.model.name == name)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Equipment, 
        obj_in: EquipmentUpdate
    ) -> Equipment:
        """
        Обновить оборудование с обработкой дубликатов.
        
        Args:
            db: Сессия базы данных
            db_obj: Существующий объект оборудования из БД
            obj_in: Схема для обновления
        
        Returns:
            Обновлённый объект оборудования
        
        Raises:
            HTTPException 409: Если новое имя уже занято другим оборудованием
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
                    detail=f"Оборудование с названием '{obj_data['name']}' уже существует"
                )
        
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def update_quantity(
        self, 
        db: AsyncSession, 
        *, 
        id: int, 
        quantity: int
    ) -> Equipment:
        """
        Обновить количество оборудования (специальная операция).
        
        Args:
            db: Сессия базы данных
            id: ID оборудования
            quantity: Новое количество
        
        Returns:
            Обновлённый объект оборудования
        
        Raises:
            HTTPException 404: Если оборудование не найдено
        """
        equipment = await self.get(db, id=id)
        
        if not equipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Оборудование с ID {id} не найдено"
            )
        
        equipment.quantity = quantity
        await db.commit()
        await db.refresh(equipment)
        
        return equipment

    async def get_available(
        self, 
        db: AsyncSession
    ) -> list[Equipment]:
        """
        Получить только доступное оборудование (quantity > 0).
        
        Args:
            db: Сессия базы данных
        
        Returns:
            Список доступного оборудования
        """
        query = select(self.model).where(self.model.quantity > 0)
        result = await db.execute(query)
        return result.scalars().all()


crud_equipment = CRUDEquipment(Equipment)