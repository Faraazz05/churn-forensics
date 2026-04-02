"""
model.py
========
Customer Health Forensics System — Phase 1
Central model registry: definitions, hyperparameters, XAI method mapping.

This is the ONLY place models are defined.
train.py and model_selector.py import from here — nothing is duplicated.

Design decisions locked:
  - Size-aware candidate sets (SVM dropped at 50k+, RF at 500k+)
  - XAI-coupling: if XGBoost within 0.01 AUC of winner → prefer XGBoost
  - Logistic Regression always built (interpretable baseline, coefficients logged)
  - class_weight="balanced" on all models — handles 22% churn rate without SMOTE

Adding a new model:
  1. Add its builder function below following the _build_* pattern
  2. Add it to MODEL_BUILDERS dict
  3. Add its XAI method to XAI_METHOD_MAP
  4. Add it to whichever SIZE_TIERS it belongs in
  Nothing else changes — model_selector.py picks it up automatically.
"""

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBClassifier = None
    XGBOOST_AVAILABLE = False


# ── Hyperparameters ────────────────────────────────────────────────────────
# Centralised — change once, applies everywhere.

XGBOOST_PARAMS = dict(
    n_estimators      = 300,
    max_depth         = 6,
    learning_rate     = 0.05,
    subsample         = 0.8,
    colsample_bytree  = 0.8,
    tree_method       = "hist",      # memory-efficient for 500k+
    eval_metric       = "auc",
    random_state      = 42,
    n_jobs            = -1,
    verbosity         = 0,
)

RANDOM_FOREST_PARAMS = dict(
    n_estimators      = 200,
    max_depth         = 12,
    min_samples_leaf  = 20,          # prevents overfitting at scale
    class_weight      = "balanced",
    n_jobs            = -1,
    random_state      = 42,
)

SVM_PARAMS = dict(
    probability       = True,
    kernel            = "rbf",
    C                 = 1.0,
    class_weight      = "balanced",
    random_state      = 42,
)

LOGISTIC_PARAMS = dict(
    max_iter          = 1000,
    C                 = 0.1,         # L2 regularisation
    solver            = "saga",      # efficient for large n
    class_weight      = "balanced",
    random_state      = 42,
)


# ── XAI method mapping ─────────────────────────────────────────────────────
# Drives Phase 2 — which explainer to use for which model.
XAI_METHOD_MAP: dict[str, str] = {
    "xgboost":       "SHAP_TreeExplainer",    # exact, fast, native tree support
    "random_forest": "SHAP_TreeExplainer",    # native tree support
    "logistic":      "logistic_coefficients", # direct — no SHAP overhead needed
    "svm":           "SHAP_KernelExplainer",  # slow fallback (model-agnostic)
}


# ── Size tiers ─────────────────────────────────────────────────────────────
# Controls which models are trained based on dataset size.
# SVM is O(n²) — unusable at 50k+.
# RandomForest is memory-heavy — dropped at 500k+.
# Logistic always present as interpretable baseline.
SIZE_TIERS: dict[str, list[str]] = {
    "small":  ["xgboost", "random_forest", "svm", "logistic"],   # < 50k
    "medium": ["xgboost", "random_forest", "logistic"],           # < 500k
    "large":  ["xgboost", "logistic"],                            # >= 500k
}

SIZE_TIER_THRESHOLDS = {
    "small":  50_000,
    "medium": 500_000,
    # large = anything above medium
}


# ── XAI coupling threshold ─────────────────────────────────────────────────
# If best_model.val_auc - xgboost.val_auc < this → prefer XGBoost.
# Rationale: sacrificing <1% AUC for exact SHAP TreeExplainer is correct
# in a diagnostic system where clarity > marginal accuracy.
XAI_COUPLING_DELTA = 0.01


# ── Builder functions ──────────────────────────────────────────────────────
def _build_xgboost():
    if not XGBOOST_AVAILABLE:
        return None
    return XGBClassifier(**XGBOOST_PARAMS)


