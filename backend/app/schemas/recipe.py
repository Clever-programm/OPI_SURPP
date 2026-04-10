from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.recipe_ingredient import RecipeIngredientCreate, RecipeIngredientRead
from app.schemas.operation import OperationCreate, OperationRead


class RecipeBase(BaseModel):
    """
    Базовая схема рецептуры.
    Соответствует модели Recipe.
    """
    name: str = Field(..., min_length=2, max_length=100, description="Название изделия")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Торт Прага",
            }
        }
    )


class RecipeCreate(RecipeBase):
    """
    Схема для создания рецептуры.
    Поддерживает вложенное создание ингредиентов и операций.
    """
    # Опциональные вложенные данные для создания "всё в одном запросе"
    ingredients: Optional[List[RecipeIngredientCreate]] = Field(None, description="Список ингредиентов рецепта")
    operations: Optional[List[OperationCreate]] = Field(None, description="Список технологических операций")

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients_unique(cls, v: Optional[List[RecipeIngredientCreate]]) -> Optional[List[RecipeIngredientCreate]]:
        """Проверка: один ингредиент не может быть добавлен дважды в рецепт."""
        if v:
            ids = [item.ingredient_id for item in v]
            if len(ids) != len(set(ids)):
                raise ValueError('Один и тот же ингредиент не может быть добавлен в рецепт несколько раз')
        return v

    @field_validator('operations')
    @classmethod
    def validate_operations_sequence(cls, v: Optional[List[OperationCreate]]) -> Optional[List[OperationCreate]]:
        """Проверка: sequence_order должен быть уникальным в рамках рецепта."""
        if v:
            orders = [op.sequence_order for op in v]
            if len(orders) != len(set(orders)):
                raise ValueError('Порядковые номера операций (sequence_order) должны быть уникальными')
        return v


class RecipeUpdate(BaseModel):
    """Схема для обновления рецептуры (частичное обновление)."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)


class RecipeRead(RecipeBase):
    """Схема для ответа (чтение) — базовая информация."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class RecipeWithDetails(RecipeRead):
    """
    Расширенная схема для ответа с вложенными данными.
    Используется в GET /recipes/{id} для отображения полного состава.
    """
    ingredients: List[RecipeIngredientRead] = Field(default_factory=list)
    operations: List[OperationRead] = Field(default_factory=list)
    
    # Вычисляемое поле: общая длительность рецепта
    @property
    def total_duration_minutes(self) -> int:
        return sum(op.duration_minutes for op in self.operations)