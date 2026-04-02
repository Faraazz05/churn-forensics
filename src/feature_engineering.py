"""
feature_engineering.py
=======================
Customer Health Forensics System — Phase 1

Modular, extensible feature engineering layer.

Design principles (locked before build):
  1. NO hardcoded feature count — features are registered in a dict,
     downstream code discovers them dynamically via get_feature_names().
  2. Stickiness index = 0.5 * norm_tenure + 0.5 * norm_engagement
     (NOT raw multiplication — controlled scale, stable SHAP contribution).
  3. All composite features bounded to [0, 1] or [0, 100].
  4. Risk flags are binary (0/1) — clean signal for both tree and linear models.
  5. Adding a new feature = add one function to FEATURE_REGISTRY. Nothing else changes.

How to add a new feature:
    @register_feature("my_new_feature", "Business meaning of this feature")
    def _my_new_feature(df: pd.DataFrame) -> pd.Series:
        return (df["some_col"] / df["other_col"]).clip(0, 1)
"""

import numpy as np
import pandas as pd
from typing import Callable


# ── Feature Registry ───────────────────────────────────────────────────────
# Maps feature_name → (compute_fn, description)
# This is the ONLY place features are declared. Downstream uses get_feature_names().
_FEATURE_REGISTRY: dict[str, tuple[Callable, str]] = {}


def register_feature(name: str, description: str):
    """
    Decorator to register a feature compute function.

    Usage:
        @register_feature("my_feature", "What this measures")
        def _my_feature(df: pd.DataFrame) -> pd.Series:
            return df["col_a"] / df["col_b"].clip(lower=1)
    """
    def decorator(fn: Callable) -> Callable:
        _FEATURE_REGISTRY[name] = (fn, description)
        return fn
    return decorator


def get_feature_names() -> list[str]:
    """Return ordered list of all registered engineered feature names."""
    return list(_FEATURE_REGISTRY.keys())


def get_feature_docs() -> dict[str, str]:
    """Return {feature_name: description} for all registered features."""
    return {name: desc for name, (_, desc) in _FEATURE_REGISTRY.items()}


# ── Internal helpers ───────────────────────────────────────────────────────
def _norm(s: pd.Series, clip_upper: float = None) -> pd.Series:
    """Min-max normalize to [0, 1]. Handles zero-range edge case safely."""
    if clip_upper is not None:
        s = s.clip(upper=clip_upper)
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series(np.zeros(len(s), dtype=float), index=s.index)
    return (s - lo) / (hi - lo)


# ── Feature definitions ────────────────────────────────────────────────────
# Each function receives the FULL raw DataFrame and returns ONE Series.
# Functions must be pure — no mutations to df.

@register_feature(
    "engagement_score",
    "Normalized composite [0-1]: weighted average of logins, features used, session time, active days"
)
def _engagement_score(df: pd.DataFrame) -> pd.Series:
    norm_logins   = _norm(df["logins_per_week"],          clip_upper=20)
    norm_features = _norm(df["features_used_count"].astype(float), clip_upper=20)
    norm_session  = _norm(df["avg_session_duration_min"], clip_upper=90)
    norm_active   = _norm(df["monthly_active_days"].astype(float), clip_upper=30)
    return (0.30 * norm_logins +
            0.25 * norm_features +
            0.25 * norm_session +
            0.20 * norm_active).round(4)


@register_feature(
    "engagement_rate",
    "Active days / 30 — proportion of month the customer was active [0-1]"
)
def _engagement_rate(df: pd.DataFrame) -> pd.Series:
    return (df["monthly_active_days"] / 30).clip(0, 1).round(4)


@register_feature(
    "stickiness_index",
    "0.5*norm_tenure + 0.5*engagement_score — detects 'trapped' (high tenure, low engagement) customers"
)
def _stickiness_index(df: pd.DataFrame) -> pd.Series:
    # Requires engagement_score to already exist in df — add_features() handles ordering
    norm_tenure = _norm(df["tenure_months"].astype(float), clip_upper=72)
    # If engagement_score already computed in df, use it; else recompute
    if "engagement_score" in df.columns:
        eng = df["engagement_score"]
    else:
        eng = _engagement_score(df)
    return (0.5 * norm_tenure + 0.5 * eng).round(4)


@register_feature(
    "spend_per_active_day",
    "monthly_spend / active_days — revenue density signal (low = underutilisation risk)"
)
def _spend_per_active_day(df: pd.DataFrame) -> pd.Series:
    return (df["monthly_spend"] / df["monthly_active_days"].clip(lower=1)).round(2)


