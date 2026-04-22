import asyncio
import secrets
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.router import api_router
from config import settings
from db.database import init_db
from models.model_loader import get_model_loader
from services.rate_limit import RateLimitContextMiddleware, limiter
from services.report_service import cleanup_expired


# === Phase 15.3 — JWT / CORS / logging hardening ===

_DEFAULT_JWT_SECRET = "change-me-in-production"


def _enforce_production_hardening() -> None:
    """Refuse to start in production with unsafe defaults (Phase 15.3)."""
    if settings.DEBUG:
        return
    if settings.JWT_SECRET_KEY == _DEFAULT_JWT_SECRET or not settings.JWT_SECRET_KEY:
        example = secrets.token_urlsafe(48)
        logger.error(
            "Refusing to start: JWT_SECRET_KEY is unset or default. "
            f"Set JWT_SECRET_KEY in your environment. Example: {example}"
        )
        sys.exit(1)
    if "*" in settings.CORS_ORIGINS:
        logger.error(
            "Refusing to start: CORS_ORIGINS contains '*' while allow_credentials=True. "
            "Set an explicit origin list."
        )
        sys.exit(1)


def _configure_logging() -> None:
    """Rotate + retain logs, scrub emails."""
    import re

    email_re = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")

    def _scrub(record):
        msg = record["message"]
        record["message"] = email_re.sub(r"***@\2", msg)
        return True

    logger.remove()
    logger.add(sys.stderr, filter=_scrub, level="INFO")
    logger.add(
        "logs/deepshield.log",
        rotation="10 MB",
        retention="7 days",
        filter=_scrub,
        level="INFO",
        enqueue=True,
    )


_configure_logging()
_enforce_production_hardening()


async def _report_cleanup_loop():
    while True:
        try:
            cleanup_expired()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Report cleanup error: {e}")
        await asyncio.sleep(600)  # every 10 min


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeepShield backend")
    init_db()
    logger.info("Database initialized")
    if settings.PRELOAD_MODELS:
        get_model_loader().preload_phase1()
    else:
        logger.info("PRELOAD_MODELS=false — models will load on first use")
    task = asyncio.create_task(_report_cleanup_loop())
    yield
    task.cancel()
    logger.info("Shutting down DeepShield backend")


app = FastAPI(
    title="DeepShield API",
    description="Explainable AI-based multimodal misinformation detection",
    version="0.1.0",
    lifespan=lifespan,
)

# Phase 15.2 — slowapi rate limiter
app.state.limiter = limiter


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RateLimitContextMiddleware)

# Phase 15.3 — explicit CORS methods/headers (no wildcards with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

app.include_router(api_router)

# Phase 19.2 — serve stored thumbnails / media under /media/*
import os as _os
_media_root = _os.environ.get("MEDIA_ROOT", "./media")
_os.makedirs(_os.path.join(_media_root, "thumbs"), exist_ok=True)
app.mount("/media", StaticFiles(directory=_media_root), name="media")


@app.get("/")
def root():
    return {"service": "DeepShield", "docs": "/docs", "health": "/api/v1/health"}
