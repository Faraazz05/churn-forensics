"""
segmentation_engine.py
======================
Customer Health Forensics System — Phase 3
Python segmentation engine.

Segments by: plan_type, region, contract_type, behavior_tier, nps_band_label.
Computes temporal degradation, acceleration detection, and benchmark flags.
"""

import numpy as np
import pandas as pd
from pathlib import Path

SEGMENT_DIMENSIONS   = ["plan_type", "region", "contract_type", "behavior_tier", "nps_band_label"]
DEGRADING_THRESHOLD  =  0.10
IMPROVING_THRESHOLD  = -0.05
SAAS_BENCHMARK       =  0.085
MIN_SEGMENT_SIZE     =  50


def add_segment_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "engagement_score" in df.columns and "behavior_tier" not in df.columns:
        df["behavior_tier"] = pd.qcut(
            df["engagement_score"], q=4,
            labels=["Q1_low","Q2_mid_low","Q3_mid_high","Q4_high"],
            duplicates="drop",
        ).astype(str)

    if "nps_band_label" not in df.columns:
        if "nps_band" in df.columns:
            df["nps_band_label"] = df["nps_band"].map({0:"detractor",1:"passive",2:"promoter"}).fillna("unknown")
        elif "nps_score" in df.columns:
            df["nps_band_label"] = pd.cut(
                df["nps_score"], bins=[-0.1,6.0,8.0,10.1],
                labels=["detractor","passive","promoter"],
            ).astype(str)
    return df


def _segment_metrics(df_seg: pd.DataFrame, spend_col: str = "monthly_spend") -> dict:
    n = len(df_seg)
    if n == 0:
        return {"segment_size": 0}
    churn    = float(df_seg["churned"].mean()) if "churned" in df_seg.columns else None
    avg_spend = float(df_seg[spend_col].mean()) if spend_col in df_seg.columns else 0.0
    n_churn  = int(df_seg["churned"].sum()) if "churned" in df_seg.columns else 0
    return {
        "segment_size":        n,
        "churn_rate":          round(churn, 4) if churn is not None else None,
        "n_churners":          n_churn,
        "avg_monthly_spend":   round(avg_spend, 2),
        "revenue_at_risk":     round(n_churn * avg_spend * 12, 2),
    }


def _temporal(current: float, previous: float, history: list = None) -> dict:
    delta = current - previous
    if delta > DEGRADING_THRESHOLD:   status = "degrading"
    elif delta < IMPROVING_THRESHOLD: status = "improving"
    else:                              status = "stable"

    abs_d = abs(delta)
    if abs_d > 0.15:    vel_mag = "high"
    elif abs_d > 0.05:  vel_mag = "medium"
    else:               vel_mag = "low"

    accel = "normal"
    if history and len(history) >= 2:
        deltas = [history[i+1] - history[i] for i in range(len(history)-1)]
        if all(d > 0 for d in deltas) and delta > 0:
            accel = "accelerating_risk"
        elif all(d < 0 for d in deltas) and delta < 0:
            accel = "decelerating"

    risk = "low"
    if current > 0.30 or (status == "degrading" and current > 0.20): risk = "high"
    elif current > 0.15 or status == "degrading": risk = "medium"

    return {
        "previous_churn_rate":  round(previous, 4),
        "churn_delta":          round(delta, 4),
        "velocity":             "increasing" if delta > 0 else ("decreasing" if delta < 0 else "stable"),
        "velocity_magnitude":   vel_mag,
        "health_status":        status,
        "risk_level":           risk,
        "acceleration":         accel,
    }


def _benchmark(churn_rate: float) -> dict:
    above = churn_rate > SAAS_BENCHMARK
    return {
        "exceeds_benchmark": above,
        "benchmark_note": (
            f"Churn {churn_rate:.1%} exceeds SaaS benchmark ({SAAS_BENCHMARK:.1%})."
            if above else
            f"Churn {churn_rate:.1%} within SaaS benchmark."
        ),
    }


