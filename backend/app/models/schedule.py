from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class Schedule(Base):
    __tablename__ = "schedule"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    operation_id = Column(Integer, ForeignKey("operations.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    
    # Связи
    equipment = relationship("Equipment", back_populates="schedule_entries")
    operation = relationship("Operation", back_populates="schedule_entries")
    order = relationship("Order", back_populates="schedule_entries")
    employee = relationship("Employee", back_populates="schedule_entries")