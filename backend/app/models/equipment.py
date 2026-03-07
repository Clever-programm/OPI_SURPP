from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    quantity = Column(Integer, nullable=False, default=1)
    
    # Связи
    # operations = relationship("Operation", back_populates="equipment")
    # schedule_entries = relationship("Schedule", back_populates="equipment")