"""
api/routes/upload.py
====================
POST /upload — ingest CSV/Excel and trigger background pipeline.
"""
import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config    import get_settings
from core.database  import get_db
from core.security  import require_admin
from db             import crud
from schemas.response_models import UploadResponse
from services       import upload_service as svc
from utils.file_handler       import validate_and_save, read_dataframe
from utils.background_tasks   import run_full_pipeline_task
from utils.logger   import log

router   = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=UploadResponse, tags=["Upload"])
async def upload_file(
    background_tasks: BackgroundTasks,
    file:    UploadFile = File(...),
    db:      AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Upload CSV or Excel customer data.
    Triggers full pipeline (Phases 1–5) as a background task.
    """
    saved_path, original_name = await validate_and_save(file)

    df      = read_dataframe(saved_path)
    summary = svc.ingest_dataframe(df, upload_id="pending")

    upload = await crud.create_upload(
        db,
        filename      = saved_path.name,
        original_name = original_name,
        file_size_mb  = saved_path.stat().st_size / 1e6,
        rows_ingested = summary["rows_ingested"],
        churn_rate    = summary.get("churn_rate"),
        status        = "processing",
    )

    # Create pipeline run record
    from services.pipeline_service import create_and_queue_pipeline
    run_id = await create_and_queue_pipeline(
        db, upload.id,
        phases=["phase1","phase2","phase3","phase4","phase5"],
        current_month=None, previous_month=None, sample_size=None,
    )

    background_tasks.add_task(
        run_full_pipeline_task,
        pipeline_run_id = run_id,
        upload_id       = upload.id,
        data_path       = saved_path,
        phases          = ["phase1","phase2","phase3","phase4","phase5"],
    )

    log.info(f"[upload] Job queued: run_id={run_id}")
    return UploadResponse(
        upload_id     = upload.id,
        filename      = original_name,
        rows_ingested = summary["rows_ingested"],
        churn_rate    = summary.get("churn_rate"),
        status        = "processing",
        job_id        = run_id,
    )
