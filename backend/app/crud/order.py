from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import date

from app.crud.base import CRUDBase
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.order import OrderCreate, OrderUpdate
from app.schemas.order_item import OrderItemCreate


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    """
    Специфичный CRUD для заказов.
    Наследуется от базового класса, добавляет работу с позициями заказа.
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: OrderCreate
    ) -> Order:
        """
        Создать новый заказ с позициями.
        
        Args:
            db: Сессия базы данных
            obj_in: Схема для создания (может содержать items)
        
        Returns:
            Созданный объект заказа
        
        Raises:
            HTTPException 400: Если дата в прошлом
        """
        obj_data = obj_in.model_dump(exclude={'items'})
        db_obj = self.model(**obj_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        # Создаём вложенные позиции
        if obj_in.items:
            for item_data in obj_in.items:
                await self.add_item_to_order(
                    db, 
                    order_id=db_obj.id, 
                    obj_in=item_data
                )
        
        await db.refresh(db_obj)
        return db_obj

    async def get_with_items(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[Order]:
        """
        Получить заказ с позициями.
        
        Args:
            db: Сессия базы данных
            id: ID заказа
        
        Returns:
            Объект заказа с подгруженными связями или None
        """
        query = (
            select(self.model)
            .options(selectinload(self.model.items))
            .where(self.model.id == id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Order, 
        obj_in: OrderUpdate
    ) -> Order:
        """
        Обновить заказ.
        
        Args:
            db: Сессия базы данных
            db_obj: Существующий объект заказа из БД
            obj_in: Схема для обновления
        
        Returns:
            Обновлённый объект заказа
        
        Raises:
            HTTPException 400: Если новая дата в прошлом
        """
        obj_data = obj_in.model_dump(exclude_unset=True)
        
        # Проверка даты
        if "due_date" in obj_data and obj_data["due_date"] < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Дата выполнения заказа не может быть в прошлом"
            )
        
        # Обновляем поля
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def update_status(
        self, 
        db: AsyncSession, 
        *, 
        id: int, 
        status_new: str
    ) -> Order:
        """
        Обновить статус заказа.
        
        Args:
            db: Сессия базы данных
            id: ID заказа
            status_new: Новый статус (new, planned, in_progress, done)
        
        Returns:
            Обновлённый объект заказа
        
        Raises:
            HTTPException 404: Если заказ не найден
        """
        order = await self.get(db, id=id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ с ID {id} не найден"
            )
        
        order.status = status_new
        await db.commit()
        await db.refresh(order)
        
        return order

    async def remove(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[Order]:
        """
        Удалить заказ каскадно (с позициями).
        
        Args:
            db: Сессия базы данных
            id: ID заказа
        
        Returns:
            Удалённый объект заказа или None
        """
        obj = await self.get_with_items(db, id=id)
        if not obj:
            return None
        
        await db.delete(obj)
        await db.commit()
        
        return obj

    # =============================================================================
    # OrderItem CRUD
    # =============================================================================
    
    async def add_item_to_order(
        self, 
        db: AsyncSession, 
        *, 
        order_id: int, 
        obj_in: OrderItemCreate
    ) -> OrderItem:
        """
        Добавить позицию в заказ.
        
        Args:
            db: Сессия базы данных
            order_id: ID заказа
            obj_in: Схема для создания позиции
        
        Returns:
            Созданный объект позиции
        """
        db_obj = OrderItem(
            order_id=order_id,
            **obj_in.model_dump()
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_items_for_order(
        self, 
        db: AsyncSession, 
        *, 
        order_id: int
    ) -> List[OrderItem]:
        """
        Получить все позиции заказа.
        
        Args:
            db: Сессия базы данных
            order_id: ID заказа
        
        Returns:
            Список позиций заказа
        """
        query = select(OrderItem).where(OrderItem.order_id == order_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_item_in_order(
        self, 
        db: AsyncSession, 
        *, 
        order_id: int,
        item_id: int,
        obj_in: dict
    ) -> OrderItem:
        """
        Обновить позицию в заказе.
        
        Args:
            db: Сессия базы данных
            order_id: ID заказа
            item_id: ID позиции
            obj_in: Данные для обновления
        
        Returns:
            Обновлённый объект позиции
        
        Raises:
            HTTPException 404: Если позиция не найдена или не принадлежит заказу
        """
        query = select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Позиция заказа не найдена"
            )
        
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def remove_item_from_order(
        self, 
        db: AsyncSession, 
        *, 
        order_id: int,
        item_id: int
    ) -> bool:
        """
        Удалить позицию из заказа.
        
        Args:
            db: Сессия базы данных
            order_id: ID заказа
            item_id: ID позиции
        
        Returns:
            True если удалено, False если не найдено
        """
        query = select(OrderItem).where(
            OrderItem.id == item_id,
            OrderItem.order_id == order_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            return False
        
        await db.delete(db_obj)
        await db.commit()
        
        return True


# Экземпляр для использования в роутах
crud_order = CRUDOrder(Order)