"""
utils/background_tasks.py
=========================
Background task wrappers for non-blocking operations.
Called by route handlers via FastAPI's BackgroundTasks.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import AsyncSessionLocal
from db import crud
from utils.logger import log

settings = get_settings()


async def run_full_pipeline_task(
    pipeline_run_id: str,
    upload_id:       str | None,
    data_path:       Path | None,
    phases:          list[str],
    current_month:   int | None = None,
    previous_month:  int | None = None,
    sample_size:     int | None = None,
) -> None:
    """
    Background task: execute the full Phase 1–5 pipeline.
    Updates pipeline_run status in DB throughout.
    Calls existing phase modules — no business logic here.
    """
    import time
    t0 = time.time()

    async with AsyncSessionLocal() as db:
        await crud.update_pipeline_run(
            db, pipeline_run_id,
            status     = "running",
            started_at = datetime.now(timezone.utc),
            phases_run = phases,
        )

    log.info(f"[Pipeline] Run {pipeline_run_id} started | phases={phases}")

    try:
        import sys
        for src in [settings.PHASE1_SRC, settings.PHASE2_SRC,
                    settings.PHASE3_SRC, settings.PHASE4_SRC, settings.PHASE5_SRC]:
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))

        results = {}

        # ── Phase 1: data + model ─────────────────────────────
        if "phase1" in phases:
            log.info("[Pipeline] Running Phase 1...")
            try:
                from pipeline import run_phase1
                summary = await asyncio.to_thread(
                    run_phase1,
                    data_dir      = settings.DATA_DIR,
                    models_dir    = settings.MODELS_DIR,
                    output_dir    = settings.OUTPUTS_DIR,
                    skip_generate = data_path is not None,
                    sample_size   = sample_size,
                )
                results["phase1"] = summary
                log.info(f"[Pipeline] Phase 1 done: {summary.get('best_model_name')}")
            except ImportError:
                log.warning("[Pipeline] Phase 1 pipeline.py not found — skipping")

        # ── Phase 2: XAI ──────────────────────────────────────
        if "phase2" in phases:
            log.info("[Pipeline] Running Phase 2 XAI...")
            try:
                from xai_runner import run_xai
                xai_summary = await asyncio.to_thread(
                    run_xai,
                    data_dir    = settings.DATA_DIR,
                    models_dir  = settings.MODELS_DIR,
                    output_dir  = settings.OUTPUTS_DIR / "xai",
                    sample_size = sample_size,
                )
                results["phase2"] = xai_summary
                log.info("[Pipeline] Phase 2 done")
            except ImportError:
                log.warning("[Pipeline] Phase 2 xai_runner.py not found — skipping")

        # ── Phase 3: Segmentation ─────────────────────────────
        if "phase3" in phases:
            log.info("[Pipeline] Running Phase 3 Segmentation...")
            try:
                from run_segmentation import run_segmentation
                seg_summary = await asyncio.to_thread(
                    run_segmentation,
                    data_dir   = settings.DATA_DIR,
                    output_dir = settings.OUTPUTS_DIR,
                    sample_size= sample_size,
                )
                results["phase3"] = seg_summary
                log.info("[Pipeline] Phase 3 done")
            except ImportError:
                log.warning("[Pipeline] Phase 3 not found — skipping")

        # ── Phase 4: Drift ────────────────────────────────────
        if "phase4" in phases:
            log.info("[Pipeline] Running Phase 4 Drift...")
            try:
                from run_drift import run_drift
                drift_summary = await asyncio.to_thread(
                    run_drift,
                    data_dir      = settings.DATA_DIR,
                    output_dir    = settings.OUTPUTS_DIR,
                    current_month = current_month,
                    ref_month     = previous_month,
                    sample_size   = sample_size,
                )
                results["phase4"] = drift_summary
                log.info("[Pipeline] Phase 4 done")
            except ImportError:
                log.warning("[Pipeline] Phase 4 not found — skipping")

        # ── Phase 5: Insights ─────────────────────────────────
        if "phase5" in phases:
            log.info("[Pipeline] Running Phase 5 Insights...")
            try:
                from insight_runner import run_insights
                insight_summary = await asyncio.to_thread(
                    run_insights,
                    outputs_dir = settings.OUTPUTS_DIR,
                    models_dir  = settings.MODELS_DIR,
                    save_dir    = settings.OUTPUTS_DIR / "insights",
                )
                results["phase5"] = insight_summary
                log.info("[Pipeline] Phase 5 done")
            except ImportError:
                log.warning("[Pipeline] Phase 5 not found — skipping")

        elapsed = round(time.time() - t0, 1)

        async with AsyncSessionLocal() as db:
            await crud.update_pipeline_run(
                db, pipeline_run_id,
                status          = "done",
                runtime_seconds = elapsed,
                completed_at    = datetime.now(timezone.utc),
            )
            if upload_id:
                await crud.update_upload(
                    db, upload_id,
                    status       = "done",
                    completed_at = datetime.now(timezone.utc),
                )

        log.info(f"[Pipeline] Run {pipeline_run_id} completed in {elapsed}s")

    except Exception as e:
        log.error(f"[Pipeline] Run {pipeline_run_id} FAILED: {e}", exc_info=True)
        async with AsyncSessionLocal() as db:
            await crud.update_pipeline_run(
                db, pipeline_run_id,
                status    = "failed",
                error_msg = str(e)[:500],
            )
            if upload_id:
                await crud.update_upload(
                    db, upload_id,
                    status    = "failed",
                    error_msg = str(e)[:500],
                )
