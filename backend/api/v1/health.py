from fastapi import APIRouter, Response, status
from loguru import logger
from sqlalchemy import text

from db.database import engine

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