@register_feature(
    "spend_per_feature",
    "monthly_spend / features_used_count — ROI per feature used"
)
def _spend_per_feature(df: pd.DataFrame) -> pd.Series:
    return (df["monthly_spend"] / df["features_used_count"].clip(lower=1)).round(2)


@register_feature(
    "support_to_usage_ratio",
    "support_tickets / monthly_logins_est — friction per session (high = dissatisfied)"
)
def _support_to_usage_ratio(df: pd.DataFrame) -> pd.Series:
    monthly_logins = df["logins_per_week"] * 4
    return (df["support_tickets_last_90d"] / monthly_logins.clip(lower=1)).round(4)


@register_feature(
    "payment_risk_flag",
    "Binary: 1 if payment_failures_last_6m >= 2 (financial stress threshold)"
)
def _payment_risk_flag(df: pd.DataFrame) -> pd.Series:
    return (df["payment_failures_last_6m"] >= 2).astype(int)


@register_feature(
    "recency_risk_flag",
    "Binary: 1 if last_login_days_ago > 21 (3-week inactivity threshold)"
)
def _recency_risk_flag(df: pd.DataFrame) -> pd.Series:
    return (df["last_login_days_ago"] > 21).astype(int)


@register_feature(
    "lifetime_value_est",
    "monthly_spend * tenure_months — historical cumulative revenue from this customer"
)
def _lifetime_value_est(df: pd.DataFrame) -> pd.Series:
    return (df["monthly_spend"] * df["tenure_months"]).round(2)


@register_feature(
    "nps_band",
    "Ordinal NPS category: 0=detractor (0-6), 1=passive (7-8), 2=promoter (9-10)"
)
def _nps_band(df: pd.DataFrame) -> pd.Series:
    return pd.cut(
        df["nps_score"],
        bins=[-0.1, 6.0, 8.0, 10.1],
        labels=[0, 1, 2]
    ).astype(int)


@register_feature(
    "commitment_score",
    "Contract intent proxy: annual=1.0, monthly=0.5"
)
def _commitment_score(df: pd.DataFrame) -> pd.Series:
    return np.where(df["contract_type"] == "annual", 1.0, 0.5)


@register_feature(
    "customer_health_score",
    "Composite [0-100] dashboard score: engagement + recency + payment health + satisfaction"
)
def _customer_health_score(df: pd.DataFrame) -> pd.Series:
    # Reuse or recompute sub-components
    eng = df["engagement_score"] if "engagement_score" in df.columns else _engagement_score(df)
    recency_score  = 1 - _norm(df["last_login_days_ago"], clip_upper=180)
    payment_health = 1 - _norm(df["payment_failures_last_6m"].astype(float), clip_upper=6)
    satisfaction   = _norm(df["nps_score"], clip_upper=10)

    return (0.30 * eng +
            0.25 * recency_score +
            0.25 * payment_health +
            0.20 * satisfaction).multiply(100).round(1)


# ── Public API ─────────────────────────────────────────────────────────────
def add_features(df: pd.DataFrame, features: list[str] = None) -> pd.DataFrame:
    """
    Add engineered features to a DataFrame.

    Non-destructive — returns a new DataFrame with additional columns.
    Works on any input size: single row, chunk, or full 500k dataset.

    Args:
        df:       Raw customer DataFrame (must contain required raw columns).
        features: Optional list of feature names to compute. Defaults to ALL
                  registered features. Pass a subset to compute only what's needed.

    Returns:
        New DataFrame with original columns + engineered feature columns appended.
    """
    df = df.copy()
    target_features = features if features is not None else get_feature_names()

    # Compute features in registration order (stickiness_index needs engagement_score first)
    for name in get_feature_names():
        if name in target_features:
            fn, _ = _FEATURE_REGISTRY[name]
            df[name] = fn(df)

    return df


def get_model_feature_cols(
    df: pd.DataFrame,
    cat_cols: list[str] = None,
    drop_cols: list[str] = None,
) -> list[str]:
    """
    Return the final list of feature column names to pass to the model.
    Discovers engineered features dynamically — no hardcoded list.

    Args:
        df:        DataFrame AFTER add_features() has been called.
        cat_cols:  Categorical columns that were one-hot encoded.
                   Defaults to ["plan_type","contract_type","payment_method","region"].
        drop_cols: Additional columns to exclude from feature set.

    Returns:
        Sorted list of model-ready feature column names.
    """
    if cat_cols is None:
        cat_cols = ["plan_type", "contract_type", "payment_method", "region"]

    always_exclude = {
        "customer_id", "churned", "churn_probability_true", "snapshot_month"
    }
    if drop_cols:
        always_exclude.update(drop_cols)

    # Exclude raw categorical cols (they appear as encoded dummies instead)
    always_exclude.update(cat_cols)

    return [c for c in df.columns if c not in always_exclude]


