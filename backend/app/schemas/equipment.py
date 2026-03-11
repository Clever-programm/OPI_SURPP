from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EquipmentBase(BaseModel):
    """
    Базовая схема для оборудования.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Название оборудования")
    quantity: int = Field(default=1, ge=0, description="Количество единиц")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Печь конвекционная Unox",
                "quantity": 2
            }
        }
    )


class EquipmentCreate(EquipmentBase):
    """Схема для создания нового оборудования."""
    pass


class EquipmentUpdate(BaseModel):
    """Схема для обновления оборудования."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    quantity: Optional[int] = Field(None, ge=0)


class EquipmentRead(EquipmentBase):
    """Схема для ответа API (чтение)."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class EquipmentQuantityUpdate(BaseModel):
    """
    Специальная схема для PATCH /quantity.
    """
    quantity: int = Field(..., ge=0, description="Новое количество")