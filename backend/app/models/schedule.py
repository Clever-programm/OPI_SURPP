from typing import Optional
from datetime import datetime, date

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
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    
    # Связи
    equipment = relationship("Equipment", back_populates="schedule_entries")
    operation = relationship("Operation", back_populates="schedule_entries")
    order = relationship("Order", back_populates="schedule_entries")
    employee = relationship("Employee", back_populates="schedule_entries")

    @property
    def operation_name(self) -> str:
        return self.operation.name if self.operation else "Неизвестная операция"

    @property
    def recipe_name(self) -> str:
        if self.operation and self.operation.recipe:
            return self.operation.recipe.name
        return "Неизвестное изделие"

    @property
    def order_due_date(self) -> Optional[date]:
        return self.order.due_date if self.order else None

    @property
    def employee_name(self) -> Optional[str]:
        return self.employee.name if self.employee else None

    @property
    def equipment_name(self) -> Optional[str]:
        return self.equipment.name if self.equipment else None