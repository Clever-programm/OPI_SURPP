from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date, datetime

from app.schemas.order_item import OrderItemCreate, OrderItemRead

class OrderBase(BaseModel):
    """
    Базовая схема заказа.
    Соответствует модели Order.
    """
    due_date: date = Field(..., description="Дата выполнения заказа (дедлайн)")
    priority: int = Field(default=2, ge=1, le=3, description="Приоритет: 1=высокий, 2=средний, 3=низкий")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "due_date": "2025-03-08",
                "priority": 1,
            }
        }
    )

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: date) -> date:
        """Проверка: дата выполнения не может быть в прошлом."""
        if v < date.today():
            raise ValueError('Дата выполнения заказа не может быть в прошлом')
        return v


class OrderCreate(OrderBase):
    """
    Схема для создания заказа.
    Поддерживает вложенное создание позиций заказа.
    """
    items: Optional[List[OrderItemCreate]] = Field(None, description="Список позиций заказа (изделия)")

    @field_validator('items')
    @classmethod
    def validate_items_unique(cls, v: Optional[List[OrderItemCreate]]) -> Optional[List[OrderItemCreate]]:
        """Проверка: одна рецептура не может быть добавлена в заказ дважды."""
        if v:
            ids = [item.recipe_id for item in v]
            if len(ids) != len(set(ids)):
                raise ValueError('Одна и та же рецептура не может быть добавлена в заказ несколько раз')
        return v


class OrderUpdate(BaseModel):
    """Схема для обновления заказа (частичное обновление)."""
    due_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    comment: Optional[str] = Field(None, max_length=500)

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[date]) -> Optional[date]:
        """Проверка: дата выполнения не может быть в прошлом."""
        if v and v < date.today():
            raise ValueError('Дата выполнения заказа не может быть в прошлом')
        return v


class OrderStatusUpdate(BaseModel):
    """
    Схема для обновления статуса заказа.
    Используется в PATCH /orders/{id}/status
    """
    status: str = Field(..., pattern="^(new|planned|in_progress|done)$", description="Статус заказа")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "in_progress"
            }
        }
    )


class OrderRead(OrderBase):
    """Схема для ответа (чтение) — базовая информация."""
    id: int
    status: str = Field(default="new", description="Статус заказа")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderWithItems(OrderRead):
    """
    Расширенная схема для ответа с вложенными позициями.
    Используется в GET /orders/{id} для отображения полного состава заказа.
    """
    items: List[OrderItemRead] = Field(default_factory=list)
    
    # Вычисляемое поле: общее количество изделий в заказе
    @property
    def total_items_quantity(self) -> int:
        return sum(item.quantity for item in self.items)