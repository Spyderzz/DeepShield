from fastapi import APIRouter

from api.v1 import analyze, auth, health, history, report

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(analyze.router)
api_router.include_router(analyze.jobs_router)  # Phase 19.3
api_router.include_router(report.router)
api_router.include_router(auth.router)
api_router.include_router(history.router)