class SegmentationEngine:
    def __init__(self, df_current, df_previous=None, df_history=None, verbose=True):
        self.df_current  = add_segment_dimensions(df_current)
        self.df_previous = add_segment_dimensions(df_previous) if df_previous is not None else None
        self.df_history  = {k: add_segment_dimensions(v) for k, v in df_history.items()} if df_history else {}
        self.verbose     = verbose
        self.dimensions  = [d for d in SEGMENT_DIMENSIONS if d in self.df_current.columns]

    def _analyze_dimension(self, dim: str) -> list[dict]:
        results = []
        for val in sorted(self.df_current[dim].dropna().unique()):
            seg = self.df_current[self.df_current[dim] == val]
            if len(seg) < MIN_SEGMENT_SIZE: continue
            metrics = _segment_metrics(seg)
            if metrics.get("churn_rate") is None: continue

            result = {
                "segment_id": f"{dim}={val}",
                "dimension":  dim,
                "value":      str(val),
                **metrics,
            }

            if self.df_previous is not None and dim in self.df_previous.columns:
                prev_seg = self.df_previous[self.df_previous[dim] == val]
                if len(prev_seg) >= MIN_SEGMENT_SIZE:
                    prev_m = _segment_metrics(prev_seg)
                    if prev_m.get("churn_rate") is not None:
                        hist_rates = []
                        for m, df_h in sorted(self.df_history.items()):
                            if dim in df_h.columns:
                                hs = df_h[df_h[dim] == val]
                                if len(hs) >= MIN_SEGMENT_SIZE:
                                    hm = _segment_metrics(hs)
                                    if hm.get("churn_rate") is not None:
                                        hist_rates.append(hm["churn_rate"])
                        result.update(_temporal(metrics["churn_rate"], prev_m["churn_rate"], hist_rates))
            else:
                result["health_status"] = "no_comparison"

            result.update(_benchmark(metrics["churn_rate"]))
            results.append(result)
        return results

    def run(self) -> dict:
        all_segs = []
        by_dim   = {}
        for dim in self.dimensions:
            segs = self._analyze_dimension(dim)
            by_dim[dim] = segs
            all_segs.extend(segs)
            if self.verbose:
                n_deg = sum(1 for s in segs if s.get("health_status") == "degrading")
                print(f"  {dim:20s} {len(segs):3d} segments | {n_deg} degrading")

        degrading    = sorted([s for s in all_segs if s.get("health_status") == "degrading"],
                               key=lambda x: -x.get("churn_delta", 0))
        improving    = sorted([s for s in all_segs if s.get("health_status") == "improving"],
                               key=lambda x: x.get("churn_delta", 0))
        accelerating = [s for s in all_segs if s.get("acceleration") == "accelerating_risk"]

        return {
            "n_segments_analyzed": len(all_segs),
            "dimensions_analyzed": self.dimensions,
            "segments":            all_segs,
            "by_dimension":        by_dim,
            "global_insights": {
                "top_degrading_segments":     degrading[:3],
                "top_improving_segments":     improving[:3],
                "accelerating_risk_segments": accelerating,
                "total_revenue_at_risk":      round(sum(s.get("revenue_at_risk", 0) for s in all_segs), 2),
                "n_degrading":   sum(1 for s in all_segs if s.get("health_status") == "degrading"),
                "n_improving":   sum(1 for s in all_segs if s.get("health_status") == "improving"),
                "n_stable":      sum(1 for s in all_segs if s.get("health_status") == "stable"),
                "n_accelerating": len(accelerating),
            },
        }


def build_from_snapshots(df_snapshots, current_month=None, previous_month=None,
                         n_history=6, **kwargs) -> SegmentationEngine:
    months  = sorted(df_snapshots["snapshot_month"].unique())
    cur_m   = current_month  or months[-1]
    prev_m  = previous_month or (cur_m - 1)
    df_cur  = df_snapshots[df_snapshots["snapshot_month"] == cur_m].copy()
    df_prev = df_snapshots[df_snapshots["snapshot_month"] == prev_m].copy() \
              if prev_m in months else None
    hist_months = [m for m in months if m < prev_m][-n_history:]
    df_history  = {m: df_snapshots[df_snapshots["snapshot_month"] == m].copy()
                   for m in hist_months}
    return SegmentationEngine(df_cur, df_prev, df_history, **kwargs)
