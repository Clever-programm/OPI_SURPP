from typing import Any, Dict, Generic, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import Base

# Типы для обобщённого класса (Generics)
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Универсальный асинхронный CRUD-класс.
    
    Предоставляет базовые операции для всех моделей:
    - create: создание записи
    - get: получение по ID
    - get_multi: получение списка с пагинацией и сортировкой
    - update: обновление записи
    - remove: удаление записи
    - exists: проверка существования по полю
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Инициализация CRUD-класса.
        
        Args:
            model: SQLAlchemy модель (например, Ingredient, Equipment)
        """
        self.model = model

    async def get(
        self, 
        db: AsyncSession, 
        id: int
    ) -> Optional[ModelType]:
        """
        Получить запись по ID.
        
        Returns:
            Объект модели или None, если не найдено.
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        page: int = 1, 
        limit: int = 50,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        **filters
    ) -> Dict[str, Any]:
        """
        Получить список записей с пагинацией, сортировкой и фильтрацией.
        
        Args:
            page: Номер страницы (начинается с 1)
            limit: Количество записей на странице
            sort_by: Поле для сортировки
            sort_order: Порядок сортировки ("asc" или "desc")
            **filters: Динамические фильтры (например, name="Мука")
        
        Returns:
            Словарь с данными и мета-информацией:
            {
                "items": [...],
                "total": 100,
                "page": 1,
                "limit": 50,
                "pages": 2
            }
        """
        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)
        
        # Применение фильтров
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
                count_query = count_query.where(getattr(self.model, field) == value)
        
        # Сортировка
        if sort_by and hasattr(self.model, sort_by):
            sort_column = getattr(self.model, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        
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

    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: CreateSchemaType
    ) -> ModelType:
        """
        Создать новую запись.
        
        Args:
            obj_in: Pydantic схема для создания
        
        Returns:
            Созданный объект модели
        
        Raises:
            IntegrityError: При нарушении уникальности (дубликат name)
        """
        obj_data = obj_in.model_dump()
        
        db_obj = self.model(**obj_data)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def update(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Обновить существующую запись.
        
        Args:
            db_obj: Объект модели из БД
            obj_in: Pydantic схема для обновления или dict
        
        Returns:
            Обновлённый объект модели
        """
        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump(exclude_unset=True)
        else:
            obj_data = obj_in
        
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
    ) -> Optional[ModelType]:
        """
        Удалить запись по ID.
        
        Args:
            id: ID записи для удаления
        
        Returns:
            Удалённый объект модели или None, если не найдено
        """
        obj = await self.get(db, id=id)
        if not obj:
            return None
        
        await db.delete(obj)
        await db.commit()
        
        return obj

    async def exists(
        self, 
        db: AsyncSession, 
        *, 
        field: str, 
        value: Any,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Проверить существование записи по полю.
        
        Args:
            field: Имя поля для проверки (например, "name")
            value: Значение для проверки
            exclude_id: Исключить запись с этим ID (для обновления)
        
        Returns:
            True, если запись существует, False иначе
        """
        if not hasattr(self.model, field):
            return False
        
        query = select(func.count()).where(
            getattr(self.model, field) == value
        )
        
        if exclude_id:
            query = query.where(self.model.id != exclude_id)
        
        result = await db.execute(query)
        count = result.scalar()
        
        return count > 0