from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date, datetime


class StockBase(BaseModel):
    """
    Базовая схема складского остатка.
    Соответствует модели Stock.
    """
    ingredient_id: int = Field(..., gt=0, description="ID ингредиента из справочника")
    quantity: float = Field(..., ge=0, description="Текущее количество на складе")
    expiration_date: Optional[date] = Field(None, description="Срок годности (опционально)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "quantity": 50.0,
                "expiration_date": "2025-06-01"
            }
        }
    )


class StockRead(StockBase):
    """Схема для ответа (чтение)."""
    id: int
    received_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StockReceive(BaseModel):
    """
    Схема для регистрации поступления сырья на склад.
    """
    ingredient_id: int = Field(..., gt=0, description="ID ингредиента")
    quantity: float = Field(..., gt=0, description="Количество поступающего сырья")
    expiration_date: date = Field(..., description="Срок годности партии")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "quantity": 100.0,
                "expiration_date": "2025-12-31"
            }
        }
    )


class StockWriteOff(BaseModel):
    """
    Схема для регистрации списания сырья со склада.
    """
    ingredient_id: int = Field(..., gt=0, description="ID ингредиента")
    quantity: float = Field(..., gt=0, description="Количество для списания")
    order_id: Optional[int] = Field(None, gt=0, description="ID заказа (если списание для производства)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "quantity": 25.0,
                "order_id": 42
            }
        }
    )


class StockCheckItem(BaseModel):
    """Элемент запроса проверки доступности."""
    ingredient_id: int = Field(..., gt=0, description="ID ингредиента")
    required_quantity: float = Field(..., gt=0, description="Требуемое количество")


class StockCheckRequest(BaseModel):
    """
    Запрос на проверку достаточности сырья для выполнения заказов.
    """
    items: List[StockCheckItem] = Field(..., min_length=1, description="Список ингредиентов для проверки")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {"ingredient_id": 1, "required_quantity": 50.0},
                    {"ingredient_id": 2, "required_quantity": 10.0}
                ]
            }
        }
    )


class StockCheckResult(BaseModel):
    """Результат проверки для одного ингредиента."""
    ingredient_id: int
    ingredient_name: str
    required: float = Field(..., description="Требуемое количество")
    available: float = Field(..., description="Доступное количество на складе")
    is_sufficient: bool = Field(..., description="Достаточно ли сырья")
    deficit: float = Field(default=0.0, ge=0, description="Дефицит (если есть)")
    expiry_warning: Optional[str] = Field(None, description="Предупреждение о сроке годности")


class StockCheckResponse(BaseModel):
    """
    Полный ответ проверки доступности сырья.
    """
    is_all_sufficient: bool = Field(..., description="Достаточно ли всех ингредиентов")
    results: List[StockCheckResult] = Field(..., description="Результаты по каждому ингредиенту")
    timestamp: datetime = Field(default_factory=datetime.now, description="Время проверки")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_all_sufficient": False,
                "results": [
                    {
                        "ingredient_id": 1,
                        "ingredient_name": "Мука пшеничная",
                        "required": 50.0,
                        "available": 30.0,
                        "is_sufficient": False,
                        "deficit": 20.0,
                        "expiry_warning": None
                    }
                ],
                "timestamp": "2026-04-10T12:00:00+00:00"
            }
        }
    )

class StockExpiring(BaseModel):
    """
    Информация об ингредиентах с истекающим сроком годности.
    
    Используется для FIFO-учёта и предотвращения порчи сырья.
    """
    ingredient_id: int
    ingredient_name: str
    quantity: float
    expiration_date: date
    days_until_expiry: int = Field(..., description="Дней до истечения срока")
    
    model_config = ConfigDict(from_attributes=True)


class StockExpiringResponse(BaseModel):
    """Ответ для эндпоинта /api/stock/expiring-soon."""
    expiring_soon: List[StockExpiring] = Field(..., description="Ингредиенты, истекающие в ближайшие дни")
    threshold_days: int = Field(..., description="Порог в днях для фильтрации")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "expiring_soon": [
                    {
                        "ingredient_id": 5,
                        "ingredient_name": "Сливки 33%",
                        "quantity": 5.0,
                        "expiration_date": "2026-04-15",
                        "days_until_expiry": 5,
                    }
                ],
                "threshold_days": 7
            }
        }
    )