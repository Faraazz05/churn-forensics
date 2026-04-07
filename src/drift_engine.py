"""
drift_engine.py
===============
Customer Health Forensics System — Phase 4
Advanced Drift Detection + Early Warning System.

Pipeline:
  1. PSI — feature distribution shift magnitude
  2. KS-test — statistical significance of shift
  3. Trend analysis — direction + velocity per feature across months
  4. Leading indicator detection — high-importance features showing decline
  5. Early warning flags — features that are leading indicators AND trending negative
  6. Retraining trigger — PSI > 0.2 on 3+ features simultaneously

Leading indicators (from Phase 1 + Phase 2):
  These are the features that predict churn earliest:
  - last_login_days_ago   (rising = risk)
  - logins_per_week       (falling = risk)
  - engagement_score      (falling = risk)
  - support_tickets_last_90d (rising = risk)
  - payment_failures_last_6m (rising = risk)
  - monthly_active_days   (falling = risk)
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from psi     import compute_psi_all_features, psi_summary, PSI_MONITOR
from ks_test import compute_ks_all_features, combined_drift_assessment


# ── Leading indicators ────────────────────────────────────────────────────
# Direction "up" = rising value is bad for retention (inactivity/stress features)
# Direction "down" = falling value is bad for retention (engagement features)
LEADING_INDICATORS: dict[str, str] = {
    "last_login_days_ago":       "up",    # more days away = worse
    "logins_per_week":           "down",  # fewer logins = worse
    "engagement_score":          "down",
    "support_tickets_last_90d":  "up",
    "payment_failures_last_6m":  "up",
    "monthly_active_days":       "down",
    "avg_session_duration_min":  "down",
    "recency_risk_flag":         "up",
    "payment_risk_flag":         "up",
    "customer_health_score":     "down",
}

DRIFT_SEVERITY_LEVELS = ["NONE", "LOW", "MEDIUM", "HIGH"]

RETRAINING_PSI_THRESHOLD   = 0.20
RETRAINING_FEATURE_COUNT   = 3    # PSI > threshold on this many features → retrain


# ── Trend analysis ─────────────────────────────────────────────────────────
def compute_feature_trend(
    monthly_means: pd.Series,  # index = month number, values = mean feature value
) -> dict:
    """
    Compute trend direction and velocity for a feature across months.

    Args:
        monthly_means: Series indexed by snapshot_month with mean values.

    Returns:
        {
            "direction":   "increasing" / "decreasing" / "stable",
            "velocity":    "high" / "medium" / "low",
            "slope":       float,   # units per month (from linear regression)
            "r_squared":   float,   # goodness of fit for trend
            "pct_change":  float,   # total % change first → last period
        }
    """
    months = np.array(monthly_means.index, dtype=float)
    values = np.array(monthly_means.values, dtype=float)

    if len(months) < 2:
        return {"direction": "stable", "velocity": "low",
                "slope": 0.0, "r_squared": 0.0, "pct_change": 0.0}

    # Linear regression for slope
    slope, intercept, r, p, se = stats.linregress(months, values)
    r_squared = r ** 2

    # Percentage change
    first_val = values[0]
    last_val  = values[-1]
    pct_change = ((last_val - first_val) / abs(first_val)) if abs(first_val) > 1e-9 else 0.0

    # Direction threshold: slope must be meaningful relative to value range
    val_range = values.max() - values.min()
    threshold = 0.01 * abs(values.mean()) if abs(values.mean()) > 1e-9 else 1e-6

    if abs(slope) < threshold:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    # Velocity based on absolute % change
    abs_pct = abs(pct_change)
    if abs_pct > 0.20:
        velocity = "high"
    elif abs_pct > 0.08:
        velocity = "medium"
    else:
        velocity = "low"

    return {
        "direction":  direction,
        "velocity":   velocity,
        "slope":      round(float(slope), 6),
        "r_squared":  round(float(r_squared), 4),
        "pct_change": round(float(pct_change), 4),
    }


def is_early_warning(
    feature:    str,
    trend:      dict,
    psi_value:  float,
    xai_top_features: list[str] = None,
) -> bool:
    """
    Determine if a feature should trigger an early warning flag.

    Conditions (ALL must be true):
      1. Feature is a known leading indicator
      2. Trend direction is adverse (rising for "up" indicators, falling for "down")
      3. PSI > 0.10 (distribution has actually shifted)

    Optional boost: feature is in XAI top features from Phase 2.
    """
    if feature not in LEADING_INDICATORS:
        return False

    bad_direction = LEADING_INDICATORS[feature]
    trend_dir     = trend.get("direction", "stable")

    direction_is_adverse = (
        (bad_direction == "up"   and trend_dir == "increasing") or
        (bad_direction == "down" and trend_dir == "decreasing")
    )

    distribution_shifted = psi_value >= 0.10

    # XAI boost — if this feature was identified as high-importance in Phase 2
    is_xai_important = (xai_top_features is not None and feature in xai_top_features)

    return direction_is_adverse and (distribution_shifted or is_xai_important)


# ── Core drift engine ──────────────────────────────────────────────────────
class DriftEngine:
    """
    Full drift detection pipeline for Phase 4.

    Usage:
        engine = DriftEngine(df_snapshots, reference_month=1, current_month=12)
        report = engine.run()
    """

    def __init__(
        self,
        df_snapshots:     pd.DataFrame,
        reference_month:  int = None,    # defaults to earliest month
        current_month:    int = None,    # defaults to latest month
        xai_top_features: list[str] = None,  # Phase 2 global top features
        verbose:          bool = True,
    ):
        if "snapshot_month" not in df_snapshots.columns:
            raise ValueError("df_snapshots must contain a 'snapshot_month' column.")

        self.df    = df_snapshots
        self.months = sorted(df_snapshots["snapshot_month"].unique())
        self.ref_month = reference_month if reference_month else self.months[0]
        self.cur_month = current_month   if current_month   else self.months[-1]
        self.xai_top   = xai_top_features or []
        self.verbose   = verbose

        self._numeric_cols = self._get_numeric_cols()

        if verbose:
            print(f"[DriftEngine] Months: {self.months}")
            print(f"[DriftEngine] Reference: Month {self.ref_month} → "
                  f"Current: Month {self.cur_month}")
            print(f"[DriftEngine] Features tracked: {len(self._numeric_cols)}")

    def _get_numeric_cols(self) -> list[str]:
        exclude = {"churned", "churn_probability_true", "snapshot_month"}
        return [c for c in self.df.select_dtypes(include=[np.number]).columns
                if c not in exclude]

    def _slice(self, month: int) -> pd.DataFrame:
        return self.df[self.df["snapshot_month"] == month]

    # ── Step 1+2: PSI + KS ────────────────────────────────────────────────
    def run_psi_ks(self) -> pd.DataFrame:
        df_ref = self._slice(self.ref_month)
        df_cur = self._slice(self.cur_month)

        df_psi = compute_psi_all_features(df_ref, df_cur, self._numeric_cols)
        df_ks  = compute_ks_all_features(df_ref, df_cur, self._numeric_cols)
        df_combined = combined_drift_assessment(df_psi, df_ks)
        return df_combined

    # ── Step 3: Trend analysis (all months) ───────────────────────────────
    def run_trend_analysis(self) -> dict[str, dict]:
        """
        For each feature, compute monthly mean across all snapshot months
        and derive trend direction + velocity.

        Returns: {feature_name: trend_dict}
        """
        trend_results = {}
        for col in self._numeric_cols:
            monthly_means = (
                self.df.groupby("snapshot_month")[col]
                .mean()
                .sort_index()
            )
            trend_results[col] = compute_feature_trend(monthly_means)
        return trend_results

    # ── Step 4+5: Leading indicators + early warnings ─────────────────────
    def run_early_warnings(
        self,
        df_drift:    pd.DataFrame,
        trends:      dict[str, dict],
    ) -> list[dict]:
        """
        Cross-reference drift + trends + leading indicator knowledge
        to produce early warning flags.

        Returns:
            List of early warning dicts, sorted by severity.
        """
        warnings = []
        psi_map = dict(zip(df_drift["feature"], df_drift["psi"])) if "psi" in df_drift.columns else {}

        for feat in self._numeric_cols:
            psi_val = float(psi_map.get(feat, 0) or 0)
            trend   = trends.get(feat, {})

            if not is_early_warning(feat, trend, psi_val, self.xai_top):
                continue

            # Compute impact label
            is_xai  = feat in self.xai_top
            impact  = "leading churn indicator" + (" (XAI-confirmed)" if is_xai else "")

            # Drift severity from combined table
            drift_row = df_drift[df_drift["feature"] == feat] if not df_drift.empty else pd.DataFrame()
            severity = drift_row["drift_severity"].values[0] if len(drift_row) > 0 else "LOW"

            warnings.append({
                "feature":        feat,
                "psi":            round(psi_val, 4),
                "trend":          trend.get("direction", "stable"),
                "velocity":       trend.get("velocity", "low"),
                "pct_change":     trend.get("pct_change", 0.0),
                "impact":         impact,
                "early_warning":  True,
                "drift_severity": severity,
                "xai_confirmed":  is_xai,
            })

        # Sort: XAI-confirmed first, then by PSI descending
        warnings.sort(key=lambda x: (-int(x["xai_confirmed"]), -x["psi"]))
        return warnings

    # ── Step 6+7: Drift output with severity ──────────────────────────────
    def build_drift_report(
        self,
        df_drift:  pd.DataFrame,
        trends:    dict[str, dict],
        warnings:  list[dict],
    ) -> list[dict]:
        """
        Build the enhanced drift report in the required output format.

        Returns:
            List of per-feature drift dicts.
        """
        report = []
        for _, row in df_drift.iterrows():
            feat    = row["feature"]
            psi_val = float(row.get("psi", 0) or 0)
            trend   = trends.get(feat, {})
            is_warn = any(w["feature"] == feat for w in warnings)

            impact = "leading churn indicator" if feat in LEADING_INDICATORS else "general feature"

            report.append({
                "feature":        feat,
                "psi":            round(psi_val, 4),
                "psi_status":     str(row.get("psi_status", "stable")),
                "ks_statistic":   float(row.get("ks_statistic", 0) or 0),
                "p_value":        float(row.get("p_value", 1.0) or 1.0),
                "ks_significant": bool(row.get("significant", False)),
                "confirmed_drift": bool(row.get("confirmed_drift", False)),
                "drift_severity": str(row.get("drift_severity", "NONE")),
                "trend":          trend.get("direction", "stable"),
                "velocity":       trend.get("velocity", "low"),
                "slope":          trend.get("slope", 0.0),
                "pct_change":     trend.get("pct_change", 0.0),
                "impact":         impact,
                "early_warning":  is_warn,
            })

        return sorted(report, key=lambda x: -x["psi"])

    # ── Retraining trigger ─────────────────────────────────────────────────
    def check_retraining_trigger(self, df_drift: pd.DataFrame) -> dict:
        """
        Evaluate whether model retraining is required.

        Trigger condition: PSI > 0.20 on 3+ features simultaneously.
        """
        if "psi" not in df_drift.columns:
            return {"model_retraining_required": False, "reason": "No PSI data"}

        high_psi = df_drift[df_drift["psi"] > RETRAINING_PSI_THRESHOLD]
        required = len(high_psi) >= RETRAINING_FEATURE_COUNT

        return {
            "model_retraining_required": bool(required),
            "features_above_threshold":  high_psi["feature"].tolist(),
            "n_features_drifted":        int(len(high_psi)),
            "threshold_psi":             RETRAINING_PSI_THRESHOLD,
            "threshold_count":           RETRAINING_FEATURE_COUNT,
            "reason": (
                f"PSI > {RETRAINING_PSI_THRESHOLD} on {len(high_psi)} features "
                f"(threshold: {RETRAINING_FEATURE_COUNT})"
                if required else
                f"Only {len(high_psi)} features drifted significantly "
                f"(need {RETRAINING_FEATURE_COUNT}+)"
            ),
        }

    # ── Full pipeline ──────────────────────────────────────────────────────
    def run(self) -> dict:
        """
        Execute full Phase 4 drift detection pipeline.

        Returns:
            Complete drift report dict (JSON serializable).
        """
        if self.verbose:
            print("\n[DriftEngine] Running PSI + KS-test...")
        df_drift = self.run_psi_ks()

        if self.verbose:
            print("[DriftEngine] Running trend analysis across months...")
        trends = self.run_trend_analysis()

        if self.verbose:
            print("[DriftEngine] Detecting early warnings...")
        warnings = self.run_early_warnings(df_drift, trends)

        drift_report   = self.build_drift_report(df_drift, trends, warnings)
        retrain_check  = self.check_retraining_trigger(df_drift)
        required_cols = ["feature", "psi", "psi_status"]

        if all(col in df_drift.columns for col in required_cols):
            psi_sum = psi_summary(df_drift[required_cols])
        else:
            print("[DriftEngine WARNING] PSI summary skipped.")
            print("Available columns:", df_drift.columns.tolist())
            psi_sum = {}

        # Overall severity
        n_high = sum(1 for d in drift_report if d["drift_severity"] == "HIGH")
        n_med  = sum(1 for d in drift_report if d["drift_severity"] == "MEDIUM")
        if n_high >= 3:
            overall_severity = "HIGH"
        elif n_high >= 1 or n_med >= 3:
            overall_severity = "MEDIUM"
        elif n_med >= 1:
            overall_severity = "LOW"
        else:
            overall_severity = "NONE"

        if self.verbose:
            print(f"[DriftEngine] Early warnings: {len(warnings)}")
            print(f"[DriftEngine] Overall severity: {overall_severity}")
            print(f"[DriftEngine] Retraining required: "
                  f"{retrain_check['model_retraining_required']}")

        return {
            "reference_month":          self.ref_month,
            "current_month":            self.cur_month,
            "overall_drift_severity":   overall_severity,
            "n_features_tracked":       len(self._numeric_cols),
            "psi_summary":              psi_sum,
            "drift_report":             drift_report,
            "early_warnings":           warnings,
            "retraining_trigger":       retrain_check,
            "drifted_features": [
                d["feature"] for d in drift_report if d["confirmed_drift"]
            ],
        }
