from fastapi import APIRouter
from app.api.v1.endpoints import (
    ingredient,
    equipment,
    competence,
    recipe,
    order,
    employee,
    stock,
    schedule
)

api_router = APIRouter()

api_router.include_router(ingredient.router)
api_router.include_router(equipment.router)
api_router.include_router(competence.router)
api_router.include_router(recipe.router)
api_router.include_router(order.router)
api_router.include_router(employee.router)
api_router.include_router(stock.router)
api_router.include_router(schedule.router)