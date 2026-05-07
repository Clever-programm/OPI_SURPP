from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.operation import Operation
from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.schemas.recipe_ingredient import RecipeIngredientCreate
from app.schemas.operation import OperationCreate


class CRUDRecipe(CRUDBase[Recipe, RecipeCreate, RecipeUpdate]):
    """
    Специфичный CRUD для рецептур.
    Наследуется от базового класса, добавляет работу с вложенными данными.
    """
    
    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: RecipeCreate
    ) -> Recipe:
        """
        Создать новую рецептуру с ингредиентами и операциями.
        
        Args:
            db: Сессия базы данных
            obj_in: Схема для создания (может содержать ingredients и operations)
        
        Returns:
            Созданный объект рецептуры
        
        Raises:
            HTTPException 409: Если рецептура с таким именем уже существует
        """
        obj_data = obj_in.model_dump(exclude={'ingredients', 'operations'})
        db_obj = self.model(**obj_data)
        
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Рецептура с названием '{obj_in.name}' уже существует"
            )
        
        # Создаём вложенные ингредиенты
        if obj_in.ingredients:
            for ingredient_data in obj_in.ingredients:
                await self.add_ingredient_to_recipe(
                    db, 
                    recipe_id=db_obj.id, 
                    obj_in=ingredient_data
                )
        
        # Создаём вложенные операции
        if obj_in.operations:
            for operation_data in obj_in.operations:
                await self.add_operation_to_recipe(
                    db, 
                    recipe_id=db_obj.id, 
                    obj_in=operation_data
                )
            
        # Жадная загрузка связей перед возвратом
        await db.refresh(db_obj)
        
        # Перезагружаем объект с отношениями через отдельный запрос
        query = (
            select(self.model)
            .options(
                selectinload(self.model.ingredients),
                selectinload(self.model.operations)
            )
            .where(self.model.id == db_obj.id)
        )
        result = await db.execute(query)
        db_obj = result.scalar_one()
        
        return db_obj

    async def get_with_details(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[Recipe]:
        """
        Получить рецептуру с ингредиентами и операциями.
        
        Args:
            db: Сессия базы данных
            id: ID рецептуры
        
        Returns:
            Объект рецептуры с подгруженными связями или None
        """
        query = (
            select(self.model)
            .options(
                selectinload(self.model.ingredients),
                selectinload(self.model.operations)
            )
            .where(self.model.id == id)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: Recipe, 
        obj_in: RecipeUpdate
    ) -> Recipe:
        """
        Обновить рецептуру с обработкой дубликатов.
        
        Args:
            db: Сессия базы данных
            db_obj: Существующий объект рецептуры из БД
            obj_in: Схема для обновления
        
        Returns:
            Обновлённый объект рецептуры
        
        Raises:
            HTTPException 409: Если новое имя уже занято другой рецептурой
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
                    detail=f"Рецептура с названием '{obj_data['name']}' уже существует"
                )
        
        # Обновляем поля
        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def remove(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[Recipe]:
        """
        Удалить рецептуру каскадно (с ингредиентами и операциями).
        
        Args:
            db: Сессия базы данных
            id: ID рецептуры
        
        Returns:
            Удалённый объект рецептуры или None
        """
        obj = await self.get_with_details(db, id=id)
        if not obj:
            return None
        
        # Каскадное удаление связанных записей
        await db.delete(obj)
        await db.commit()
        
        return obj

    # =============================================================================
    # RecipeIngredient CRUD
    # =============================================================================
    
    async def add_ingredient_to_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int, 
        obj_in: RecipeIngredientCreate
    ) -> RecipeIngredient:
        """
        Добавить ингредиент в рецептуру.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
            obj_in: Схема для создания связи
        
        Returns:
            Созданный объект связи
        """
        db_obj = RecipeIngredient(
            recipe_id=recipe_id,
            **obj_in.model_dump()
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_ingredients_for_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int
    ) -> List[RecipeIngredient]:
        """
        Получить все ингредиенты рецептуры.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
        
        Returns:
            Список связей рецепт-ингредиент
        """
        query = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def update_ingredient_in_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int,
        ingredient_link_id: int,
        quantity: float
    ) -> RecipeIngredient:
        """
        Обновить количество ингредиента в рецептуре.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
            ingredient_link_id: ID связи рецепт-ингредиент
            quantity: Новое количество
        
        Returns:
            Обновлённый объект связи
        
        Raises:
            HTTPException 404: Если связь не найдена или не принадлежит рецепту
        """
        query = select(RecipeIngredient).where(
            RecipeIngredient.id == ingredient_link_id,
            RecipeIngredient.recipe_id == recipe_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Связь рецепт-ингредиент не найдена"
            )
        
        db_obj.quantity = quantity
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def remove_ingredient_from_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int,
        ingredient_link_id: int
    ) -> bool:
        """
        Удалить ингредиент из рецептуры.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
            ingredient_link_id: ID связи рецепт-ингредиент
        
        Returns:
            True если удалено, False если не найдено
        """
        query = select(RecipeIngredient).where(
            RecipeIngredient.id == ingredient_link_id,
            RecipeIngredient.recipe_id == recipe_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            return False
        
        await db.delete(db_obj)
        await db.commit()
        
        return True

    # =============================================================================
    # Operation CRUD
    # =============================================================================
    
    async def add_operation_to_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int, 
        obj_in: OperationCreate
    ) -> Operation:
        """
        Добавить операцию в рецептуру.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
            obj_in: Схема для создания операции
        
        Returns:
            Созданный объект операции
        """
        db_obj = Operation(
            recipe_id=recipe_id,
            **obj_in.model_dump()
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_operations_for_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int
    ) -> List[Operation]:
        """
        Получить все операции рецептуры.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
        
        Returns:
            Список операций
        """
        query = (
            select(Operation)
            .where(Operation.recipe_id == recipe_id)
            .order_by(Operation.sequence_number)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def update_operation(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int,
        operation_id: int,
        obj_in: dict
    ) -> Operation:
        """
        Обновить операцию в рецептуре.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
            operation_id: ID операции
            obj_in: Данные для обновления
        
        Returns:
            Обновлённый объект операции
        
        Raises:
            HTTPException 404: Если операция не найдена или не принадлежит рецепту
        """
        query = select(Operation).where(
            Operation.id == operation_id,
            Operation.recipe_id == recipe_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Операция не найдена"
            )
        
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def remove_operation_from_recipe(
        self, 
        db: AsyncSession, 
        *, 
        recipe_id: int,
        operation_id: int
    ) -> bool:
        """
        Удалить операцию из рецептуры.
        
        Args:
            db: Сессия базы данных
            recipe_id: ID рецептуры
            operation_id: ID операции
        
        Returns:
            True если удалено, False если не найдено
        """
        query = select(Operation).where(
            Operation.id == operation_id,
            Operation.recipe_id == recipe_id
        )
        result = await db.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            return False
        
        await db.delete(db_obj)
        await db.commit()
        
        return True


# Экземпляр для использования в роутах
crud_recipe = CRUDRecipe(Recipe)