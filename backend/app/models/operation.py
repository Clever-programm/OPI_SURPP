from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

class Operation(Base):
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    competence_id = Column(Integer, ForeignKey("competences.id"), nullable=True)
    sequence_number = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    
    # Связи
    recipe = relationship("Recipe", back_populates="operations")
    equipment = relationship("Equipment", back_populates="operations")
    competence = relationship("Competence", back_populates="operations")
    schedule_entries = relationship("Schedule", back_populates="operation")