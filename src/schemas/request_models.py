"""
schemas/request_models.py
=========================
Pydantic request schemas for all API endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class CustomerFeatures(BaseModel):
    """Raw customer feature payload for single prediction."""
    customer_id:              str
    age:                      Optional[int]   = None
    region:                   Optional[str]   = None
    plan_type:                Optional[str]   = None
    contract_type:            Optional[str]   = None
    payment_method:           Optional[str]   = None
    tenure_months:            Optional[int]   = None
    logins_per_week:          Optional[float] = None
    features_used_count:      Optional[int]   = None
    avg_session_duration_min: Optional[float] = None
    monthly_active_days:      Optional[int]   = None
    last_login_days_ago:      Optional[int]   = None
    monthly_spend:            Optional[float] = None
    payment_failures_last_6m: Optional[int]   = None
    referrals_made:           Optional[int]   = None
    support_tickets_last_90d: Optional[int]   = None
    nps_score:                Optional[float] = None

    model_config = {"extra": "allow"}  # allow additional raw features


class BatchPredictRequest(BaseModel):
    customers: List[CustomerFeatures] = Field(..., min_length=1, max_length=10_000)


class ExplainRequest(BaseModel):
    customer_id: str
    top_k:       int = Field(default=10, ge=1, le=20)


class PipelineRunRequest(BaseModel):
    upload_id:       Optional[str] = None
    phases:          List[str]     = Field(
        default=["phase1","phase2","phase3","phase4","phase5"],
        description="Phases to run",
    )
    current_month:   Optional[int] = None
    previous_month:  Optional[int] = None
    sample_size:     Optional[int] = Field(default=None, ge=1000)


class SegmentQueryRequest(BaseModel):
    dimension:     Optional[str]  = None
    health_status: Optional[str]  = None
    limit:         int            = Field(default=100, ge=1, le=1000)


class QARequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
