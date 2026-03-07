from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class Recipe(Base):
    __tablename__ = "recipes"
    
    recipe_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    
    # Связи
    # ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    # operations = relationship("Operation", back_populates="recipe", cascade="all, delete-orphan", order_by="Operation.sequence_number")
    # order_items = relationship("OrderItem", back_populates="recipe")