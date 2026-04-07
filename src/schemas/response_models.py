"""
schemas/response_models.py
==========================
Pydantic response schemas — defines the exact JSON shape of every endpoint.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error:   str
    detail:  Optional[str] = None
    code:    int


class HealthResponse(BaseModel):
    status:       str
    db_connected: bool
    model_loaded: bool
    version:      str
    uptime_s:     float


# ── Prediction ────────────────────────────────────────────────
class PredictionOut(BaseModel):
    customer_id:       str
    churn_probability: float
    risk_tier:         str   # Critical / High / Medium / Safe
    model_name:        Optional[str] = None
    predicted_at:      Optional[datetime] = None


class BatchPredictionOut(BaseModel):
    predictions:   List[PredictionOut]
    n_customers:   int
    churn_rate:    float
    risk_summary:  Dict[str, int]


# ── XAI ──────────────────────────────────────────────────────
class FeatureExplanation(BaseModel):
    feature:    str
    importance: float
    direction:  str   # risk+ / risk-
    confidence: str   # HIGH / MEDIUM / LOW


class ExplanationOut(BaseModel):
    customer_id:        str
    churn_probability:  float
    primary_method:     str
    validators_active:  int
    high_conf_features: List[str]
    explanations:       List[FeatureExplanation]
    reasoning:          Optional[Dict[str, Any]] = None


# ── Segments ──────────────────────────────────────────────────
class SegmentOut(BaseModel):
    segment_id:          str
    dimension:           str
    value:               str
    segment_size:        Optional[int] = None
    churn_rate:          Optional[float]
    previous_churn_rate: Optional[float]
    churn_delta:         Optional[float]
    health_status:       Optional[str]
    risk_level:          Optional[str]
    revenue_at_risk:     Optional[float]
    acceleration:        Optional[str]
    exceeds_benchmark:   Optional[bool]


class SegmentsResponse(BaseModel):
    run_id:            Optional[str]
    n_segments:        int
    segments:          List[SegmentOut]
    global_insights:   Optional[Dict[str, Any]]


# ── Drift ─────────────────────────────────────────────────────
class DriftFeatureOut(BaseModel):
    feature:        str
    psi:            Optional[float]
    psi_status:     Optional[str]
    ks_statistic:   Optional[float]
    p_value:        Optional[float]
    drift_severity: Optional[str]
    trend:          Optional[str]
    velocity:       Optional[str]
    early_warning:  bool = False
    xai_confirmed:  bool = False


class DriftResponse(BaseModel):
    overall_severity:    str
    n_features_tracked:  int
    drifted_features:    List[str]
    early_warnings:      List[DriftFeatureOut]
    retraining_trigger:  Dict[str, Any]
    drift_features:      List[DriftFeatureOut]


# ── Insights ──────────────────────────────────────────────────
class InsightResponse(BaseModel):
    executive_summary:   str
    customer_risk:       Dict[str, Any]
    segments:            Dict[str, Any]
    drift_analysis:      Dict[str, Any]
    causal_analysis:     Dict[str, Any]
    prediction_outlook:  Dict[str, Any]
    recommendations:     List[Dict[str, Any]]
    business_impact:     Dict[str, Any]
    generated_at:        Optional[datetime] = None
    llm_mode:            Optional[str] = None


# ── Models / Leaderboard ──────────────────────────────────────
class ModelOut(BaseModel):
    model_name:       str
    val_auc:          Optional[float]
    val_f1:           Optional[float]
    test_auc:         Optional[float]
    test_f1:          Optional[float]
    n_features:       Optional[int]
    xai_method:       Optional[str]
    is_active:        bool
    trained_at:       Optional[datetime]


class LeaderboardResponse(BaseModel):
    best_model:    Optional[ModelOut]
    all_models:    List[ModelOut]
    n_models:      int


# ── Customers ─────────────────────────────────────────────────
class CustomerRiskOut(BaseModel):
    customer_id:       str
    churn_probability: float
    risk_tier:         str
    plan_type:         Optional[str]
    region:            Optional[str]
    contract_type:     Optional[str]
    primary_driver:    Optional[str]
    top_action:        Optional[str]


class CustomerProfileOut(BaseModel):
    customer_id:  str
    profile:      Dict[str, Any]
    prediction:   Optional[PredictionOut]
    explanation:  Optional[ExplanationOut]
    segment:      Optional[SegmentOut]
    insights:     Optional[Dict[str, Any]]


class WatchlistResponse(BaseModel):
    threshold:   float
    n_customers: int
    customers:   List[Dict[str, Any]]


# ── Upload ────────────────────────────────────────────────────
class UploadResponse(BaseModel):
    upload_id:    str
    filename:     str
    rows_ingested: Optional[int]
    churn_rate:   Optional[float]
    status:       str
    job_id:       Optional[str]


# ── Pipeline ──────────────────────────────────────────────────
class PipelineStatusResponse(BaseModel):
    run_id:         str
    status:         str
    phases_run:     Optional[List[str]]
    n_customers:    Optional[int]
    runtime_seconds: Optional[float]
    error_msg:      Optional[str]
    started_at:     Optional[datetime]
    completed_at:   Optional[datetime]


# ── Q&A ──────────────────────────────────────────────────────
class QAResponse(BaseModel):
    question:     str
    answer:       str
    intent:       str
    source:       str  # llm / rules
    context_used: List[str]
