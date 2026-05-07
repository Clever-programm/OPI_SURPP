from pydantic import BaseModel, Field, ConfigDict


class RecipeIngredientBase(BaseModel):
    """
    Базовая схема для связи рецепта с ингредиентом.
    Соответствует модели RecipeIngredient (many-to-many через association object).
    """
    ingredient_id: int = Field(..., gt=0, description="ID ингредиента из справочника")
    quantity: float = Field(..., gt=0, description="Количество ингредиента в рецепте")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ingredient_id": 1,
                "quantity": 500.0,
            }
        }
    )


class RecipeIngredientCreate(RecipeIngredientBase):
    """Схема для добавления ингредиента в рецепт."""
    pass


class RecipeIngredientRead(RecipeIngredientBase):
    """Схема для ответа (чтение)."""
    id: int
    recipe_id: int
    
    model_config = ConfigDict(from_attributes=True)