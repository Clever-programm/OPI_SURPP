from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base

class Competence(Base):
    __tablename__ = "competences"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    
    # Связи
    employee_competences = relationship("EmployeeCompetence", back_populates="competence")
    # operations = relationship("Operation", back_populates="competence")