"""
ks_test.py
==========
Customer Health Forensics System — Phase 4
Kolmogorov–Smirnov test for statistical significance of distribution changes.

The KS-test answers: "Is the shift in this feature's distribution statistically
significant, or could it be explained by random sampling variation?"

PSI tells you HOW MUCH the distribution shifted.
KS-test tells you WHETHER that shift is statistically real.

Together they give: drift magnitude (PSI) + drift confidence (KS p-value).
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional
from psi import PSI_MONITOR


# ── Significance thresholds ────────────────────────────────────────────────
KS_ALPHA_STRONG = 0.01   # p < 0.01 → highly significant drift
KS_ALPHA_WEAK   = 0.05   # p < 0.05 → significant drift


def ks_status(p_value: float) -> str:
    if p_value < KS_ALPHA_STRONG:
        return "highly_significant"
    elif p_value < KS_ALPHA_WEAK:
        return "significant"
    else:
        return "not_significant"


def compute_ks_single(
    reference: np.ndarray,
    current:   np.ndarray,
) -> dict:
    """
    Run two-sample KS-test between reference and current distributions.

    Args:
        reference: Reference period values.
        current:   Current period values.

    Returns:
        {
            "ks_statistic": float,   # D — max distance between CDFs
            "p_value":      float,   # probability this gap is random
            "significant":  bool,    # p < 0.05
            "status":       str,     # "highly_significant" / "significant" / "not_significant"
        }
    """
    ref = np.array(reference, dtype=float)
    cur = np.array(current,   dtype=float)

    # Remove NaN
    ref = ref[~np.isnan(ref)]
    cur = cur[~np.isnan(cur)]

    if len(ref) < 10 or len(cur) < 10:
        return {
            "ks_statistic": None,
            "p_value":      None,
            "significant":  False,
            "status":       "insufficient_data",
        }

    stat, p = stats.ks_2samp(ref, cur)

    return {
        "ks_statistic": round(float(stat), 6),
        "p_value":      round(float(p), 6),
        "significant":  bool(p < KS_ALPHA_WEAK),
        "status":       ks_status(p),
    }


def compute_ks_all_features(
    df_reference: pd.DataFrame,
    df_current:   pd.DataFrame,
    numeric_cols: list[str] = None,
) -> pd.DataFrame:
    """
    Run KS-test for all numeric features between two DataFrames.

    Args:
        df_reference: Reference period DataFrame.
        df_current:   Current period DataFrame.
        numeric_cols: Features to test. Defaults to all numeric non-target columns.

    Returns:
        DataFrame: feature, ks_statistic, p_value, significant, status
    """
    if numeric_cols is None:
        numeric_cols = df_reference.select_dtypes(include=[np.number]).columns.tolist()
        exclude = {"churned", "churn_probability_true", "snapshot_month"}
        numeric_cols = [c for c in numeric_cols if c not in exclude]

    results = []
    for col in numeric_cols:
        if col not in df_reference.columns or col not in df_current.columns:
            continue

        ref_vals = df_reference[col].dropna().values
        cur_vals = df_current[col].dropna().values

        result = compute_ks_single(ref_vals, cur_vals)
        result["feature"] = col
        results.append(result)

    df_ks = (
        pd.DataFrame(results)
        [["feature", "ks_statistic", "p_value", "significant", "status"]]
        .sort_values("ks_statistic", ascending=False, na_position="last")
        .reset_index(drop=True)
    )
    return df_ks


def combined_drift_assessment(
    df_psi: pd.DataFrame,
    df_ks:  pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge PSI and KS results into a single assessment per feature.

    A feature is "confirmed_drift" when:
      - PSI >= 0.10 (some distribution shift)  AND
      - KS p-value < 0.05 (shift is statistically significant)

    This prevents false alarms from small PSI values being treated as drift.

    Returns:
        DataFrame with columns:
        feature, psi, psi_status, ks_statistic, p_value, ks_significant,
        confirmed_drift, drift_severity
    """
    print("\n[DEBUG] df_psi columns:", df_psi.columns.tolist())
    print("[DEBUG] df_ks columns:", df_ks.columns.tolist())

    merged = df_psi.merge(df_ks, on="feature", how="outer")

    print("[DEBUG] merged columns:", merged.columns.tolist())

    # Safety guard: ensure psi_status survived the merge
    if "psi_status" not in merged.columns:
        raise ValueError("psi_status column lost during merge — check PSI output")

    def _severity(row) -> str:
        psi = row.get("psi", 0) or 0
        sig = row.get("significant", False)
        if psi > 0.20 and sig:
            return "HIGH"
        elif psi > 0.10 and sig:
            return "MEDIUM"
        elif psi > 0.10 or sig:
            return "LOW"
        return "NONE"

    merged["confirmed_drift"] = (
        (merged["psi"] >= 0.10 if "psi" in merged.columns else False) &
        (merged["significant"] == True)
    )
    merged["drift_severity"] = merged.apply(_severity, axis=1)

    return merged.sort_values("psi", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    n   = 5000
    ref = pd.DataFrame({
        "logins_per_week":    rng.normal(3.5, 1.5, n),
        "last_login_days_ago": rng.exponential(12, n),
        "nps_score":           rng.normal(6.5, 2.0, n),
    })
    cur = pd.DataFrame({
        "logins_per_week":    rng.normal(2.0, 1.5, n),   # drifted
        "last_login_days_ago": rng.exponential(25, n),   # drifted
        "nps_score":           rng.normal(6.4, 2.0, n),  # stable
    })

    df_ks = compute_ks_all_features(ref, cur)
    print(df_ks.to_string(index=False))
    print("\n✓ ks_test.py smoke test passed")
