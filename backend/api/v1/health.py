from fastapi import APIRouter, Response, status
from loguru import logger
from sqlalchemy import text

from config import settings
from db.database import engine
from services.llm_explainer import is_rate_limited

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Legacy combined healthcheck — kept for backwards compatibility."""
    return {"status": "ok", "service": "deepshield-backend"}


@router.get("/health/live")
def health_live():
    """Liveness probe — returns 200 as long as the process is up."""
    return {"status": "alive"}


@router.get("/health/ready")
def health_ready(response: Response):
    """Readiness probe — 200 only when DB is reachable and models are loaded.

    Phase 19.5: the frontend disables the Analyze button while this returns 503.
    """
    checks: dict[str, bool] = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["db"] = True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"readiness db check failed: {e}")
        checks["db"] = False

    try:
        from models.model_loader import get_model_loader
        checks["models"] = bool(get_model_loader().is_ready())
    except AttributeError:
        # No is_ready() — fall back to "ready if loader constructs"
        try:
            from models.model_loader import get_model_loader
            get_model_loader()
            checks["models"] = True
        except Exception:  # noqa: BLE001
            checks["models"] = False
    except Exception as e:  # noqa: BLE001
        logger.warning(f"readiness model check failed: {e}")
        checks["models"] = False

    ok = all(checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ok else "not_ready", "checks": checks}


@router.get("/health/llm")
def health_llm(response: Response):
    """LLM availability probe — lets the frontend decide whether to request/show
    the AI summary card. Doesn't spend tokens; only checks config + breaker state.
    """
    has_primary = bool(settings.LLM_API_KEY)
    has_fallback = bool(settings.GROQ_API_KEY)
    cooldown = is_rate_limited()

    # Available if (any provider configured) AND (not rate-limited OR fallback exists)
    available = (has_primary or has_fallback) and (not cooldown or has_fallback)
    if not available:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "available": available,
        "primary": f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}" if has_primary else None,
        "fallback": f"groq/{settings.GROQ_MODEL}" if has_fallback else None,
        "rate_limited": cooldown,
    }
