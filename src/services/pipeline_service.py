"""
services/pipeline_service.py
==============================
Pipeline orchestration service — creates runs and delegates to background task.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from db import crud
from utils.logger import log


async def create_and_queue_pipeline(
    db:             AsyncSession,
    upload_id:      Optional[str],
    phases:         list[str],
    current_month:  Optional[int],
    previous_month: Optional[int],
    sample_size:    Optional[int],
) -> str:
    """Create pipeline run record and return run_id."""
    run = await crud.create_pipeline_run(
        db,
        upload_id = upload_id,
        status    = "queued",
        phases_run = phases,
    )
    log.info(f"[PipelineService] Pipeline run created: {run.id}")
    return run.id


async def get_run_status(db: AsyncSession, run_id: str) -> Optional[dict]:
    run = await crud.get_pipeline_run(db, run_id)
    if not run:
        return None
    return {
        "run_id":          run.id,
        "status":          run.status,
        "phases_run":      run.phases_run,
        "n_customers":     run.n_customers,
        "runtime_seconds": run.runtime_seconds,
        "error_msg":       run.error_msg,
        "started_at":      run.started_at,
        "completed_at":    run.completed_at,
    }
