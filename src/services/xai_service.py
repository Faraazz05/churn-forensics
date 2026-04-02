"""
services/xai_service.py
=======================
Calls Phase 2 XAI engine. Loads saved outputs or runs on-demand.
"""
import json, sys
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from core.config import get_settings
from services.prediction_service import _load_model, _feat_names, _setup_phase1_path
from utils.logger import log

settings = get_settings()


def _xai_outputs_dir() -> Path:
    return settings.OUTPUTS_DIR / "xai"


def load_global_explanation() -> dict:
    path = _xai_outputs_dir() / "global_explanation.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_watchlist_reasoning() -> list:
    path = _xai_outputs_dir() / "watchlist_reasoning.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_confidence_summary() -> dict:
    path = _xai_outputs_dir() / "confidence_summary.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def get_customer_explanation(customer_id: str) -> Optional[dict]:
    """Load saved explanation for a customer from watchlist outputs."""
    for filename in ["watchlist_explanations.json", "watchlist_reasoning.json"]:
        path = _xai_outputs_dir() / filename
        if path.exists():
            with open(path) as f:
                data = json.load(f)
            for item in (data if isinstance(data, list) else []):
                if item.get("customer_id") == customer_id:
                    return item
    return None


def explain_on_demand(features: dict, churn_prob: float) -> dict:
    """
    Run XAI on-demand for a single customer.
    Falls back to coefficient-based explanation if SHAP unavailable.
    """
    _setup_phase1_path()
    _setup_xai_path()

    try:
        from feature_engineering import build_feature_matrix
        from xai_engine import XAIEngine

        model = _load_model()
        df = pd.DataFrame([features])
        X, _ = build_feature_matrix(df, target=None)
        if _feat_names:
            X = X.reindex(columns=_feat_names, fill_value=0)

        engine = XAIEngine(model, X, pd.Series([0]*len(X)),
                           list(X.columns), verbose=False)
        return engine.explain_local(
            X_row       = X,
            customer_id = features.get("customer_id","unknown"),
            churn_prob  = churn_prob,
        )
    except Exception as e:
        log.warning(f"[XAIService] On-demand XAI failed ({e}), using fallback")
        return _coefficient_fallback(features, churn_prob)


def _coefficient_fallback(features: dict, prob: float) -> dict:
    """Simple feature ranking based on raw values (no SHAP)."""
    KNOWN_RISK = {
        "last_login_days_ago": "risk+", "payment_failures_last_6m": "risk+",
        "support_tickets_last_90d": "risk+", "logins_per_week": "risk-",
        "nps_score": "risk-", "engagement_score": "risk-",
    }
    exps = []
    for feat, direction in KNOWN_RISK.items():
        if feat in features and features[feat] is not None:
            exps.append({"feature": feat, "importance": 0.5,
                         "direction": direction, "confidence": "LOW"})
    return {
        "customer_id": features.get("customer_id","unknown"),
        "churn_probability": round(prob,4),
        "primary_method": "coefficient_fallback",
        "validators_active": 0,
        "high_conf_features": [],
        "explanations": exps[:10],
    }


def _setup_xai_path():
    for p in [settings.PHASE2_SRC, settings.BASE_DIR / "src"]:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
