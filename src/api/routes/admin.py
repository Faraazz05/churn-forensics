"""
api/routes/admin.py
===================
GET /logs    — recent system logs
GET /uploads — recent uploads list
Admin-only endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.config    import get_settings
from core.database  import get_db
from core.security  import require_admin
from db             import crud

router   = APIRouter()
settings = get_settings()


@router.get("/logs", tags=["Admin"])
async def get_logs(
    lines: int = Query(100, ge=1, le=5000),
    _=Depends(require_admin),
):
    """Return last N lines from the API log file."""
    log_file = settings.LOG_FILE
    if not log_file.exists():
        return {"lines": [], "message": "Log file not found."}
    try:
        all_lines = log_file.read_text(encoding="utf-8").splitlines()
        return {"n_lines": len(all_lines), "lines": all_lines[-lines:]}
    except Exception as e:
        return {"error": str(e)}


@router.get("/uploads", tags=["Admin"])
async def list_uploads(
    limit:  int = Query(50, ge=1, le=500),
    db:     AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """List recent file uploads with status."""
    uploads = await crud.list_uploads(db, limit=limit)
    return {
        "n_uploads": len(uploads),
        "uploads": [
            {
                "upload_id":    u.id,
                "filename":     u.original_name,
                "rows":         u.rows_ingested,
                "churn_rate":   u.churn_rate,
                "status":       u.status,
                "created_at":   u.created_at.isoformat() if u.created_at else None,
            }
            for u in uploads
        ],
    }
