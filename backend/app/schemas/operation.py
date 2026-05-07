from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class OperationBase(BaseModel):
    """
    Базовая схема для технологической операции.
    Соответствует модели Operation.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Название операции")
    sequence_number: int = Field(..., ge=1, description="Порядковый номер в технологической цепочке")
    duration_minutes: int = Field(..., ge=1, description="Длительность выполнения (мин)")
    
    # Опциональные связи с ресурсами
    equipment_id: Optional[int] = Field(None, gt=0, description="ID требуемого оборудования")
    competence_id: Optional[int] = Field(None, gt=0, description="ID требуемой квалификации")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Замес теста",
                "sequence_number": 1,
                "duration_minutes": 15,
                "equipment_id": 3,
                "competence_id": 2
            }
        }
    )

    @field_validator('sequence_number')
    @classmethod
    def validate_sequence_number(cls, v: int) -> int:
        """Валидация: порядок операций должен быть положительным."""
        if v < 1:
            raise ValueError('sequence_number должен быть >= 1')
        return v


class OperationCreate(OperationBase):
    """Схема для создания операции."""
    pass


class OperationUpdate(BaseModel):
    """Схема для обновления операции (все поля опциональны)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    sequence_number: Optional[int] = Field(None, ge=1)
    duration_minutes: Optional[int] = Field(None, ge=1)
    equipment_id: Optional[int] = Field(None, gt=0)
    competence_id: Optional[int] = Field(None, gt=0)


class OperationRead(OperationBase):
    """Схема для ответа (чтение)."""
    id: int
    recipe_id: int
    
    model_config = ConfigDict(from_attributes=True)