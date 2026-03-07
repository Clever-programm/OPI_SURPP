from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    
    # Связи
    competences = relationship("EmployeeCompetence", back_populates="employee")
    # schedule_entries = relationship("Schedule", back_populates="employee")