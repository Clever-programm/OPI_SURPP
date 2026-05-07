from typing import Optional, List
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.stock import Stock
from app.models.ingredient import Ingredient
from app.schemas.stock import (
    StockReceive,
    StockWriteOff,
    StockCheckRequest,
    StockCheckResult,
    StockCheckResponse,
    StockExpiring,
)


class CRUDStock:
    """
    CRUD-операции для складского учёта.
    """
    
    async def get_stock_by_ingredient(
        self, 
        db: AsyncSession, 
        *, 
        ingredient_id: int
    ) -> Optional[Stock]:
        """
        Получить складской остаток по ингредиенту.
        
        Args:
            db: Сессия базы данных
            ingredient_id: ID ингредиента
        
        Returns:
            Объект Stock или None
        """
        query = (
            select(Stock)
            .where(and_(Stock.ingredient_id == ingredient_id, Stock.quantity > 0))
            .order_by(Stock.received_at.asc())
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def get_all_stock(
        self, 
        db: AsyncSession,
        *,
        page: int = 1,
        limit: int = 50,
        ingredient_id: Optional[int] = None,
        expiring_days: Optional[int] = None
    ) -> dict:
        """
        Получить все складские остатки с пагинацией и фильтрацией.
        
        Args:
            db: Сессия базы данных
            page: Номер страницы
            limit: Записей на странице
            ingredient_id: Фильтр по ингредиенту
            expiring_days: Показать только истекающие через N дней
        
        Returns:
            Словарь с данными и мета-информацией
        """
        
        query = select(Stock).options(selectinload(Stock.ingredient)).where(Stock.quantity > 0)
        count_query = select(func.count()).select_from(Stock).where(Stock.quantity > 0)
        
        # Фильтр по ингредиенту
        if ingredient_id:
            query = query.where(Stock.ingredient_id == ingredient_id)
            count_query = count_query.where(Stock.ingredient_id == ingredient_id)
        
        # Фильтр по истекающим срокам
        if expiring_days:
            cutoff_date = date.today() + timedelta(days=expiring_days)
            query = query.where(
                and_(
                    Stock.expiration_date != None,
                    Stock.expiration_date <= cutoff_date
                )
            )
            count_query = count_query.where(
                and_(
                    Stock.expiration_date != None,
                    Stock.expiration_date <= cutoff_date
                )
            )
        
        # Пагинация
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

    async def get_total_quantity(
        self, 
        db: AsyncSession, 
        *, 
        ingredient_id: int
    ) -> float:
        """
        Получить общее количество ингредиента на складе (сумма всех партий).
        
        Args:
            db: Сессия базы данных
            ingredient_id: ID ингредиента
        
        Returns:
            Общее количество
        """
        query = select(func.sum(Stock.quantity)).where(Stock.ingredient_id == ingredient_id)
        result = await db.execute(query)
        total = result.scalar()
        return total if total else 0.0
 
    async def receive_stock(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: StockReceive
    ) -> Stock:
        """
        Зарегистрировать поступление сырья на склад.
        Всегда создаёт новую запись (партию) для точного учёта сроков годности.
        """
        # Валидация срока годности
        if obj_in.expiration_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок годности не может быть в прошлом"
            )
        
        # Создаём новую запись для каждой партии
        stock = Stock(
            ingredient_id=obj_in.ingredient_id,
            quantity=obj_in.quantity,
            expiration_date=obj_in.expiration_date
        )
        db.add(stock)
        
        await db.commit()
        await db.refresh(stock)
        
        return stock

    async def write_off_stock(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: StockWriteOff
    ) -> Stock:
        """
        Зарегистрировать списание сырья со склада.
        Логика:
        1. Если указан stock_id — списываем из конкретной партии.
        2. Если не указан — списываем по FIFO (по дате поступления).
        """
        if obj_in.stock_id:
            # Списание из конкретной партии
            query = select(Stock).where(and_(Stock.id == obj_in.stock_id, Stock.ingredient_id == obj_in.ingredient_id))
            result = await db.execute(query)
            batch = result.scalar_one_or_none()
            
            if not batch:
                raise HTTPException(status_code=404, detail=f"Партия ID {obj_in.stock_id} для этого ингредиента не найдена")
            
            if batch.quantity < obj_in.quantity:
                raise HTTPException(status_code=409, detail=f"В выбранной партии недостаточно сырья. Доступно: {batch.quantity}")
            
            batch.quantity -= obj_in.quantity
            await db.commit()
            await db.refresh(batch)
            return batch

        # Иначе — классический FIFO по дате поступления
        total_available = await self.get_total_quantity(db, ingredient_id=obj_in.ingredient_id)
        
        if total_available < obj_in.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Недостаточно сырья. Доступно: {total_available}, требуется: {obj_in.quantity}"
            )
        
        # Сортируем по дате поступления (старые первыми)
        query = (
            select(Stock)
            .where(and_(Stock.ingredient_id == obj_in.ingredient_id, Stock.quantity > 0))
            .order_by(Stock.received_at.asc())
        )
        result = await db.execute(query)
        batches = result.scalars().all()
        
        remaining_to_write_off = obj_in.quantity
        last_updated_stock = None
        
        for batch in batches:
            if remaining_to_write_off <= 0:
                break
                
            if batch.quantity <= remaining_to_write_off:
                remaining_to_write_off -= batch.quantity
                batch.quantity = 0
            else:
                batch.quantity -= remaining_to_write_off
                remaining_to_write_off = 0
            
            last_updated_stock = batch
        
        await db.commit()
        if last_updated_stock:
            await db.refresh(last_updated_stock)
            return last_updated_stock
        
        raise HTTPException(status_code=404, detail="Партии для списания не найдены")

    async def write_off_for_order(
        self, 
        db: AsyncSession, 
        *, 
        order_id: int,
        items: List[dict]
    ) -> bool:
        """
        Списать сырьё для производства по заказу.
        
        Args:
            db: Сессия базы данных
            order_id: ID заказа
            items: Список ингредиентов для списания
                [{"ingredient_id": 1, "quantity": 50.0}, ...]
        
        Returns:
            True если все списания успешны
        
        Raises:
            HTTPException 409: Если любого ингредиента недостаточно
        """
        # Сначала проверяем доступность всех ингредиентов
        for item in items:
            stock = await self.get_stock_by_ingredient(db, ingredient_id=item["ingredient_id"])
            
            if not stock:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ингредиент ID {item['ingredient_id']} отсутствует на складе"
                )
            
            if stock.quantity < item["quantity"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Недостаточно ингредиента ID {item['ingredient_id']}. "
                           f"Доступно: {stock.quantity}, требуется: {item['quantity']}"
                )
        
        # Все проверки пройдены — выполняем списание
        for item in items:
            write_off = StockWriteOff(
                ingredient_id=item["ingredient_id"],
                quantity=item["quantity"],
                order_id=order_id
            )
            await self.write_off_stock(db, obj_in=write_off)
        
        return True

    async def check_availability(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: StockCheckRequest
    ) -> StockCheckResponse:
        """
        Проверить достаточность сырья для выполнения заказов.
        
        Бизнес-логика:
        - Проверка каждого ингредиента из запроса
        - Расчёт дефицита
        - Предупреждения о сроках годности
        
        Args:
            db: Сессия базы данных
            obj_in: Запрос на проверку
        
        Returns:
            StockCheckResponse с результатами проверки
        """
        results = []
        all_sufficient = True
        
        for item in obj_in.items:
            # Получаем складской остаток
            stock = await self.get_stock_by_ingredient(db, ingredient_id=item.ingredient_id)
            
            # Получаем название ингредиента
            ingredient_query = select(Ingredient).where(Ingredient.id == item.ingredient_id)
            ingredient_result = await db.execute(ingredient_query)
            ingredient = ingredient_result.scalar_one_or_none()
            
            ingredient_name = ingredient.name if ingredient else f"Unknown ID {item.ingredient_id}"
            available = stock.quantity if stock else 0.0
            is_sufficient = available >= item.required_quantity
            
            if not is_sufficient:
                all_sufficient = False
            
            # Проверка срока годности
            expiry_warning = None
            if stock and stock.expiration_date:
                days_until_expiry = (stock.expiration_date - date.today()).days
                if days_until_expiry <= 7:
                    expiry_warning = f"Истекает через {days_until_expiry} дн."
            
            results.append(StockCheckResult(
                ingredient_id=item.ingredient_id,
                ingredient_name=ingredient_name,
                required=item.required_quantity,
                available=available,
                is_sufficient=is_sufficient,
                deficit=max(0, item.required_quantity - available),
                expiry_warning=expiry_warning
            ))
        
        return StockCheckResponse(
            is_all_sufficient=all_sufficient,
            results=results
        )
   
    async def get_expiring_soon(
        self, 
        db: AsyncSession, 
        *, 
        days: int = 7
    ) -> List[StockExpiring]:
        """
        Получить ингредиенты с истекающим сроком годности.
        
        Args:
            db: Сессия базы данных
            days: Порог в днях (по умолчанию 7 дней)
        
        Returns:
            Список истекающих ингредиентов
        """
        
        cutoff_date = date.today() + timedelta(days=days)
        
        query = (
            select(Stock, Ingredient)
            .join(Ingredient, Stock.ingredient_id == Ingredient.id)
            .where(
                and_(
                    Stock.expiration_date != None,
                    Stock.expiration_date <= cutoff_date,
                    Stock.expiration_date >= date.today(),
                    Stock.quantity > 0
                )
            )
            .order_by(Stock.expiration_date.asc())
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        expiring_list = []
        for stock, ingredient in rows:
            days_until_expiry = (stock.expiration_date - date.today()).days
            
            expiring_list.append(StockExpiring(
                ingredient_id=ingredient.id,
                ingredient_name=ingredient.name,
                quantity=stock.quantity,
                expiration_date=stock.expiration_date,
                days_until_expiry=days_until_expiry
            ))
        
        return expiring_list


# Экземпляр для использования в роутах
crud_stock = CRUDStock()