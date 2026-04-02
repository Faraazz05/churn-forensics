"""
db/crud.py
==========
All database read/write operations (no business logic here).
Called exclusively by service layer.
"""

from datetime import datetime, timezone
from typing import Any, Optional, Sequence
from uuid import uuid4

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Customer, DriftLog, Explanation, InsightReport,
    ModelMetadata, Prediction, PipelineRun,
    SegmentResult, Upload,
)


def _uuid() -> str:
    return str(uuid4())


# ── Uploads ───────────────────────────────────────────────────
async def create_upload(db: AsyncSession, **kwargs) -> Upload:
    obj = Upload(id=_uuid(), **kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_upload(db: AsyncSession, upload_id: str) -> Optional[Upload]:
    return await db.get(Upload, upload_id)


async def update_upload(db: AsyncSession, upload_id: str, **kwargs) -> Optional[Upload]:
    await db.execute(update(Upload).where(Upload.id == upload_id).values(**kwargs))
    await db.commit()
    return await db.get(Upload, upload_id)


async def list_uploads(db: AsyncSession, limit: int = 50) -> Sequence[Upload]:
    r = await db.execute(select(Upload).order_by(desc(Upload.created_at)).limit(limit))
    return r.scalars().all()


# ── Customers ─────────────────────────────────────────────────
async def upsert_customer(db: AsyncSession, customer_id: str, **kwargs) -> Customer:
    obj = await db.get(Customer, customer_id)
    if obj is None:
        obj = Customer(customer_id=customer_id, **kwargs)
        db.add(obj)
    else:
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_customer(db: AsyncSession, customer_id: str) -> Optional[Customer]:
    return await db.get(Customer, customer_id)


async def list_customers(db: AsyncSession, limit: int = 100,
                          offset: int = 0) -> Sequence[Customer]:
    r = await db.execute(select(Customer).offset(offset).limit(limit))
    return r.scalars().all()


# ── Predictions ───────────────────────────────────────────────
async def create_prediction(db: AsyncSession, **kwargs) -> Prediction:
    obj = Prediction(id=_uuid(), **kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_latest_prediction(db: AsyncSession, customer_id: str) -> Optional[Prediction]:
    r = await db.execute(
        select(Prediction)
        .where(Prediction.customer_id == customer_id)
        .order_by(desc(Prediction.created_at))
        .limit(1)
    )
    return r.scalar_one_or_none()


async def get_predictions_by_tier(db: AsyncSession, risk_tier: str,
                                   limit: int = 200) -> Sequence[Prediction]:
    r = await db.execute(
        select(Prediction)
        .where(Prediction.risk_tier == risk_tier)
        .order_by(desc(Prediction.churn_probability))
        .limit(limit)
    )
    return r.scalars().all()


async def get_watchlist(db: AsyncSession, threshold: float = 0.70,
                         limit: int = 200) -> Sequence[Prediction]:
    r = await db.execute(
        select(Prediction)
        .where(Prediction.churn_probability >= threshold)
        .order_by(desc(Prediction.churn_probability))
        .limit(limit)
    )
    return r.scalars().all()


async def get_risk_distribution(db: AsyncSession) -> dict[str, int]:
    r = await db.execute(
        select(Prediction.risk_tier, func.count(Prediction.id))
        .group_by(Prediction.risk_tier)
    )
    return {row[0]: row[1] for row in r.all()}


# ── Explanations ──────────────────────────────────────────────
async def create_explanation(db: AsyncSession, **kwargs) -> Explanation:
    obj = Explanation(id=_uuid(), **kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_explanation_by_prediction(db: AsyncSession,
                                         prediction_id: str) -> Optional[Explanation]:
    r = await db.execute(
        select(Explanation).where(Explanation.prediction_id == prediction_id)
    )
    return r.scalar_one_or_none()


# ── Segment results ────────────────────────────────────────────
async def bulk_insert_segments(db: AsyncSession, run_id: str,
                                segments: list[dict]) -> int:
    objs = [SegmentResult(id=_uuid(), run_id=run_id, **{
        k: v for k, v in s.items()
        if k in SegmentResult.__table__.columns.keys()
    }) for s in segments]
    db.add_all(objs)
    await db.commit()
    return len(objs)


async def get_segments(db: AsyncSession, run_id: Optional[str] = None,
                        health_status: Optional[str] = None,
                        limit: int = 200) -> Sequence[SegmentResult]:
    q = select(SegmentResult)
    if run_id:        q = q.where(SegmentResult.run_id == run_id)
    if health_status: q = q.where(SegmentResult.health_status == health_status)
    q = q.order_by(desc(SegmentResult.churn_rate)).limit(limit)
    r = await db.execute(q)
    return r.scalars().all()


async def get_segment_by_id(db: AsyncSession, segment_id: str) -> Optional[SegmentResult]:
    r = await db.execute(
        select(SegmentResult)
        .where(SegmentResult.segment_id == segment_id)
        .order_by(desc(SegmentResult.created_at))
        .limit(1)
    )
    return r.scalar_one_or_none()


async def get_latest_run_id(db: AsyncSession) -> Optional[str]:
    r = await db.execute(
        select(SegmentResult.run_id)
        .order_by(desc(SegmentResult.created_at))
        .limit(1)
    )
    row = r.scalar_one_or_none()
    return row


# ── Drift logs ─────────────────────────────────────────────────
async def bulk_insert_drift(db: AsyncSession, run_id: str,
                              drift_features: list[dict]) -> int:
    objs = [DriftLog(id=_uuid(), run_id=run_id, **{
        k: v for k, v in d.items()
        if k in DriftLog.__table__.columns.keys()
    }) for d in drift_features]
    db.add_all(objs)
    await db.commit()
    return len(objs)


async def get_drift_features(db: AsyncSession, run_id: Optional[str] = None,
                              early_warning_only: bool = False,
                              limit: int = 100) -> Sequence[DriftLog]:
    q = select(DriftLog)
    if run_id:           q = q.where(DriftLog.run_id == run_id)
    if early_warning_only: q = q.where(DriftLog.early_warning == True)
    q = q.order_by(desc(DriftLog.psi)).limit(limit)
    r = await db.execute(q)
    return r.scalars().all()


# ── Insights ───────────────────────────────────────────────────
async def save_insight_report(db: AsyncSession, run_id: str,
                               report: dict) -> InsightReport:
    obj = InsightReport(
        id                  = _uuid(),
        run_id              = run_id,
        executive_summary   = report.get("executive_summary"),
        customer_risk       = report.get("customer_risk"),
        segments            = report.get("segments"),
        drift_analysis      = report.get("drift_analysis"),
        causal_analysis     = report.get("causal_analysis"),
        prediction_outlook  = report.get("prediction_outlook"),
        recommendations     = report.get("recommendations"),
        business_impact     = report.get("business_impact"),
        llm_mode            = report.get("llm_mode"),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_latest_insight(db: AsyncSession) -> Optional[InsightReport]:
    r = await db.execute(
        select(InsightReport).order_by(desc(InsightReport.created_at)).limit(1)
    )
    return r.scalar_one_or_none()


# ── Model metadata ─────────────────────────────────────────────
async def save_model_metadata(db: AsyncSession, **kwargs) -> ModelMetadata:
    # Deactivate previous active model
    await db.execute(
        update(ModelMetadata).where(ModelMetadata.is_active == True)
                              .values(is_active=False)
    )
    obj = ModelMetadata(id=_uuid(), is_active=True, **kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_active_model(db: AsyncSession) -> Optional[ModelMetadata]:
    r = await db.execute(
        select(ModelMetadata).where(ModelMetadata.is_active == True).limit(1)
    )
    return r.scalar_one_or_none()


async def list_models(db: AsyncSession, limit: int = 20) -> Sequence[ModelMetadata]:
    r = await db.execute(
        select(ModelMetadata).order_by(desc(ModelMetadata.trained_at)).limit(limit)
    )
    return r.scalars().all()


# ── Pipeline runs ──────────────────────────────────────────────
async def create_pipeline_run(db: AsyncSession, **kwargs) -> PipelineRun:
    obj = PipelineRun(id=_uuid(), **kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def update_pipeline_run(db: AsyncSession, run_id: str, **kwargs) -> Optional[PipelineRun]:
    await db.execute(update(PipelineRun).where(PipelineRun.id == run_id).values(**kwargs))
    await db.commit()
    return await db.get(PipelineRun, run_id)


async def get_pipeline_run(db: AsyncSession, run_id: str) -> Optional[PipelineRun]:
    return await db.get(PipelineRun, run_id)


async def list_pipeline_runs(db: AsyncSession, limit: int = 20) -> Sequence[PipelineRun]:
    r = await db.execute(
        select(PipelineRun).order_by(desc(PipelineRun.created_at)).limit(limit)
    )
    return r.scalars().all()
