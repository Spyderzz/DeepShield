from fastapi import APIRouter

from api.v1 import analyze, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(analyze.router)
