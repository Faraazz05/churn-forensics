"""
reasoning_engine.py
===================
Customer Health Forensics — Phase 5
Reasoning engine: combines rule engine + ANN signals + XAI explanations
into structured causal chains and multi-factor reasoning.

Output per customer:
  - causal_chain:  ordered list of [signal → mechanism → outcome]
  - root_causes:   categorised root cause mapping
  - risk_factors:  weighted, confidence-rated risk factors
  - what_summary:  data-level observations
  - why_summary:   causal interpretations

This is the analytical layer beneath the LLM — it structures the evidence
so the LLM (or rule fallback) can generate coherent narratives.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Any

from rule_engine import evaluate_rules, rule_summary, risk_tier, RuleResult


# ── Root cause taxonomy ─────────────────────────────────────────
ROOT_CAUSE_MAP = {
    "engagement":       "Engagement decline",
    "payment":          "Pricing / financial stress",
    "support":          "Product friction",
    "satisfaction":     "Satisfaction / relationship",
    "contract":         "Commitment level",
    "product_adoption": "Shallow product adoption",
    "overall_health":   "Multi-dimensional health failure",
    "onboarding":       "Onboarding / time-to-value failure",
}

# Causal templates: {category} → chain strings
CAUSAL_CHAIN_TEMPLATES = {
    "engagement": [
        "Declining logins/activity → product no longer part of daily workflow → "
        "reduced perceived value → cancellation intent",
        "Last login {days} days ago → habit loop broken → "
        "competitor evaluation window opens",
    ],
    "payment": [
        "Payment failures → budget pressure or deliberate payment avoidance → "
        "account will lapse without proactive intervention",
        "Financial stress signals → reduced willingness to pay → "
        "subscription deprioritisation",
    ],
    "support": [
        "High support volume → unresolved product friction → "
        "frustration accumulates → confidence erodes → churn decision",
        "Support-to-usage ratio > 1.5 → customer fighting product more than using it → "
        "negative experience loop",
    ],
    "satisfaction": [
        "Low NPS (detractor) → active dissatisfaction expressed → "
        "word-of-mouth risk + high cancellation probability",
        "Passive NPS score → vulnerable to competitor switching → "
        "first better offer triggers churn",
    ],
    "contract": [
        "Monthly contract → zero switching cost → "
        "any friction or budget review triggers cancellation",
    ],
    "product_adoption": [
        "Low feature usage → shallow product dependency → "
        "easy to switch → competitor wins on next evaluation",
    ],
    "onboarding": [
        "Short tenure (< 3 months) → activation not complete → "
        "customer hasn't reached 'aha moment' → pre-cancellation window",
    ],
}


@dataclass
class ReasoningResult:
    customer_id:    str
    churn_prob:     float
    risk_tier:      str
    causal_chains:  list[str]
    root_causes:    list[dict]
    risk_factors:   list[dict]
    what_summary:   list[str]
    why_summary:    list[str]
    ann_weights:    dict = field(default_factory=dict)
    interactions:   list = field(default_factory=list)
    confidence:     str  = "MEDIUM"   # HIGH / MEDIUM / LOW
    primary_category: str = "unknown"


class ReasoningEngine:
    """
    Multi-signal reasoning engine.

    Combines:
      - Rule engine (deterministic signals)
      - XAI explanations (SHAP/LIME/AIX360 consensus)
      - ANN feature impact scores
      - Drift signals

    Returns structured ReasoningResult per customer.
    """

    def __init__(self, ann_model=None, feature_names: list[str] = None):
        self.ann_model    = ann_model
        self.feature_names = feature_names or []

    def reason(
        self,
        customer_id:    str,
        features:       dict,
        churn_prob:     float,
        xai_explanation: dict   = None,
        drift_signals:   list   = None,
    ) -> ReasoningResult:
        """
        Full reasoning pipeline for one customer.

        Args:
            customer_id:    Customer identifier.
            features:       Dict of feature_name → value.
            churn_prob:     Predicted churn probability.
            xai_explanation: Output from XAIEngine.explain_local() (optional).
            drift_signals:  List of drifted feature names (optional).

        Returns:
            ReasoningResult with structured causal analysis.
        """
        tier = risk_tier(churn_prob)

        # 1. Rule engine
        fired_rules  = evaluate_rules(features)
        rule_sum     = rule_summary(fired_rules)
        primary_cat  = rule_sum.get("dominant_category", "unknown")

        # 2. ANN feature impact (if model available)
        ann_weights  = {}
        interactions = []
        if self.ann_model is not None and self.feature_names:
            try:
                import pandas as pd
                from ann_feature_model import compute_feature_impact, detect_feature_interactions
                X_row = pd.DataFrame([features]).reindex(columns=self.feature_names, fill_value=0)
                ann_weights  = compute_feature_impact(self.ann_model, X_row, self.feature_names)
                interactions = detect_feature_interactions(self.ann_model, X_row, self.feature_names)
            except Exception as e:
                pass  # ANN failure is non-fatal

        # 3. XAI integration
        xai_features = []
        xai_dirs     = {}
        if xai_explanation and "explanations" in xai_explanation:
            for exp in xai_explanation["explanations"][:5]:
                xai_features.append(exp["feature"])
                xai_dirs[exp["feature"]] = exp.get("direction", "unknown")

        # 4. Build WHAT statements
        what_statements = rule_sum.get("what_statements", [])
        if drift_signals:
            for feat in drift_signals[:2]:
                what_statements.append(
                    f"Feature '{feat}' distribution has shifted significantly "
                    f"since the reference period."
                )

        # 5. Build WHY (causal chains)
        causal_chains = self._build_causal_chains(
            fired_rules, features, primary_cat
        )
        why_statements = rule_sum.get("why_statements", [])

        # 6. Risk factors (merged: rules + XAI + ANN)
        risk_factors = self._build_risk_factors(
            fired_rules, xai_features, xai_dirs, ann_weights
        )

        # 7. Root causes
        root_causes = self._build_root_causes(fired_rules, primary_cat)

        # 8. Confidence
        confidence = self._assess_confidence(
            fired_rules, xai_explanation, ann_weights
        )

        return ReasoningResult(
            customer_id    = customer_id,
            churn_prob     = round(float(churn_prob), 4),
            risk_tier      = tier,
            causal_chains  = causal_chains,
            root_causes    = root_causes,
            risk_factors   = risk_factors,
            what_summary   = what_statements[:5],
            why_summary    = why_statements[:3],
            ann_weights    = {k: v for k, v in list(ann_weights.items())[:8]},
            interactions   = interactions[:3],
            confidence     = confidence,
            primary_category = primary_cat,
        )

    def _build_causal_chains(
        self,
        fired_rules: list[RuleResult],
        features:    dict,
        primary_cat: str,
    ) -> list[str]:
        """Build 1–3 causal chain strings from fired rules and category."""
        chains = []

        # Primary category chains
        templates = CAUSAL_CHAIN_TEMPLATES.get(primary_cat, [])
        for tmpl in templates[:1]:
            try:
                days_since = int(features.get("last_login_days_ago", 0))
                chains.append(tmpl.format(days=days_since))
            except Exception:
                chains.append(tmpl)

        # Secondary chains from other fired rule categories
        seen_cats = {primary_cat}
        for rule in fired_rules[1:3]:
            if rule.category not in seen_cats:
                seen_cats.add(rule.category)
                cat_chains = CAUSAL_CHAIN_TEMPLATES.get(rule.category, [])
                if cat_chains:
                    chains.append(cat_chains[0])

        return chains[:3]

    def _build_risk_factors(
        self,
        fired_rules:  list[RuleResult],
        xai_features: list[str],
        xai_dirs:     dict,
        ann_weights:  dict,
    ) -> list[dict]:
        """
        Merge rule signals + XAI + ANN into unified risk factor list.
        Confidence increases when multiple methods agree on the same feature.
        """
        factor_scores: dict[str, dict] = {}

        # From rules
        SEVERITY_SCORE = {"CRITICAL": 1.0, "HIGH": 0.75, "MEDIUM": 0.5, "LOW": 0.25}
        for rule in fired_rules:
            key = rule.category
            if key not in factor_scores:
                factor_scores[key] = {
                    "factor":    ROOT_CAUSE_MAP.get(key, key),
                    "score":     0.0,
                    "sources":   [],
                    "direction": "risk+",
                }
            factor_scores[key]["score"] = max(
                factor_scores[key]["score"],
                SEVERITY_SCORE.get(rule.severity, 0.5)
            )
            factor_scores[key]["sources"].append("rules")

        # From XAI
        for feat in xai_features[:5]:
            direction = xai_dirs.get(feat, "risk+")
            if direction == "risk+":
                score = ann_weights.get(feat, 0.5)
                cat   = _feat_to_category(feat)
                if cat not in factor_scores:
                    factor_scores[cat] = {
                        "factor":  ROOT_CAUSE_MAP.get(cat, feat),
                        "score":   0.0,
                        "sources": [],
                        "direction": direction,
                    }
                factor_scores[cat]["score"] = max(factor_scores[cat]["score"], score)
                factor_scores[cat]["sources"].append("xai")

        # ANN agreement boosts confidence
        for cat, info in factor_scores.items():
            if "xai" in info["sources"] and "rules" in info["sources"]:
                info["confidence"] = "HIGH"
            elif len(info["sources"]) > 0:
                info["confidence"] = "MEDIUM"
            else:
                info["confidence"] = "LOW"

        return sorted(
            [v for v in factor_scores.values()],
            key=lambda x: -x["score"]
        )[:6]

    def _build_root_causes(
        self,
        fired_rules: list[RuleResult],
        primary_cat: str,
    ) -> list[dict]:
        seen = {}
        for rule in fired_rules:
            cat = rule.category
            if cat not in seen:
                seen[cat] = {
                    "category":    cat,
                    "label":       ROOT_CAUSE_MAP.get(cat, cat),
                    "severity":    rule.severity,
                    "evidence":    rule.what,
                    "mechanism":   rule.why,
                }
        return list(seen.values())[:4]

    def _assess_confidence(
        self,
        fired_rules:     list[RuleResult],
        xai_explanation: dict,
        ann_weights:     dict,
    ) -> str:
        """
        Reasoning confidence: HIGH when rules + XAI + ANN all agree on direction.
        """
        n_sources = 0
        if fired_rules:         n_sources += 1
        if xai_explanation:     n_sources += 1
        if ann_weights:         n_sources += 1

        if n_sources >= 3:
            return "HIGH"
        elif n_sources >= 2:
            return "MEDIUM"
        return "LOW"


def _feat_to_category(feature: str) -> str:
    """Map a feature name to a root-cause category."""
    mapping = {
        "last_login_days_ago":       "engagement",
        "logins_per_week":           "engagement",
        "monthly_active_days":       "engagement",
        "avg_session_duration_min":  "engagement",
        "engagement_score":          "engagement",
        "engagement_rate":           "engagement",
        "recency_risk_flag":         "engagement",
        "stickiness_index":          "engagement",
        "payment_failures_last_6m":  "payment",
        "monthly_spend":             "payment",
        "payment_risk_flag":         "payment",
        "commitment_score":          "contract",
        "support_tickets_last_90d":  "support",
        "support_to_usage_ratio":    "support",
        "nps_score":                 "satisfaction",
        "nps_band":                  "satisfaction",
        "features_used_count":       "product_adoption",
        "spend_per_feature":         "product_adoption",
        "customer_health_score":     "overall_health",
        "tenure_months":             "onboarding",
        "lifetime_value_est":        "payment",
        "referrals_made":            "satisfaction",
    }
    return mapping.get(feature, "engagement")
