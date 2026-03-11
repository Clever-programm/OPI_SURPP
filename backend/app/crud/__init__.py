from .base import CRUDBase
from .ingredient import crud_ingredient
from .equipment import crud_equipment
from .competence import crud_competence

__all__ = [
    "CRUDBase",
    "crud_ingredient",
    "crud_equipment",
    "crud_competence",
]