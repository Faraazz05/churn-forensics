"""
api/routes/pipeline.py
======================
POST /pipeline/run    — manually trigger full pipeline
GET  /pipeline/status/{run_id}
GET  /pipeline/history
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database  import get_db
from core.security  import require_admin, require_api_key
from schemas.request_models  import PipelineRunRequest
from schemas.response_models import PipelineStatusResponse
from services.pipeline_service import create_and_queue_pipeline, get_run_status
from utils.background_tasks   import run_full_pipeline_task
from db             import crud

router = APIRouter()


@router.post("/pipeline/run", tags=["Pipeline"])
async def trigger_pipeline(
    payload:          PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db:               AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """Manually trigger full pipeline execution (background)."""
    run_id = await create_and_queue_pipeline(
        db,
        upload_id      = payload.upload_id,
        phases         = payload.phases,
        current_month  = payload.current_month,
        previous_month = payload.previous_month,
        sample_size    = payload.sample_size,
    )

    background_tasks.add_task(
        run_full_pipeline_task,
        pipeline_run_id = run_id,
        upload_id       = payload.upload_id,
        data_path       = None,
        phases          = payload.phases,
        current_month   = payload.current_month,
        previous_month  = payload.previous_month,
        sample_size     = payload.sample_size,
    )

    return {"status": "queued", "run_id": run_id,
            "message": f"Pipeline queued. Poll GET /pipeline/status/{run_id}"}


@router.get("/pipeline/status/{run_id}", response_model=PipelineStatusResponse,
            tags=["Pipeline"])
async def get_pipeline_status(
    run_id: str,
    db:     AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """Check pipeline run status."""
    result = await get_run_status(db, run_id)
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f"Pipeline run '{run_id}' not found.")
    return PipelineStatusResponse(**result)


@router.get("/pipeline/history", tags=["Pipeline"])
async def pipeline_history(
    limit:  int = 20,
    db:     AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """List recent pipeline runs."""
    runs = await crud.list_pipeline_runs(db, limit=limit)
    return {
        "n_runs": len(runs),
        "runs": [
            {
                "run_id":   r.id,
                "status":   r.status,
                "phases":   r.phases_run,
                "runtime":  r.runtime_seconds,
                "started":  r.started_at.isoformat() if r.started_at else None,
            }
            for r in runs
        ],
    }
