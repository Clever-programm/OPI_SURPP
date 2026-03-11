from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class UnitType(str, Enum):
    """Допустимые единицы измерения."""
    KG = "кг"
    G = "г"
    L = "л"
    ML = "мл"
    PCS = "шт"


class IngredientBase(BaseModel):
    """
    Базовая схема для ингредиента.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Название ингредиента")
    unit: UnitType = Field(..., description="Единица измерения")
    shelf_life_days: int = Field(..., gt=0, description="Срок годности в днях")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Мука пшеничная",
                "unit": "кг",
                "shelf_life_days": 365
            }
        }
    )


class IngredientCreate(IngredientBase):
    """Схема для создания нового ингредиента."""
    pass


class IngredientUpdate(BaseModel):
    """
    Схема для обновления ингредиента.
    Все поля необязательны (Partial Update).
    """
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    unit: Optional[UnitType] = None
    shelf_life_days: Optional[int] = Field(None, gt=0)


class IngredientRead(IngredientBase):
    """
    Схема для ответа API (чтение).
    """
    id: int

    model_config = ConfigDict(from_attributes=True)