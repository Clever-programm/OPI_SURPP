from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class OrderItemBase(BaseModel):
    """
    Базовая схема для позиции заказа.
    Соответствует модели OrderItem (связующая таблица).
    """
    recipe_id: int = Field(..., gt=0, description="ID рецептуры изделия")
    quantity: int = Field(..., ge=1, description="Количество изделий для заказа")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recipe_id": 1,
                "quantity": 10
            }
        }
    )


class OrderItemCreate(OrderItemBase):
    """Схема для добавления позиции в заказ."""
    pass


class OrderItemUpdate(BaseModel):
    """Схема для обновления позиции заказа."""
    recipe_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=1)


class OrderItemRead(OrderItemBase):
    """Схема для ответа (чтение)."""
    id: int
    order_id: int
    
    model_config = ConfigDict(from_attributes=True)