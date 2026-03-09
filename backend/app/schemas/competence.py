from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CompetenceBase(BaseModel):
    """
    Базовая схема для компетенции.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Название компетенции")
    description: Optional[str] = Field(None, max_length=500, description="Описание навыков")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Кондитер 3 разряда",
                "description": "Приготовление кремов и декорирование"
            }
        }
    )


class CompetenceCreate(CompetenceBase):
    """Схема для создания новой компетенции."""
    pass


class CompetenceUpdate(BaseModel):
    """Схема для обновления компетенции."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CompetenceRead(CompetenceBase):
    """Схема для ответа API (чтение)."""
    id: int

    model_config = ConfigDict(from_attributes=True)