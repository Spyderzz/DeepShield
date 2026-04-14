from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.router import api_router
from config import settings
from db.database import init_db
from models.model_loader import get_model_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeepShield backend")
    init_db()
    logger.info("Database initialized")
    if settings.PRELOAD_MODELS:
        get_model_loader().preload_phase1()
    else:
        logger.info("PRELOAD_MODELS=false — models will load on first use")
    yield
    logger.info("Shutting down DeepShield backend")


app = FastAPI(
    title="DeepShield API",
    description="Explainable AI-based multimodal misinformation detection",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {"service": "DeepShield", "docs": "/docs", "health": "/api/v1/health"}
