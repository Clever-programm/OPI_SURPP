from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.employee_competence import EmployeeCompetenceCreate, EmployeeCompetenceRead


class EmployeeBase(BaseModel):
    """
    Базовая схема сотрудника.
    Соответствует модели Employee.
    """
    name: str = Field(..., min_length=3, max_length=150, description="ФИО сотрудника")
    active: bool = Field(default=True, description="Статус: активен / не активен")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Иванова Мария Петровна",
                "active": True
            }
        }
    )


class EmployeeCreate(EmployeeBase):
    """
    Схема для создания сотрудника.
    Поддерживает вложенное добавление компетенций.
    """
    competences: Optional[List[EmployeeCompetenceCreate]] = Field(
        None, 
        description="Список компетенций (разрядов) сотрудника"
    )

    @field_validator('competences')
    @classmethod
    def validate_competences_unique(cls, v: Optional[List[EmployeeCompetenceCreate]]) -> Optional[List[EmployeeCompetenceCreate]]:
        """Проверка: одна компетенция не может быть добавлена сотруднику дважды."""
        if v:
            ids = [item.competence_id for item in v]
            if len(ids) != len(set(ids)):
                raise ValueError('Одна и та же компетенция не может быть добавлена сотруднику несколько раз')
        return v


class EmployeeUpdate(BaseModel):
    """Схема для обновления сотрудника (частичное обновление)."""
    name: Optional[str] = Field(None, min_length=3, max_length=150)
    active: Optional[bool] = None


class EmployeeRead(EmployeeBase):
    """Схема для ответа (чтение) — базовая информация."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class EmployeeWithCompetences(EmployeeRead):
    """
    Расширенная схема для ответа с компетенциями сотрудника.
    Используется в GET /employees/{id} для отображения квалификации.
    """
    competences: List[EmployeeCompetenceRead] = Field(default_factory=list)