from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime, date


class ScheduleBase(BaseModel):
    """
    Базовая схема записи производственного расписания.
    Соответствует модели Schedule.
    """
    start_time: datetime = Field(..., description="Начало операции")
    end_time: datetime = Field(..., description="Окончание операции")
    duration_minutes: int = Field(..., gt=0, description="Длительность операции в минутах")
    operation_id: int = Field(..., gt=0, description="ID технологической операции")
    order_id: int = Field(..., gt=0, description="ID производственного заказа")
    equipment_id: Optional[int] = Field(None, gt=0, description="ID оборудования (если требуется)")
    employee_id: Optional[int] = Field(None, gt=0, description="ID сотрудника (если требуется)")
    name: Optional[str] = Field(None, max_length=100, description="Название операции в расписании")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_time": "2026-04-15T09:00:00+00:00",
                "end_time": "2026-04-15T11:00:00+00:00",
                "duration_minutes": 120,
                "operation_id": 1,
                "order_id": 5,
                "equipment_id": 3,
                "employee_id": 2,
                "name": "Замес теста для торта Прага"
            }
        }
    )

    @model_validator(mode='after')
    def validate_time_range(self) -> 'ScheduleBase':
        """Проверка: end_time должен быть после start_time."""
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError('Время окончания должно быть позже времени начала')
        return self


class ScheduleRead(ScheduleBase):
    """Схема для ответа (чтение)."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class ScheduleCreate(ScheduleBase):
    """
    Схема для создания записи расписания.
    
    Используется при ручном добавлении операции или корректировке плана.
    """
    pass


class ScheduleUpdate(BaseModel):
    """
    Схема для частичного обновления записи расписания.
    
    Все поля опциональны — обновляются только указанные.
    """
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    operation_id: Optional[int] = Field(None, gt=0)
    order_id: Optional[int] = Field(None, gt=0)
    equipment_id: Optional[int] = Field(None, gt=0)
    employee_id: Optional[int] = Field(None, gt=0)
    name: Optional[str] = Field(None, max_length=100)
    
    @model_validator(mode='after')
    def validate_time_range(self) -> 'ScheduleUpdate':
        """Проверка: если оба времени указаны, end должен быть после start."""
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValueError('Время окончания должно быть позже времени начала')
        return self


class ScheduleGenerateRequest(BaseModel):
    """
    Запрос на формирование производственного расписания.
    ⚠️ Алгоритм генерации реализован как заглушка.
    """
    start_date: date = Field(..., description="Дата начала планирования")
    end_date: date = Field(..., description="Дата окончания планирования")
    order_ids: Optional[List[int]] = Field(None, description="ID заказов для планирования")
    prioritize_by: str = Field(
        default="due_date", 
        pattern="^(due_date|priority|created_at)$",
        description="Критерий приоритета"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2026-04-15",
                "end_date": "2026-04-21",
                "order_ids": [1, 2, 3],
                "prioritize_by": "due_date"
            }
        }
    )
    
    @model_validator(mode='after')
    def validate_date_range(self) -> 'ScheduleGenerateRequest':
        """Проверка: end_date должен быть не раньше start_date."""
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError('Дата окончания должна быть не раньше даты начала')
        return self


class ScheduleConflict(BaseModel):
    """
    Информация о конфликте ресурсов.
    
    ⚠️ Реализована как заглушка для демонстрации структуры данных.
    """
    conflict_type: str = Field(
        ..., 
        pattern="^(equipment|employee|ingredient|sequence)$",
        description="Тип конфликта"
    )
    description: str = Field(..., description="Описание конфликта")
    resource_id: Optional[int] = Field(None, description="ID ресурса")
    resource_name: str = Field(..., description="Название ресурса")
    time_slot: datetime = Field(..., description="Временной слот конфликта")
    affected_orders: List[int] = Field(default_factory=list, description="ID затронутых заказов")


class ScheduleGenerateResponse(BaseModel):
    """
    Ответ на запрос генерации расписания.
    
    ⚠️ Алгоритм реализован как заглушка — возвращает mock-данные.
    """
    success: bool = Field(..., description="Успешно ли сформировано расписание")
    schedule_id: Optional[int] = Field(None, description="ID сформированного плана")
    orders_planned: int = Field(default=0, description="Количество запланированных заказов")
    orders_failed: int = Field(default=0, description="Количество неудачных заказов")
    conflicts: List[ScheduleConflict] = Field(default_factory=list, description="Список конфликтов")
    generated_at: datetime = Field(default_factory=datetime.now, description="Время генерации")


class ScheduleWithDetails(ScheduleRead):
    """
    Расширенная схема для отображения расписания с деталями.
    
    Используется в GET /schedule/{id} для удобного отображения.
    """
    operation_name: str = Field(..., description="Название технологической операции")
    recipe_name: str = Field(..., description="Название изделия (рецептуры)")
    order_due_date: Optional[date] = Field(None, description="Срок выполнения заказа")
    employee_name: Optional[str] = Field(None, description="ФИО сотрудника")
    equipment_name: Optional[str] = Field(None, description="Название оборудования")
    
    model_config = ConfigDict(from_attributes=True)