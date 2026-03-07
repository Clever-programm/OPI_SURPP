from datetime import datetime

from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    due_date = Column(Date, nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="new")
    created_at = Column(DateTime, default=datetime.now(datetime.timezone.utc))
    
    # Связи
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    schedule_entries = relationship("Schedule", back_populates="order")