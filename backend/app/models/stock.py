from datetime import datetime

from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class Stock(Base):
    __tablename__ = "stock"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=0)
    expiration_date = Column(Date, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    ingredient = relationship("Ingredient", back_populates="stock_items")