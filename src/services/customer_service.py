"""
services/customer_service.py
==============================
Customer profile assembly — joins prediction + XAI + segment + insight.
"""
from typing import Optional

from services.prediction_service import predict_single
from services.xai_service        import get_customer_explanation, explain_on_demand
from services.segmentation_service import load_segment_results
from utils.logger import log


def get_full_profile(customer_id: str, raw_features: dict) -> dict:
    """Build a complete customer intelligence profile."""
    profile = {"customer_id": customer_id, "raw_features": raw_features}

    # Prediction
    pred = predict_single(raw_features)
    profile["prediction"] = pred

    # XAI — try saved first, then on-demand
    exp = get_customer_explanation(customer_id)
    if exp is None:
        exp = explain_on_demand(raw_features, pred["churn_probability"])
    profile["explanation"] = exp

    # Segment membership
    plan    = raw_features.get("plan_type", "")
    region  = raw_features.get("region", "")
    segs    = load_segment_results()
    matched = [s for s in segs if
               (plan and s.get("value") == plan) or
               (region and s.get("value") == region)]
    profile["segments"] = matched[:3]

    return profile


def get_at_risk_list(churn_probs: list[dict], threshold: float = 0.50) -> list[dict]:
    """Filter and sort customers by risk."""
    at_risk = [c for c in churn_probs if c.get("churn_probability", 0) >= threshold]
    return sorted(at_risk, key=lambda x: -x["churn_probability"])
