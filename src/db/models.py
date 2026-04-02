"""
db/models.py
============
SQLAlchemy ORM table definitions for all Phase outputs.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text, Index,
)
from sqlalchemy.orm import relationship

from core.database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


# ── Uploads ───────────────────────────────────────────────────
class Upload(Base):
    __tablename__ = "uploads"

    id           = Column(String, primary_key=True, default=_uuid)
    filename     = Column(String, nullable=False)
    original_name = Column(String)
    file_size_mb = Column(Float)
    rows_ingested = Column(Integer)
    churn_rate   = Column(Float)
    status       = Column(String, default="pending")  # pending/processing/done/failed
    error_msg    = Column(Text)
    created_at   = Column(DateTime(timezone=True), default=_now)
    completed_at = Column(DateTime(timezone=True))

    predictions  = relationship("Prediction", back_populates="upload", cascade="all,delete")


# ── Customers ─────────────────────────────────────────────────
class Customer(Base):
    __tablename__ = "customers"

    customer_id      = Column(String, primary_key=True)
    age              = Column(Integer)
    region           = Column(String)
    plan_type        = Column(String)
    contract_type    = Column(String)
    payment_method   = Column(String)
    tenure_months    = Column(Integer)
    monthly_spend    = Column(Float)
    raw_features     = Column(JSON)   # full raw feature dict
    created_at       = Column(DateTime(timezone=True), default=_now)
    updated_at       = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    predictions      = relationship("Prediction", back_populates="customer",
                                    cascade="all,delete")

    __table_args__ = (
        Index("ix_customer_region",   "region"),
        Index("ix_customer_plan",     "plan_type"),
        Index("ix_customer_contract", "contract_type"),
    )


# ── Predictions ───────────────────────────────────────────────
class Prediction(Base):
    __tablename__ = "predictions"

    id               = Column(String, primary_key=True, default=_uuid)
    customer_id      = Column(String, ForeignKey("customers.customer_id", ondelete="CASCADE"))
    upload_id        = Column(String, ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)
    churn_probability = Column(Float, nullable=False)
    risk_tier        = Column(String)   # Critical / High / Medium / Safe
    model_name       = Column(String)
    model_version    = Column(String)
    feature_snapshot = Column(JSON)    # features used at prediction time
    created_at       = Column(DateTime(timezone=True), default=_now)

    customer         = relationship("Customer", back_populates="predictions")
    upload           = relationship("Upload", back_populates="predictions")
    explanations     = relationship("Explanation", back_populates="prediction",
                                    cascade="all,delete")

    __table_args__ = (
        Index("ix_pred_customer",   "customer_id"),
        Index("ix_pred_risk_tier",  "risk_tier"),
        Index("ix_pred_created",    "created_at"),
    )


# ── Explanations (XAI) ────────────────────────────────────────
class Explanation(Base):
    __tablename__ = "explanations"

    id             = Column(String, primary_key=True, default=_uuid)
    prediction_id  = Column(String, ForeignKey("predictions.id", ondelete="CASCADE"))
    primary_method = Column(String)              # SHAP_TreeExplainer / logistic_coef / LIME
    top_features   = Column(JSON)                # [{feature, importance, direction, confidence}]
    high_conf_features = Column(JSON)
    validators_active  = Column(Integer, default=0)
    confidence_summary = Column(JSON)
    reasoning      = Column(JSON)                # WHAT/WHY from Phase 5 reasoning engine
    created_at     = Column(DateTime(timezone=True), default=_now)

    prediction     = relationship("Prediction", back_populates="explanations")

    __table_args__ = (Index("ix_expl_prediction", "prediction_id"),)


# ── Segment results ────────────────────────────────────────────
class SegmentResult(Base):
    __tablename__ = "segment_results"

    id                  = Column(String, primary_key=True, default=_uuid)
    run_id              = Column(String, index=True)
    segment_id          = Column(String, nullable=False, index=True)
    dimension           = Column(String)
    value               = Column(String)
    snapshot_month      = Column(Integer)
    segment_size        = Column(Integer)
    churn_rate          = Column(Float)
    previous_churn_rate = Column(Float)
    churn_delta         = Column(Float)
    revenue_at_risk     = Column(Float)
    health_status       = Column(String)    # improving / stable / degrading
    risk_level          = Column(String)
    acceleration        = Column(String)
    exceeds_benchmark   = Column(Boolean, default=False)
    created_at          = Column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_seg_health",  "health_status"),
        Index("ix_seg_churn",   "churn_rate"),
    )


# ── Drift logs ─────────────────────────────────────────────────
class DriftLog(Base):
    __tablename__ = "drift_logs"

    id              = Column(String, primary_key=True, default=_uuid)
    run_id          = Column(String, index=True)
    feature         = Column(String, nullable=False, index=True)
    psi             = Column(Float)
    psi_status      = Column(String)
    ks_statistic    = Column(Float)
    p_value         = Column(Float)
    drift_severity  = Column(String)
    trend           = Column(String)
    velocity        = Column(String)
    early_warning   = Column(Boolean, default=False, index=True)
    xai_confirmed   = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), default=_now)


# ── Insight reports ────────────────────────────────────────────
class InsightReport(Base):
    __tablename__ = "insights"

    id                = Column(String, primary_key=True, default=_uuid)
    run_id            = Column(String, index=True)
    executive_summary = Column(Text)
    customer_risk     = Column(JSON)
    segments          = Column(JSON)
    drift_analysis    = Column(JSON)
    causal_analysis   = Column(JSON)
    prediction_outlook = Column(JSON)
    recommendations   = Column(JSON)
    business_impact   = Column(JSON)
    llm_mode          = Column(String)
    created_at        = Column(DateTime(timezone=True), default=_now)


# ── Model metadata ─────────────────────────────────────────────
class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id              = Column(String, primary_key=True, default=_uuid)
    model_name      = Column(String, nullable=False)
    version         = Column(String)
    val_auc         = Column(Float)
    val_f1          = Column(Float)
    test_auc        = Column(Float)
    test_f1         = Column(Float)
    n_features      = Column(Integer)
    dataset_size    = Column(Integer)
    churn_rate_train = Column(Float)
    xai_method      = Column(String)
    selection_reason = Column(Text)
    is_active       = Column(Boolean, default=True)
    trained_at      = Column(DateTime(timezone=True), default=_now)


# ── Pipeline runs ──────────────────────────────────────────────
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id              = Column(String, primary_key=True, default=_uuid)
    upload_id       = Column(String, ForeignKey("uploads.id", ondelete="SET NULL"), nullable=True)
    status          = Column(String, default="queued")  # queued/running/done/failed
    phases_run      = Column(JSON)       # ["phase1","phase2",...]
    n_customers     = Column(Integer)
    overall_drift   = Column(String)
    retrain_flag    = Column(Boolean, default=False)
    runtime_seconds = Column(Float)
    error_msg       = Column(Text)
    started_at      = Column(DateTime(timezone=True))
    completed_at    = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), default=_now)
