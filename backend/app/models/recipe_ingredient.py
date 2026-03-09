from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    
    # Связи
    recipe = relationship("Recipe", back_populates="ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")
    
    __table_args__ = (UniqueConstraint('recipe_id', 'ingredient_id'),)