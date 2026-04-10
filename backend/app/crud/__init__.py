from .base import CRUDBase
from .ingredient import crud_ingredient
from .equipment import crud_equipment
from .competence import crud_competence
from .recipe import crud_recipe
from .order import crud_order
from .stock import crud_stock
from .employee import crud_employee

__all__ = [
    "CRUDBase",
    "crud_ingredient",
    "crud_equipment",
    "crud_competence",
    "crud_recipe",
    "crud_order",
    "crud_stock",
    "crud_employee",
]