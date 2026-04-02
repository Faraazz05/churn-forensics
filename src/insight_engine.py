"""
insight_engine.py
=================
Customer Health Forensics — Phase 5
Main insight orchestrator.

Combines outputs from all previous phases + ANN + RL + LLM
into a structured intelligence report with 8 sections.

Section structure (mandatory):
  1. Executive Summary
  2. Customer Risk Analysis
  3. Segment Intelligence
  4. Drift & Behavior Analysis
  5. Causal Analysis (WHY)
  6. Predictive Outlook (WHAT NEXT)
  7. Recommended Actions
  8. Business Impact
"""

import json
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from rule_engine     import evaluate_segment_rules, evaluate_drift_rules, risk_tier
from reasoning_engine import ReasoningEngine
from rl_recommender  import RLRecommender, ACTIONS
from llm_pipeline    import LLMPipeline
from prompt_templates import templates


class NumpyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, np.ndarray):    return o.tolist()
        return super().default(o)


def _load(path: Path) -> Any:
    if not path.exists(): return None
    with open(path) as f: return json.load(f)


def _safe(val, default=0):
    return val if val is not None else default


class InsightEngine:
    """
    Phase 5 Insight Engine.

    Loads all previous phase outputs and generates a complete
    executive intelligence report.

    Usage:
        engine = InsightEngine(outputs_dir=Path("outputs"))
        report = engine.run()
    """

    def __init__(
        self,
        outputs_dir: Path,
        models_dir:  Path  = None,
        llm:         LLMPipeline  = None,
        rl:          RLRecommender = None,
        ann_model                 = None,
        feature_names: list       = None,
        verbose:     bool  = True,
    ):
        self.outputs_dir   = Path(outputs_dir)
        self.models_dir    = Path(models_dir) if models_dir else self.outputs_dir.parent / "models"
        self.llm           = llm or LLMPipeline()
        self.rl            = rl  or RLRecommender()
        self.verbose       = verbose

        self._reasoning    = ReasoningEngine(ann_model, feature_names)
        self._data         = {}
        self._load_all()

    def _load_all(self):
        """Load all previous phase outputs."""
        d = self.outputs_dir

        self._data["segments"]   = _load(d / "segmentation/segmentation_results.json") or []
        self._data["insights"]   = _load(d / "segmentation/global_insights.json") or {}
        self._data["drift"]      = _load(d / "drift/drift_report.json") or {}
        self._data["warnings"]   = _load(d / "drift/early_warnings.json") or []
        self._data["retrain"]    = _load(d / "drift/retraining_trigger.json") or {}
        self._data["xai_global"] = _load(d / "xai/global_explanation.json") or {}
        self._data["watchlist"]  = _load(d / "xai/watchlist_reasoning.json") or []
        self._data["confidence"] = _load(d / "xai/confidence_summary.json") or {}
        self._data["intel"]      = _load(d / "phase34_intelligence.json") or {}
        self._data["r_seg"]      = _load(d / "r_outputs/segmentation_plan_type.json") or {}
        self._data["r_drift"]    = _load(d / "r_outputs/drift_validation.json") or {}
        self._data["oct_psi"]    = _load(d / "octave_outputs/psi_validation.json") or {}

        if self.verbose:
            loaded = [k for k,v in self._data.items() if v]
            print(f"[InsightEngine] Loaded: {loaded}")

    # ── Data helpers ───────────────────────────────────────────
    def _overall_churn_rate(self) -> float:
        segs = self._data["segments"]
        if not segs: return 0.0
        rates = [s.get("churn_rate") for s in segs if s.get("churn_rate")]
        return sum(rates) / len(rates) if rates else 0.0

    def _prev_churn_rate(self) -> float:
        segs = self._data["segments"]
        if not segs: return 0.0
        rates = [s.get("previous_churn_rate") for s in segs if s.get("previous_churn_rate")]
        return sum(rates) / len(rates) if rates else self._overall_churn_rate()

    def _top_degrading(self, n=3) -> list:
        return self._data["insights"].get("top_degrading_segments", [])[:n]

    def _early_warning_features(self) -> list[str]:
        return [w["feature"] for w in self._data["warnings"][:5]]

    def _drifted_features(self) -> list[str]:
        return self._data["drift"].get("drifted_features", [])

    def _top_xai_features(self, n=5) -> list[str]:
        return [f.get("feature","—") for f in
                self._data["xai_global"].get("top_features",[])[:n]]

    # ── Section builders ───────────────────────────────────────
    def _build_executive_summary(self) -> str:
        cur   = self._overall_churn_rate()
        prev  = self._prev_churn_rate()
        delta = cur - prev
        top_segs = self._top_degrading(1)
        top_seg  = top_segs[0].get("segment_id","—") if top_segs else "—"
        top_rate = top_segs[0].get("churn_rate",0) * 100 if top_segs else 0

        n_critical = sum(1 for c in self._data["watchlist"]
                         if c.get("churn_probability",0) >= 0.70)
        revenue    = _safe(self._data["insights"].get("total_revenue_at_risk"))

        return self.llm.generate(
            "executive_summary",
            churn_rate              = cur,
            churn_delta             = delta,
            n_critical              = n_critical,
            top_segment             = top_seg,
            top_segment_rate        = top_rate,
            revenue_at_risk         = revenue,
            early_warning_features  = self._early_warning_features(),
            drift_severity          = self._data["drift"].get("overall_drift_severity","—"),
        )

    def _build_customer_risk(self) -> dict:
        watchlist = self._data["watchlist"]

        by_tier = {"Critical": 0, "High": 0, "Medium": 0, "Safe": 0}
        for c in watchlist:
            t = c.get("risk_tier", risk_tier(c.get("churn_probability",0)))
            by_tier[t] = by_tier.get(t, 0) + 1

        top_customers = []
        sorted_wl = sorted(watchlist, key=lambda x: -x.get("churn_probability",0))
        for c in sorted_wl[:10]:
            r   = c.get("reasoning", {})
            why = r.get("why", {})
            top_customers.append({
                "customer_id":       c.get("customer_id"),
                "churn_probability": c.get("churn_probability"),
                "risk_tier":         c.get("risk_tier", "—"),
                "primary_driver":    why.get("primary_driver","—"),
                "primary_category":  why.get("primary_category","—"),
                "top_action":        why.get("recommended_action","—"),
                "what_changed":      r.get("what_changed",[])[0] if r.get("what_changed") else "—",
            })

        conf = self._data["confidence"]
        return {
            "n_customers_analyzed": len(watchlist),
            "risk_distribution":    by_tier,
            "top_at_risk":          top_customers,
            "explanation_trust":    {
                "trust_score": conf.get("trust_score"),
                "HIGH":        conf.get("HIGH"),
                "MEDIUM":      conf.get("MEDIUM"),
                "LOW":         conf.get("LOW"),
            },
        }

    def _build_segment_intelligence(self) -> dict:
        insights  = self._data["insights"]
        segments  = self._data["segments"] if isinstance(self._data["segments"],list) else []
        seg_rules = {s.get("segment_id"):
                     evaluate_segment_rules(s) for s in segments}

        above_bm  = [s.get("segment_id","—") for s in segments
                     if s.get("exceeds_benchmark")]

        narrative = self.llm.generate(
            "segment_intelligence",
            degrading_segments     = [s.get("segment_id") for s in insights.get("top_degrading_segments",[])],
            improving_segments     = [s.get("segment_id") for s in insights.get("top_improving_segments",[])],
            highest_churn_segment  = insights.get("highest_churn_segments",[{}])[0].get("segment_id","—")
                                     if insights.get("highest_churn_segments") else "—",
            highest_churn_rate     = (insights.get("highest_churn_segments",[{}])[0].get("churn_rate",0)*100)
                                     if insights.get("highest_churn_segments") else 0,
            total_revenue_at_risk  = _safe(insights.get("total_revenue_at_risk")),
            above_benchmark        = above_bm[:5],
        )

        # R statistical validation
        r_findings = {}
        r_seg = self._data["r_seg"]
        if r_seg.get("anova"):
            r_findings = {
                "anova_significant": r_seg["anova"].get("significant"),
                "p_value":           r_seg["anova"].get("p_value"),
                "interpretation":    r_seg["anova"].get("interpretation",""),
            }

        return {
            "narrative":          narrative,
            "n_degrading":        insights.get("n_degrading", 0),
            "n_improving":        insights.get("n_improving", 0),
            "n_accelerating":     insights.get("n_accelerating", 0),
            "total_revenue_at_risk": insights.get("total_revenue_at_risk", 0),
            "top_degrading":      insights.get("top_degrading_segments", [])[:5],
            "accelerating":       insights.get("accelerating_risk_segments", []),
            "above_benchmark":    above_bm,
            "r_validation":       r_findings,
        }

    def _build_drift_analysis(self) -> dict:
        drift    = self._data["drift"]
        warnings = self._data["warnings"]
        retrain  = self._data["retrain"]

        drift_rules = evaluate_drift_rules(drift.get("drift_report",[]))

        # Octave validation
        oct_summary = {}
        oct = self._data["oct_psi"]
        if oct:
            oct_summary = {
                "agreement_rate":    oct.get("agreement_rate"),
                "validation_passed": oct.get("validation_passed"),
            }

        # R drift validation
        r_drift_summary = {}
        r_d = self._data["r_drift"]
        if r_d.get("summary"):
            r_drift_summary = r_d["summary"]

        return {
            "overall_severity":       drift.get("overall_drift_severity","—"),
            "n_features_tracked":     drift.get("n_features_tracked",0),
            "drifted_features":       drift.get("drifted_features",[]),
            "early_warning_features": [w["feature"] for w in warnings],
            "early_warnings_detail":  warnings[:8],
            "retraining": {
                "required": retrain.get("model_retraining_required", False),
                "reason":   retrain.get("reason","—"),
                "features": retrain.get("features_above_threshold",[]),
            },
            "rule_assessment":    drift_rules,
            "octave_validation":  oct_summary,
            "r_validation":       r_drift_summary,
        }

    def _build_causal_analysis(self) -> dict:
        top_feats    = self._top_xai_features()
        drifted      = self._drifted_features()
        r_seg        = self._data["r_seg"]
        rule_cats    = list({s.get("health_status","")
                             for s in self._data["segments"]
                             if s.get("health_status") == "degrading"})

        r_findings_str = ""
        if r_seg.get("anova",{}).get("interpretation"):
            r_findings_str = r_seg["anova"]["interpretation"]

        seg_patterns = ", ".join(
            s.get("segment_id","—") + f"(+{s.get('churn_delta',0):.2f})"
            for s in self._top_degrading(3)
        ) or "no clear segment pattern"

        narrative = self.llm.generate(
            "causal_analysis",
            top_features     = top_feats,
            drifted_features = drifted[:5],
            rule_categories  = ["engagement","payment","support","satisfaction"],
            segment_patterns = seg_patterns,
            r_findings       = r_findings_str or "R validation pending",
        )

        # Build causal chain from top watchlist customer
        sample_chains = []
        for c in self._data["watchlist"][:2]:
            r = c.get("reasoning",{})
            if r.get("why",{}).get("primary_why"):
                sample_chains.append({
                    "customer_id":  c.get("customer_id"),
                    "primary":      r["why"].get("primary_driver","—"),
                    "mechanism":    r["why"].get("primary_why","—"),
                })

        return {
            "narrative":       narrative,
            "top_xai_drivers": self._data["xai_global"].get("top_features",[])[:8],
            "causal_chains":   sample_chains,
            "root_cause_categories": ["Engagement decline","Financial stress",
                                      "Product friction","Satisfaction issues"],
        }

    def _build_predictive_outlook(self) -> dict:
        insights    = self._data["insights"]
        drift       = self._data["drift"]
        accel_segs  = [s.get("segment_id","—") for s in
                       insights.get("accelerating_risk_segments",[])]
        declining   = self._early_warning_features()

        velocity = "stable"
        segs_with_delta = [s for s in self._data["segments"] if s.get("churn_delta")]
        if segs_with_delta:
            avg_delta = sum(s["churn_delta"] for s in segs_with_delta) / len(segs_with_delta)
            if avg_delta > 0.05:  velocity = "increasing"
            elif avg_delta < -0.03: velocity = "decreasing"

        high_drift = [f for f in drift.get("drift_report",[])
                      if f.get("drift_severity") == "HIGH"][:4]

        narrative = self.llm.generate(
            "predictive_outlook",
            current_churn_rate   = self._overall_churn_rate(),
            velocity             = velocity,
            accelerating_segments = accel_segs[:3],
            declining_indicators  = declining[:4],
            retrain_required      = drift.get("retraining_trigger",{}).get("model_retraining_required",False),
            high_drift_features   = [f.get("feature","—") for f in high_drift],
        )

        return {
            "narrative":           narrative,
            "churn_velocity":      velocity,
            "accelerating_segments": accel_segs,
            "high_risk_indicators": declining,
            "retrain_flag":        drift.get("retraining_trigger",{}).get("model_retraining_required",False),
        }

    def _build_recommendations(self) -> list[dict]:
        insights     = self._data["insights"]
        drift        = self._data["drift"]
        top_deg      = self._top_degrading(1)
        top_seg      = top_deg[0].get("segment_id","—") if top_deg else "—"
        top_drivers  = self._top_xai_features(3)
        n_critical   = sum(1 for c in self._data["watchlist"]
                           if c.get("churn_probability",0) >= 0.70)
        warnings     = self._early_warning_features()

        # RL recommendations
        primary_cat  = "engagement"
        if top_drivers:
            from reasoning_engine import _feat_to_category
            primary_cat = _feat_to_category(top_drivers[0])

        rl_recs      = self.rl.recommend("Critical", primary_cat, top_k=3)
        rl_actions   = [r["description"] for r in rl_recs]
        top_rl       = rl_recs[0]["description"] if rl_recs else "—"

        # Rule top action
        rule_action = "Immediate customer success review"
        for seg in self._data["segments"][:1]:
            seg_rule = evaluate_segment_rules(seg)
            if seg_rule["actions"]:
                rule_action = seg_rule["actions"][0]

        narrative = self.llm.generate(
            "recommendations",
            top_segment    = top_seg,
            top_drivers    = top_drivers,
            n_critical     = n_critical,
            rl_actions     = rl_actions,
            revenue_at_risk = _safe(insights.get("total_revenue_at_risk")),
            early_warnings  = warnings[:3],
            rule_action     = rule_action,
        )

        # Structure into ranked list
        recommendations = []
        lines = [l.strip() for l in narrative.split("\n") if l.strip()]
        for i, line in enumerate(lines[:5], 1):
            recommendations.append({
                "rank":        i,
                "description": line,
                "target":      top_seg if i == 1 else f"High-risk customers (n={n_critical})",
                "source":      "llm" if self.llm.is_llm_active else "rules+rl",
            })

        # Always include RL top action
        if rl_recs:
            recommendations.append({
                "rank":        len(recommendations) + 1,
                "description": f"[RL-optimised] {top_rl}",
                "target":      f"{primary_cat} risk customers",
                "source":      "rl",
                "q_value":     rl_recs[0].get("q_value"),
            })

        return recommendations

    def _build_business_impact(self) -> dict:
        insights = self._data["insights"]
        segs     = self._data["segments"] if isinstance(self._data["segments"],list) else []
        wl       = self._data["watchlist"]

        total_rev = _safe(insights.get("total_revenue_at_risk"))
        n_crit    = sum(1 for c in wl if c.get("churn_probability",0) >= 0.70)
        n_high    = sum(1 for c in wl if 0.5 <= c.get("churn_probability",0) < 0.70)

        # Estimate: 30% of at-risk customers saved with good intervention
        SAVE_RATE        = 0.30
        avg_spend_annual = 0
        if segs:
            spends = [s.get("avg_monthly_spend",0) for s in segs if s.get("avg_monthly_spend")]
            if spends: avg_spend_annual = (sum(spends)/len(spends)) * 12

        potential_recovery = total_rev * SAVE_RATE

        return {
            "total_annual_revenue_at_risk": round(total_rev, 2),
            "projected_loss_if_no_action":  round(total_rev * 0.60, 2),
            "potential_recovery":            round(potential_recovery, 2),
            "recovery_assumption":           f"{SAVE_RATE:.0%} save rate with targeted actions",
            "critical_customers_count":      n_crit,
            "high_risk_customers_count":     n_high,
            "avg_annual_customer_value":     round(avg_spend_annual, 2),
            "n_degrading_segments":          insights.get("n_degrading",0),
        }

    # ── Full report ────────────────────────────────────────────
    def run(self, save_path: Path = None) -> dict:
        """
        Generate the complete Phase 5 intelligence report.

        Returns:
            Report dict (8 sections, JSON serializable).
        """
        t0 = time.time()
        print(f"\n[InsightEngine] Generating intelligence report "
              f"(LLM: {self.llm.active_mode})...")

        report = {
            "generated_at":    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "llm_mode":        self.llm.active_mode,
            "executive_summary": self._build_executive_summary(),
            "customer_risk":     self._build_customer_risk(),
            "segments":          self._build_segment_intelligence(),
            "drift_analysis":    self._build_drift_analysis(),
            "causal_analysis":   self._build_causal_analysis(),
            "prediction_outlook": self._build_predictive_outlook(),
            "recommendations":   self._build_recommendations(),
            "business_impact":   self._build_business_impact(),
            "runtime_seconds":   round(time.time() - t0, 2),
        }

        if save_path:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w") as f:
                json.dump(report, f, indent=2, cls=NumpyEncoder)
            print(f"[InsightEngine] Report saved → {save_path}")

        return report
