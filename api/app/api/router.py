from fastapi import APIRouter

from app.api.endpoints import departments, expenses

api_router = APIRouter()
api_router.include_router(expenses.router)
api_router.include_router(departments.router)
