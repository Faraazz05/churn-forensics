"""
psi.py
======
Customer Health Forensics System — Phase 4
Population Stability Index (PSI) computation.

PSI measures how much a feature's distribution has shifted between
a reference period and a current period.

Thresholds:
  PSI < 0.10  → stable          (no action)
  PSI 0.10–0.20 → monitor       (watch next period)
  PSI > 0.20  → significant drift (investigate / retrain)
"""

import numpy as np
import pandas as pd
from typing import Union


# ── Thresholds ─────────────────────────────────────────────────────────────
PSI_STABLE    = 0.10
PSI_MONITOR   = 0.20
N_BINS        = 10
EPSILON       = 1e-6   # prevents log(0)


def psi_status(psi_value: float) -> str:
    if psi_value < PSI_STABLE:
        return "stable"
    elif psi_value < PSI_MONITOR:
        return "monitor"
    else:
        return "significant_drift"


def compute_psi_single(
    reference: np.ndarray,
    current:   np.ndarray,
    n_bins:    int = N_BINS,
) -> float:
    """
    Compute PSI between a reference and current distribution.

    Formula:
        PSI = Σ (current% - reference%) × ln(current% / reference%)

    Args:
        reference: Array of feature values from reference period.
        current:   Array of feature values from current period.
        n_bins:    Number of quantile bins to use.

    Returns:
        PSI score (float >= 0)
    """
    reference = np.array(reference, dtype=float)
    current   = np.array(current,   dtype=float)

    # Build bins on reference distribution
    breakpoints = np.nanpercentile(reference, np.linspace(0, 100, n_bins + 1))
    breakpoints = np.unique(breakpoints)  # remove duplicates from low-variance features

    if len(breakpoints) < 2:
        # Degenerate — all values the same, no distribution to compare
        return 0.0

    # Count proportions in each bin
    ref_counts = np.histogram(reference, bins=breakpoints)[0]
    cur_counts = np.histogram(current,   bins=breakpoints)[0]

    ref_pct = ref_counts / (len(reference) + EPSILON)
    cur_pct = cur_counts / (len(current)   + EPSILON)

    # Avoid log(0)
    ref_pct = np.where(ref_pct == 0, EPSILON, ref_pct)
    cur_pct = np.where(cur_pct == 0, EPSILON, cur_pct)

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return float(round(psi, 6))


def compute_psi_all_features(
    df_reference: pd.DataFrame,
    df_current:   pd.DataFrame,
    numeric_cols: list[str] = None,
    n_bins:       int       = N_BINS,
) -> pd.DataFrame:
    """
    Compute PSI for all numeric features between two DataFrames.

    Args:
        df_reference: DataFrame from the reference period.
        df_current:   DataFrame from the current period.
        numeric_cols: Columns to compute PSI for. Defaults to all numeric.
        n_bins:       Number of bins.

    Returns:
        DataFrame with columns: feature, psi, status, reference_n, current_n
    """
    if numeric_cols is None:
        numeric_cols = df_reference.select_dtypes(include=[np.number]).columns.tolist()
        # Remove non-feature columns
        exclude = {"churned", "churn_probability_true", "snapshot_month"}
        numeric_cols = [c for c in numeric_cols if c not in exclude]

    def assign_psi_status(psi):
        if psi < 0.10:
            return "stable"
        elif psi < 0.20:
            return "monitor"
        else:
            return "significant_drift"

    results = []
    for col in numeric_cols:
        if col not in df_reference.columns or col not in df_current.columns:
            continue

        ref_vals = df_reference[col].dropna().values
        cur_vals = df_current[col].dropna().values

        if len(ref_vals) < 30 or len(cur_vals) < 30:
            continue  # Not enough data for meaningful PSI

        psi_val = compute_psi_single(ref_vals, cur_vals, n_bins)
        results.append({
            "feature":      col,
            "psi":          psi_val,
            "psi_status":   assign_psi_status(psi_val),
            "reference_n":  len(ref_vals),
            "current_n":    len(cur_vals),
        })

    df_psi = (
        pd.DataFrame(results)
        .sort_values("psi", ascending=False)
        .reset_index(drop=True)
    )
    return df_psi


def psi_summary(df_psi: pd.DataFrame) -> dict:
    """
    Summarise PSI results across all features.

    Returns:
        {
            "n_stable": int,
            "n_monitor": int,
            "n_drifted": int,
            "max_psi": float,
            "max_psi_feature": str,
            "retraining_trigger": bool,   # PSI > 0.2 on 3+ features
            "drifted_features": [...]
        }
    """
    if df_psi.empty:
        return {"n_stable": 0, "n_monitor": 0, "n_drifted": 0,
                "retraining_trigger": False, "drifted_features": []}

    # Support both legacy "status" and new "psi_status" column names
    status_col = "psi_status" if "psi_status" in df_psi.columns else "status"
    drifted = df_psi[df_psi[status_col] == "significant_drift"]
    monitor = df_psi[df_psi[status_col] == "monitor"]
    stable  = df_psi[df_psi[status_col] == "stable"]

    return {
        "n_stable":           len(stable),
        "n_monitor":          len(monitor),
        "n_drifted":          len(drifted),
        "max_psi":            float(df_psi["psi"].max()),
        "max_psi_feature":    df_psi.iloc[0]["feature"] if len(df_psi) > 0 else None,
        "retraining_trigger": len(drifted) >= 3,
        "drifted_features":   drifted["feature"].tolist(),
        "monitor_features":   monitor["feature"].tolist(),
    }


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    n   = 5000
    ref = pd.DataFrame({"logins_per_week": rng.normal(3.5, 1.5, n),
                         "last_login_days_ago": rng.exponential(12, n)})
    # Simulate drift: mean shifts
    cur = pd.DataFrame({"logins_per_week": rng.normal(2.0, 1.5, n),   # drifted
                         "last_login_days_ago": rng.exponential(25, n)})  # drifted

    df_psi = compute_psi_all_features(ref, cur)
    print(df_psi.to_string(index=False))
    print("\nSummary:", psi_summary(df_psi))
    print("\n✓ psi.py smoke test passed")
