"""
api/routes/health.py
====================
GET /health — system status check.
"""
import time
from fastapi import APIRouter, Depends
from schemas.response_models import HealthResponse
from core.config import get_settings
from core.security import require_api_key
from core.database import engine
from services.prediction_service import is_model_loaded

router   = APIRouter()
settings = get_settings()
_START   = time.time()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(_=Depends(require_api_key)):
    """System liveness + readiness check."""
    db_ok = False
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return HealthResponse(
        status       = "ok" if db_ok else "degraded",
        db_connected = db_ok,
        model_loaded = is_model_loaded(),
        version      = settings.APP_VERSION,
        uptime_s     = round(time.time() - _START, 1),
    )