def _build_random_forest():
    return RandomForestClassifier(**RANDOM_FOREST_PARAMS)


def _build_svm():
    # SVM requires scaled features — wrap in Pipeline
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm",    SVC(**SVM_PARAMS)),
    ])


def _build_logistic():
    # Logistic also benefits from scaling
    return Pipeline([
        ("scaler", StandardScaler()),
        ("lr",     LogisticRegression(**LOGISTIC_PARAMS)),
    ])


# ── Model builder registry ─────────────────────────────────────────────────
MODEL_BUILDERS: dict[str, callable] = {
    "xgboost":       _build_xgboost,
    "random_forest": _build_random_forest,
    "svm":           _build_svm,
    "logistic":      _build_logistic,
}


# ── Public helpers ─────────────────────────────────────────────────────────
def get_size_tier(dataset_size: int) -> str:
    """Return the size tier label for a given dataset size."""
    if dataset_size < SIZE_TIER_THRESHOLDS["small"]:
        return "small"
    elif dataset_size < SIZE_TIER_THRESHOLDS["medium"]:
        return "medium"
    return "large"


def get_candidates(dataset_size: int) -> dict[str, object]:
    """
    Return instantiated candidate models for a given dataset size.
    Skips any model whose builder returns None (e.g. XGBoost not installed).

    Args:
        dataset_size: Total number of training rows.

    Returns:
        Dict of {model_name: fitted_estimator_instance}
    """
    tier  = get_size_tier(dataset_size)
    names = SIZE_TIERS[tier]

    candidates = {}
    for name in names:
        model = MODEL_BUILDERS[name]()
        if model is not None:
            candidates[name] = model
        else:
            print(f"  [model.py] Skipping '{name}' — builder returned None "
                  f"(package not installed?)")

    print(f"  Size tier: {tier} ({dataset_size:,} rows) → "
          f"candidates: {list(candidates.keys())}")
    return candidates


def get_xai_method(model_name: str) -> str:
    """Return the recommended XAI method for a given model name."""
    return XAI_METHOD_MAP.get(model_name, "SHAP_KernelExplainer")


def extract_logistic_coefs(logistic_model, feature_names: list[str]):
    """
    Extract Logistic Regression coefficients as a DataFrame.
    Works whether logistic_model is a raw LR or a Pipeline wrapping one.

    Returns:
        pd.DataFrame with columns: feature, coefficient, abs_coef, direction
    """
    import numpy as np
    import pandas as pd

    lr = (logistic_model.named_steps["lr"]
          if hasattr(logistic_model, "named_steps")
          else logistic_model)

    coefs = pd.DataFrame({
        "feature":     feature_names,
        "coefficient": lr.coef_[0],
    })
    coefs["abs_coef"]  = coefs["coefficient"].abs()
    coefs["direction"] = np.where(coefs["coefficient"] > 0, "risk+", "risk-")
    coefs = (coefs
             .sort_values("abs_coef", ascending=False)
             .round(4)
             .reset_index(drop=True))
    return coefs


def model_summary() -> None:
    """Print a human-readable summary of all registered models and tiers."""
    print("\n── Model Registry Summary ──────────────────────────")
    print(f"  XGBoost available : {XGBOOST_AVAILABLE}")
    print(f"  XAI coupling delta: {XAI_COUPLING_DELTA}")
    print()
    for tier, names in SIZE_TIERS.items():
        threshold = SIZE_TIER_THRESHOLDS.get(tier, "∞")
        print(f"  [{tier.upper()}] (< {threshold:,} rows): {names}")
    print()
    print("  XAI method mapping:")
    for name, method in XAI_METHOD_MAP.items():
        print(f"    {name:15s} → {method}")
    print()


if __name__ == "__main__":
    model_summary()
    print("Building one of each to verify constructors...")
    for name, builder in MODEL_BUILDERS.items():
        m = builder()
        status = "✓" if m is not None else "✗ (package missing)"
        print(f"  {status} {name}: {type(m).__name__ if m else 'None'}")
    print("\n✓ model.py OK")