def build_feature_matrix(
    df: pd.DataFrame,
    cat_cols:  list[str] = None,
    drop_cols: list[str] = None,
    target:    str       = "churned",
) -> tuple[pd.DataFrame, pd.Series | None]:
    """
    Full feature matrix construction pipeline:
      1. Add all engineered features
      2. One-hot encode categoricals
      3. Select model columns dynamically
      4. Return (X, y)

    Args:
        df:        Raw customer DataFrame.
        cat_cols:  Categorical columns to one-hot encode.
        drop_cols: Additional columns to exclude.
        target:    Target column name. Pass None to skip y extraction.

    Returns:
        (X, y) where y is None if target column absent.
    """
    if cat_cols is None:
        cat_cols = ["plan_type", "contract_type", "payment_method", "region"]

    # Step 1: engineer features
    df_feat = add_features(df)

    # Step 2: encode categoricals
    df_enc = pd.get_dummies(df_feat, columns=cat_cols, drop_first=True, dtype=int)

    # Step 3: discover feature columns
    feature_cols = get_model_feature_cols(df_enc, cat_cols=cat_cols, drop_cols=drop_cols)
    feature_cols = [c for c in feature_cols if c in df_enc.columns]

    X = df_enc[feature_cols]
    y = df_enc[target] if (target and target in df_enc.columns) else None

    return X, y


def validate_features(df: pd.DataFrame) -> bool:
    """
    Run range / null checks on all registered features.
    Raises AssertionError on failure. Returns True on full pass.
    """
    df_feat = add_features(df)

    range_checks = {
        "engagement_score":    (0.0, 1.0),
        "engagement_rate":     (0.0, 1.0),
        "stickiness_index":    (0.0, 1.0),
        "payment_risk_flag":   (0,   1),
        "recency_risk_flag":   (0,   1),
        "commitment_score":    (0.4, 1.1),
        "customer_health_score": (0.0, 100.0),
        "nps_band":            (0,   2),
    }

    print("\n── Feature Validation ──────────────────────────────")
    all_pass = True
    for feat in get_feature_names():
        col = df_feat[feat]
        nulls = int(col.isnull().sum())
        lo, hi = float(col.min()), float(col.max())

        if feat in range_checks:
            exp_lo, exp_hi = range_checks[feat]
            ok = (lo >= exp_lo) and (hi <= exp_hi) and (nulls == 0)
        else:
            ok = nulls == 0

        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{status}] {feat:35s} range=[{lo:.3f}, {hi:.3f}]  nulls={nulls}")

    n_features = len(get_feature_names())
    print(f"\n  Total engineered features: {n_features}")
    print(f"  {'✓ All checks passed' if all_pass else '✗ Some checks FAILED'}")

    assert all_pass, "Feature validation failed — see output above"
    return True


if __name__ == "__main__":
    # Quick smoke test
    rng = np.random.default_rng(42)
    n   = 1_000
    dummy = pd.DataFrame({
        "customer_id":               [f"C{i}" for i in range(n)],
        "age":                        rng.integers(18, 70, n),
        "tenure_months":              rng.integers(1, 72, n),
        "plan_type":                  rng.choice(["basic","pro","enterprise"], n),
        "contract_type":              rng.choice(["monthly","annual"], n),
        "payment_method":             rng.choice(["card","paypal","bank_transfer"], n),
        "region":                     rng.choice(["North","South","East","West","Central"], n),
        "logins_per_week":            rng.uniform(0, 20, n).round(1),
        "features_used_count":        rng.integers(1, 20, n),
        "avg_session_duration_min":   rng.uniform(1, 90, n).round(1),
        "monthly_active_days":        rng.integers(0, 30, n),
        "last_login_days_ago":        rng.integers(0, 180, n),
        "monthly_spend":              rng.uniform(20, 350, n).round(2),
        "payment_failures_last_6m":   rng.integers(0, 6, n),
        "referrals_made":             rng.integers(0, 10, n),
        "support_tickets_last_90d":   rng.integers(0, 15, n),
        "nps_score":                  rng.uniform(0, 10, n).round(1),
        "churned":                    rng.integers(0, 2, n),
        "churn_probability_true":     rng.uniform(0, 1, n).round(4),
    })

    validate_features(dummy)
    X, y = build_feature_matrix(dummy)
    print(f"\nFeature matrix: {X.shape[1]} columns")
    print(f"Registered features: {get_feature_names()}")
    print("\n✓ feature_engineering.py smoke test passed")
