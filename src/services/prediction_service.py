"""
services/prediction_service.py
================================
Calls Phase 1 model. No business logic — pure delegation.
"""

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from core.config import get_settings
from utils.logger import log

settings = get_settings()

_model       = None
_feat_names  = None
_model_info  = None

RISK_TIERS = {(0.70, 1.01): "Critical", (0.50, 0.70): "High",
              (0.30, 0.50): "Medium",   (0.00, 0.30): "Safe"}


def _risk_tier(prob: float) -> str:
    for (lo, hi), label in RISK_TIERS.items():
        if lo <= prob < hi:
            return label
    return "Safe"


def _load_model():
    global _model, _feat_names, _model_info
    if _model is not None:
        return _model

    model_path = settings.MODELS_DIR / "best_model.pkl"
    feat_path  = settings.MODELS_DIR / "feature_names.json"
    info_path  = settings.MODELS_DIR / "best_model_info.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    _model = joblib.load(model_path)

    if feat_path.exists():
        with open(feat_path) as f:
            _feat_names = json.load(f)

    if info_path.exists():
        with open(info_path) as f:
            _model_info = json.load(f)

    log.info(f"[PredictionService] Model loaded: "
             f"{_model_info.get('best_model_name','?') if _model_info else '?'}")
    return _model


def is_model_loaded() -> bool:
    try:
        _load_model()
        return True
    except Exception:
        return False


def predict_single(features: dict) -> dict:
    """Predict churn probability for a single customer."""
    model = _load_model()

    # Feature engineering
    _setup_phase1_path()
    from feature_engineering import add_features, build_feature_matrix

    df  = pd.DataFrame([features])
    X, _ = build_feature_matrix(df, target=None)

    if _feat_names:
        X = X.reindex(columns=_feat_names, fill_value=0)

    prob = float(model.predict_proba(X)[0, 1])

    return {
        "customer_id":       features.get("customer_id", "unknown"),
        "churn_probability": round(prob, 4),
        "risk_tier":         _risk_tier(prob),
        "model_name":        _model_info.get("best_model_name") if _model_info else "unknown",
    }


def predict_batch(records: list[dict]) -> list[dict]:
    """Batch prediction — processes all records at once."""
    model = _load_model()
    _setup_phase1_path()
    from feature_engineering import build_feature_matrix

    df  = pd.DataFrame(records)
    X, _ = build_feature_matrix(df, target=None)
    if _feat_names:
        X = X.reindex(columns=_feat_names, fill_value=0)

    probs = model.predict_proba(X)[:, 1]
    model_name = _model_info.get("best_model_name") if _model_info else "unknown"

    return [
        {
            "customer_id":       r.get("customer_id", f"row_{i}"),
            "churn_probability": round(float(p), 4),
            "risk_tier":         _risk_tier(float(p)),
            "model_name":        model_name,
        }
        for i, (r, p) in enumerate(zip(records, probs))
    ]


def get_model_info() -> dict:
    try:
        _load_model()
        return _model_info or {}
    except Exception as e:
        return {"error": str(e)}


def _setup_phase1_path():
    for p in [settings.PHASE1_SRC, settings.BASE_DIR / "src"]:
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
