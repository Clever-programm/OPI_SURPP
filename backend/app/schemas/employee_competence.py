from pydantic import BaseModel, Field, ConfigDict


class EmployeeCompetenceBase(BaseModel):
    """
    Базовая схема связи сотрудника с компетенцией.
    Соответствует модели EmployeeCompetence (many-to-many).
    """
    employee_id: int = Field(..., gt=0, description="ID сотрудника")
    competence_id: int = Field(..., gt=0, description="ID компетенции (разряда)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "employee_id": 1,
                "competence_id": 3
            }
        }
    )


class EmployeeCompetenceCreate(EmployeeCompetenceBase):
    """Схема для добавления компетенции сотруднику."""
    pass


class EmployeeCompetenceRead(EmployeeCompetenceBase):
    """Схема для ответа (чтение) с названием компетенции."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)