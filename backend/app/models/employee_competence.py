from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base

class EmployeeCompetence(Base):
    __tablename__ = "employee_competences"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    competence_id = Column(Integer, ForeignKey("competences.id"), nullable=False)
    
    # Связи
    employee = relationship("Employee", back_populates="competences")
    competence = relationship("Competence", back_populates="employee_competences")
    
    # Уникальность пары сотрудник-компетенция
    __table_args__ = (UniqueConstraint('employee_id', 'competence_id'),)