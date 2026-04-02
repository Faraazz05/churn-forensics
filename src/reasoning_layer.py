"""
reasoning_layer.py
==================
Customer Health Forensics System — Phase 2
Business Reasoning Layer — WHAT happened + WHY it caused churn risk.

This layer sits on top of raw XAI explanations.
It does NOT re-explain — it interprets the XAI output into human language.

Two question types answered:
  WHAT → data-level evidence (observable, factual)
  WHY  → interpretation (causal reasoning, business context)

Supports:
  Per-customer:
    - WHAT changed in their behaviour
    - WHY they are at churn risk
  Population-level:
    - WHAT behavioral patterns are declining
    - WHY churn is increasing in a segment
    - WHAT changed since last period (drift)
    - WHY a specific segment is degrading

Design principle:
  Clarity > complexity.
  Every output must be readable by a non-technical founder or CSM.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any


# ── Feature → Business concept mappings ───────────────────────────────────
# Each feature maps to:
#   label:    human-readable feature name
#   category: high-level churn driver category
#   what_template: how to describe a CHANGE in this feature
#   why_text: why this drives churn risk

FEATURE_BUSINESS_MAP: dict[str, dict] = {
    "last_login_days_ago": {
        "label":    "Days since last login",
        "category": "Inactivity",
        "what_risk_template":  "Customer has not logged in for {value:.0f} days",
        "what_safe_template":  "Customer logged in {value:.0f} days ago (recent)",
        "why":      "Extended inactivity is the strongest leading indicator of churn — "
                    "customers who stop using the product stop seeing value from it.",
    },
    "logins_per_week": {
        "label":    "Weekly logins",
        "category": "Engagement decline",
        "what_risk_template":  "Weekly login frequency has dropped to {value:.1f} sessions",
        "what_safe_template":  "Customer is logging in {value:.1f} times per week (healthy)",
        "why":      "Declining login frequency means the product has lost its habit "
                    "loop — customers who don't form routines around a product will cancel.",
    },
    "monthly_active_days": {
        "label":    "Monthly active days",
        "category": "Engagement decline",
        "what_risk_template":  "Active only {value:.0f} of 30 days this month",
        "what_safe_template":  "Active {value:.0f} days this month",
        "why":      "Low monthly active days shows the product isn't part of the "
                    "customer's regular workflow.",
    },
    "support_tickets_last_90d": {
        "label":    "Support tickets (90 days)",
        "category": "Friction & dissatisfaction",
        "what_risk_template":  "Raised {value:.0f} support tickets in the last 90 days",
        "what_safe_template":  "Low support contact ({value:.0f} tickets in 90 days)",
        "why":      "High support volume signals unresolved friction or product confusion. "
                    "Customers who repeatedly hit blockers lose confidence in the product.",
    },
    "payment_failures_last_6m": {
        "label":    "Payment failures (6 months)",
        "category": "Financial stress",
        "what_risk_template":  "{value:.0f} payment failure(s) in the last 6 months",
        "what_safe_template":  "No payment issues in the last 6 months",
        "why":      "Payment failures correlate strongly with budget pressure or "
                    "deliberate cancellation intent — customers who can't or won't pay are at risk.",
    },
    "nps_score": {
        "label":    "NPS score",
        "category": "Satisfaction",
        "what_risk_template":  "NPS score is {value:.1f}/10 (detractor range)",
        "what_safe_template":  "NPS score is {value:.1f}/10",
        "why":      "Low NPS indicates active dissatisfaction. Detractors are significantly "
                    "more likely to churn and less likely to respond to retention campaigns.",
    },
    "features_used_count": {
        "label":    "Features used",
        "category": "Product adoption",
        "what_risk_template":  "Using only {value:.0f} product features",
        "what_safe_template":  "Actively using {value:.0f} product features",
        "why":      "Narrow feature usage signals shallow adoption. "
                    "Customers using few features are vulnerable to competitor switching.",
    },
    "avg_session_duration_min": {
        "label":    "Average session duration",
        "category": "Engagement depth",
        "what_risk_template":  "Average session is only {value:.0f} minutes",
        "what_safe_template":  "Average session is {value:.0f} minutes",
        "why":      "Short sessions suggest the customer isn't finding value or "
                    "getting work done in the product — browsing rather than using.",
    },
    "monthly_spend": {
        "label":    "Monthly spend",
        "category": "Revenue signal",
        "what_risk_template":  "Monthly spend is ${value:.2f}",
        "what_safe_template":  "Monthly spend is ${value:.2f}",
        "why":      "Spend level affects churn sensitivity — lower-spend customers "
                    "have less switching cost and cancel more readily.",
    },
    "tenure_months": {
        "label":    "Customer tenure",
        "category": "Loyalty",
        "what_risk_template":  "Customer has only been active for {value:.0f} months",
        "what_safe_template":  "Customer has been active for {value:.0f} months",
        "why":      "Short tenure customers haven't built product dependency yet — "
                    "they are more likely to try alternatives.",
    },
    "engagement_score": {
        "label":    "Engagement score",
        "category": "Engagement decline",
        "what_risk_template":  "Overall engagement score is {value:.2f}/1.0 (low)",
        "what_safe_template":  "Engagement score is {value:.2f}/1.0",
        "why":      "Composite engagement below 0.4 consistently predicts near-term churn.",
    },
    "stickiness_index": {
        "label":    "Stickiness index",
        "category": "Trapped customer risk",
        "what_risk_template":  "High tenure but low engagement — stickiness score {value:.2f}",
        "what_safe_template":  "Stickiness index is {value:.2f}",
        "why":      "High stickiness with low engagement flags 'trapped' customers "
                    "who stay due to switching costs but will leave at contract renewal.",
    },
    "customer_health_score": {
        "label":    "Customer health score",
        "category": "Overall health",
        "what_risk_template":  "Customer health score is {value:.0f}/100 (at risk)",
        "what_safe_template":  "Customer health score is {value:.0f}/100",
        "why":      "The composite health score aggregates engagement, recency, "
                    "payment health and satisfaction into a single actionable signal.",
    },
    "payment_risk_flag": {
        "label":    "Payment risk flag",
        "category": "Financial stress",
        "what_risk_template":  "Payment risk flag is active (2+ failures)",
        "what_safe_template":  "No payment risk flag",
        "why":      "Binary flag for customers showing active financial stress. "
                    "Immediate intervention is typically required.",
    },
    "recency_risk_flag": {
        "label":    "Recency risk flag",
        "category": "Inactivity",
        "what_risk_template":  "Recency risk flag active — inactive for 3+ weeks",
        "what_safe_template":  "No recency risk flag",
        "why":      "Three weeks of inactivity is the empirical threshold after which "
                    "re-engagement success rates drop sharply.",
    },
    "referrals_made": {
        "label":    "Referrals made",
        "category": "Advocacy",
        "what_risk_template":  "Made only {value:.0f} referrals (low advocacy)",
        "what_safe_template":  "Has made {value:.0f} referrals (promoter behaviour)",
        "why":      "Customers who refer others are deeply invested in the product — "
                    "low referral count signals passive or disengaged users.",
    },
    "support_to_usage_ratio": {
        "label":    "Support-to-usage ratio",
        "category": "Friction & dissatisfaction",
        "what_risk_template":  "High support-to-usage ratio: {value:.2f}",
        "what_safe_template":  "Low support-to-usage ratio: {value:.2f}",
        "why":      "A high ratio means the customer is contacting support almost as "
                    "often as they use the product — classic signal of a frustrated user.",
    },
    "spend_per_active_day": {
        "label":    "Spend per active day",
        "category": "Value extraction",
        "what_risk_template":  "Spend per active day is ${value:.2f} — low value extraction",
        "what_safe_template":  "Spend per active day is ${value:.2f}",
        "why":      "Customers who spend a lot relative to days they use the product "
                    "perceive low value-for-money and are price-sensitive churn risks.",
    },
    "commitment_score": {
        "label":    "Contract commitment",
        "category": "Commitment level",
        "what_risk_template":  "Monthly contract — low switching barrier",
        "what_safe_template":  "Annual contract — high switching barrier",
        "why":      "Monthly contracts have zero financial penalty for cancellation — "
                    "they churn at approximately double the rate of annual contracts.",
    },
    "nps_band": {
        "label":    "NPS band",
        "category": "Satisfaction",
        "what_risk_template":  "In detractor NPS band (score 0–6)",
        "what_safe_template":  "In {value} NPS band",
        "why":      "Detractors are actively dissatisfied — they are not just churn risks "
                    "but also potential sources of negative word-of-mouth.",
    },
    "lifetime_value_est": {
        "label":    "Estimated lifetime value",
        "category": "Revenue signal",
        "what_risk_template":  "Estimated LTV is ${value:.0f}",
        "what_safe_template":  "Estimated LTV is ${value:.0f}",
        "why":      "LTV context quantifies the revenue impact of losing this customer — "
                    "high-LTV churns warrant immediate personal outreach.",
    },
}

# Risk thresholds for WHAT direction classification per feature
RISK_THRESHOLDS: dict[str, dict] = {
    "last_login_days_ago":       {"high_risk_above": 21},
    "logins_per_week":           {"high_risk_below": 2.0},
    "monthly_active_days":       {"high_risk_below": 10},
    "support_tickets_last_90d":  {"high_risk_above": 3},
    "payment_failures_last_6m":  {"high_risk_above": 1},
    "nps_score":                 {"high_risk_below": 6.0},
    "features_used_count":       {"high_risk_below": 3},
    "avg_session_duration_min":  {"high_risk_below": 5.0},
    "engagement_score":          {"high_risk_below": 0.3},
    "customer_health_score":     {"high_risk_below": 40.0},
    "stickiness_index":          {"high_risk_below": 0.3},
    "payment_risk_flag":         {"high_risk_above": 0},
    "recency_risk_flag":         {"high_risk_above": 0},
}

# Churn risk category → recommended action
CATEGORY_ACTIONS: dict[str, str] = {
    "Inactivity":               "Trigger a re-engagement campaign with personalised "
                                "login incentive. Target users inactive 14–30 days.",
    "Engagement decline":       "Send a 'tips & highlights' email showing features "
                                "they haven't discovered yet. Schedule a check-in call.",
    "Friction & dissatisfaction": "Escalate open tickets to senior support. "
                                  "Book a customer success call within 48 hours.",
    "Financial stress":         "Proactively reach out to offer payment plan or "
                                "temporary downgrade. Do not let payment failures cascade.",
    "Product adoption":         "Assign an onboarding specialist. Send feature education "
                                "sequence targeting unused high-value features.",
    "Satisfaction":             "Reach out personally to understand root cause of "
                                "low NPS. Offer a product review session.",
    "Trapped customer risk":    "Flag for pre-renewal outreach 60 days before contract end. "
                                "Position value-added features before renewal conversation.",
    "Commitment level":         "Offer annual plan discount. Frame as cost saving, not commitment.",
    "Engagement depth":         "Send 'power user tips' content. Show ROI reports for their account.",
    "Revenue signal":           "High-value customer — prioritise for dedicated CSM.",
    "Advocacy":                 "Invite to referral program. Ask for case study or testimonial.",
    "Value extraction":         "Send ROI summary report. Show what similar customers achieved.",
    "Overall health":           "Flag for immediate customer success review.",
    "Loyalty":                  "Trigger new-customer success programme. "
                                "Assign onboarding check-in for first 90 days.",
}


# ── WHAT/WHY builders ─────────────────────────────────────────────────────
def _what_statement(feat: str, value: float, direction: str) -> str:
    """Generate a WHAT statement: factual description of the feature value."""
    mapping = FEATURE_BUSINESS_MAP.get(feat)
    if not mapping:
        return f"{feat} = {value:.4f} ({'risk driver' if direction == 'risk+' else 'protective'})"

    if direction == "risk+":
        tmpl = mapping.get("what_risk_template", "{label} is concerning: {value:.2f}")
    else:
        tmpl = mapping.get("what_safe_template", "{label} value: {value:.2f}")

    try:
        return tmpl.format(value=value, label=mapping["label"])
    except (KeyError, ValueError):
        return f"{mapping['label']}: {value}"


def _why_statement(feat: str) -> str:
    """Generate a WHY statement: causal business interpretation."""
    mapping = FEATURE_BUSINESS_MAP.get(feat)
    if not mapping:
        return f"Feature '{feat}' is influencing the churn risk prediction."
    return mapping.get("why", "This feature significantly impacts churn risk.")


def _get_category(feat: str) -> str:
    mapping = FEATURE_BUSINESS_MAP.get(feat)
    return mapping["category"] if mapping else "Other"


def _get_action(category: str) -> str:
    return CATEGORY_ACTIONS.get(category, "Review customer account and contact CSM.")


# ── Per-customer reasoning ─────────────────────────────────────────────────
def build_customer_reasoning(
    explanation:   dict,
    X_row:         pd.DataFrame,
    top_n:         int = 5,
) -> dict:
    """
    Build the full WHAT + WHY reasoning block for a single customer.

    Args:
        explanation: Output from XAIEngine.explain_local()
        X_row:       Single-row DataFrame with feature values
        top_n:       How many drivers to include in the reasoning

    Returns:
        Complete customer reasoning dict (strict output format)
    """
    cid        = explanation["customer_id"]
    churn_prob = explanation["churn_probability"]
    exps       = explanation.get("explanations", [])

    # ── Risk tier ─────────────────────────────────────────────────────────
    if churn_prob >= 0.70:
        risk_tier = "Critical"
    elif churn_prob >= 0.50:
        risk_tier = "High"
    elif churn_prob >= 0.30:
        risk_tier = "Medium"
    else:
        risk_tier = "Safe"

    # ── Take top-N risk+ features for WHAT statements ─────────────────────
    risk_features  = [e for e in exps if e["direction"] == "risk+"][:top_n]
    safe_features  = [e for e in exps if e["direction"] == "risk-"][:2]

    what_changed = []
    for exp in risk_features:
        feat = exp["feature"]
        val  = float(X_row[feat].values[0]) if feat in X_row.columns else 0.0
        what_changed.append(_what_statement(feat, val, "risk+"))

    # ── Primary + secondary drivers ────────────────────────────────────────
    primary_feat   = risk_features[0]["feature"] if risk_features else None
    secondary_feat = risk_features[1]["feature"] if len(risk_features) > 1 else None

    primary_category   = _get_category(primary_feat)   if primary_feat   else "Unknown"
    secondary_category = _get_category(secondary_feat) if secondary_feat else None

    primary_driver   = FEATURE_BUSINESS_MAP.get(primary_feat, {}).get("label", primary_feat)
    secondary_driver = (FEATURE_BUSINESS_MAP.get(secondary_feat, {}).get("label", secondary_feat)
                        if secondary_feat else None)

    # ── Protective factors ─────────────────────────────────────────────────
    protective_factors = []
    for exp in safe_features:
        feat = exp["feature"]
        val  = float(X_row[feat].values[0]) if feat in X_row.columns else 0.0
        protective_factors.append(_what_statement(feat, val, "risk-"))

    # ── WHY block ─────────────────────────────────────────────────────────
    why_primary   = _why_statement(primary_feat)   if primary_feat   else "Multiple risk signals detected."
    why_secondary = _why_statement(secondary_feat) if secondary_feat else None

    why = {
        "primary_driver":   primary_driver,
        "primary_category": primary_category,
        "primary_why":      why_primary,
        "recommended_action": _get_action(primary_category),
    }
    if secondary_driver:
        why["secondary_driver"]   = secondary_driver
        why["secondary_category"] = secondary_category
        why["secondary_why"]      = why_secondary

    # ── High-confidence drivers ────────────────────────────────────────────
    high_conf = [e["feature"] for e in exps if e["confidence"] == "HIGH"]

    return {
        "customer_id":       cid,
        "churn_probability": churn_prob,
        "risk_tier":         risk_tier,
        "reasoning": {
            "what_changed":         what_changed,
            "protective_factors":   protective_factors,
            "why":                  why,
            "high_confidence_drivers": high_conf,
        },
        "explanations": exps,  # raw feature-level scores
    }


# ── Population-level reasoning ─────────────────────────────────────────────
def build_global_reasoning(
    global_explanation:   dict,
    df:                   pd.DataFrame,
    segment_col:          str  = None,
    segment_val:          str  = None,
    top_n:                int  = 5,
) -> dict:
    """
    WHAT + WHY at the population or segment level.

    Args:
        global_explanation: Output from XAIEngine.explain_global()
        df:                 Full DataFrame with churn labels + features
        segment_col:        Column to filter by (e.g. "plan_type")
        segment_val:        Value to filter on (e.g. "pro")
        top_n:              Number of global drivers to explain

    Returns:
        Population-level reasoning dict
    """
    top_features = global_explanation.get("top_features", [])[:top_n]

    # Segment filter
    if segment_col and segment_val and segment_col in df.columns:
        df_seg = df[df[segment_col] == segment_val]
        context = f"{segment_col}={segment_val}"
    else:
        df_seg = df
        context = "all customers"

    churn_rate = float(df_seg["churned"].mean()) if "churned" in df_seg.columns else None

    # ── WHAT: global pattern descriptions ─────────────────────────────────
    what_patterns = []
    for exp in top_features:
        feat = exp["feature"]
        direction = exp.get("direction", "unknown")
        mapping = FEATURE_BUSINESS_MAP.get(feat, {})
        label = mapping.get("label", feat)
        category = mapping.get("category", "Other")

        if direction == "risk+":
            what_patterns.append(
                f"'{label}' is the #{len(what_patterns)+1} driver increasing churn risk "
                f"across {context}."
            )
        else:
            what_patterns.append(
                f"'{label}' is acting as a protective factor against churn in {context}."
            )

    # ── WHY: category-level explanations ──────────────────────────────────
    seen_categories = set()
    why_explanations = []
    actions = []

    for exp in top_features:
        feat = exp["feature"]
        if exp.get("direction") != "risk+":
            continue
        cat = _get_category(feat)
        if cat not in seen_categories:
            seen_categories.add(cat)
            why_explanations.append({
                "category":  cat,
                "why":       _why_statement(feat),
                "action":    _get_action(cat),
            })
            actions.append(_get_action(cat))

    return {
        "context":      context,
        "churn_rate":   round(churn_rate, 4) if churn_rate else None,
        "method":       global_explanation.get("method"),
        "sample_size":  global_explanation.get("sample_size"),
        "reasoning": {
            "what_patterns":     what_patterns,
            "why_explanations":  why_explanations,
            "top_actions":       actions[:3],
        },
        "top_global_features": top_features,
    }


# ── Drift reasoning ────────────────────────────────────────────────────────
def build_drift_reasoning(
    drift_report:     dict,
    reference_period: str,
    current_period:   str,
) -> dict:
    """
    WHAT changed over time + WHY churn risk shifted.

    Args:
        drift_report:     Output from Phase 4 drift detection engine.
                          Expected: {"drifted_features": [...], "psi_scores": {...},
                                     "ks_results": {...}, "severity": "HIGH/MEDIUM/LOW"}
        reference_period: e.g. "Month 7" or "2024-Q3"
        current_period:   e.g. "Month 12" or "2025-Q1"

    Returns:
        Drift reasoning dict with WHAT changed and WHY it matters for churn.
    """
    drifted_feats = drift_report.get("drifted_features", [])
    psi_scores    = drift_report.get("psi_scores", {})
    severity      = drift_report.get("severity", "UNKNOWN")

    what_changed = []
    why_matters  = []
    categories   = set()

    for feat in drifted_feats:
        psi = psi_scores.get(feat, 0)
        mapping = FEATURE_BUSINESS_MAP.get(feat, {})
        label   = mapping.get("label", feat)
        cat     = mapping.get("category", "Other")
        categories.add(cat)

        # PSI interpretation
        if psi > 0.25:
            severity_tag = "significant shift"
        elif psi > 0.1:
            severity_tag = "moderate shift"
        else:
            severity_tag = "minor shift"

        what_changed.append(
            f"'{label}' shows {severity_tag} between {reference_period} "
            f"and {current_period} (PSI={psi:.3f})."
        )
        why_matters.append(_why_statement(feat))

    # Primary drift category
    primary_categories = list(categories)[:2]
    actions = [_get_action(cat) for cat in primary_categories]

    # Retraining recommendation
    retrain_flag = drift_report.get("retraining_flag", False)
    retrain_msg  = (
        "Model retraining is recommended — PSI > 0.2 on 3+ features simultaneously. "
        "Current predictions may be stale."
        if retrain_flag else
        "Model performance is likely stable — monitor next period."
    )

    return {
        "reference_period": reference_period,
        "current_period":   current_period,
        "drift_severity":   severity,
        "drifted_features": drifted_feats,
        "reasoning": {
            "what_changed":        what_changed,
            "why_churn_increased": why_matters,
            "affected_categories": primary_categories,
            "recommended_actions": actions,
            "retraining_note":     retrain_msg,
        },
    }


# ── Segment degradation reasoning ─────────────────────────────────────────
def build_segment_reasoning(
    segment_data: dict,
    global_reasoning: dict = None,
) -> dict:
    """
    WHAT is happening in a degrading segment + WHY it's degrading.

    Args:
        segment_data: {
            "segment": "pro/monthly/East",
            "churn_rate": 0.41,
            "prev_churn_rate": 0.28,
            "revenue_at_risk": 125000,
            "top_risk_features": [feature, ...]
        }
        global_reasoning: Optional global reasoning for cross-reference.

    Returns:
        Segment reasoning dict.
    """
    seg         = segment_data.get("segment", "Unknown segment")
    churn_rate  = segment_data.get("churn_rate", 0)
    prev_rate   = segment_data.get("prev_churn_rate")
    revenue_risk = segment_data.get("revenue_at_risk", 0)
    risk_feats  = segment_data.get("top_risk_features", [])

    # WHAT is happening
    what_statements = [
        f"Segment '{seg}' has a churn rate of {churn_rate:.1%}.",
    ]
    if prev_rate:
        delta = churn_rate - prev_rate
        direction = "increased" if delta > 0 else "decreased"
        what_statements.append(
            f"Churn rate has {direction} by {abs(delta):.1%} since the previous period."
        )
    if revenue_risk:
        what_statements.append(
            f"Estimated annual revenue at risk: ${revenue_risk:,.0f}."
        )

    for feat in risk_feats[:3]:
        mapping = FEATURE_BUSINESS_MAP.get(feat, {})
        label   = mapping.get("label", feat)
        what_statements.append(
            f"'{label}' is a top risk driver in this segment."
        )

    # WHY it's degrading
    why_statements = []
    categories = set()
    for feat in risk_feats[:3]:
        cat = _get_category(feat)
        categories.add(cat)
        why_statements.append(_why_statement(feat))

    # SaaS benchmarking context
    saas_benchmark_monthly = 0.085  # 8.5% monthly = SaaS industry median
    benchmark_note = (
        f"This segment's churn rate ({churn_rate:.1%}) exceeds the SaaS industry "
        f"monthly median ({saas_benchmark_monthly:.1%})."
        if churn_rate > saas_benchmark_monthly else
        f"This segment's churn rate ({churn_rate:.1%}) is within SaaS industry benchmarks."
    )

    actions = list({_get_action(cat) for cat in categories})[:2]

    return {
        "segment":          seg,
        "churn_rate":       churn_rate,
        "revenue_at_risk":  revenue_risk,
        "benchmark_note":   benchmark_note,
        "reasoning": {
            "what_is_happening": what_statements,
            "why_degrading":     why_statements,
            "affected_categories": list(categories),
            "recommended_actions": actions,
        },
    }


# ── Extended WHAT/WHY question bank ───────────────────────────────────────
SUPPORTED_QUESTIONS = {
    # Per-customer questions
    "why_is_customer_at_risk":
        "→ build_customer_reasoning(explanation, X_row)",
    "what_changed_for_customer":
        "→ build_customer_reasoning(explanation, X_row)['reasoning']['what_changed']",
    "what_are_protective_factors":
        "→ build_customer_reasoning(explanation, X_row)['reasoning']['protective_factors']",
    "what_action_should_csm_take":
        "→ build_customer_reasoning(explanation, X_row)['reasoning']['why']['recommended_action']",
    "how_confident_is_the_explanation":
        "→ explanation['high_conf_features'] + confidence_summary(batch)",

    # Population questions
    "why_is_churn_increasing":
        "→ build_global_reasoning(global_exp, df)",
    "what_behavioral_patterns_are_declining":
        "→ build_global_reasoning(global_exp, df)['reasoning']['what_patterns']",
    "which_features_drive_churn_globally":
        "→ XAIEngine.explain_global(X_sample)['top_features']",
    "what_are_the_top_churn_drivers":
        "→ build_global_reasoning(global_exp, df)['top_global_features']",

    # Segment questions
    "why_is_segment_degrading":
        "→ build_segment_reasoning(segment_data)",
    "what_is_happening_in_segment":
        "→ build_segment_reasoning(segment_data)['reasoning']['what_is_happening']",
    "which_segments_exceed_saas_benchmark":
        "→ build_segment_reasoning(segment_data)['benchmark_note']",
    "what_revenue_is_at_risk":
        "→ build_segment_reasoning(segment_data)['revenue_at_risk']",

    # Drift questions
    "what_changed_since_last_period":
        "→ build_drift_reasoning(drift_report, ref, current)",
    "why_did_churn_increase_this_month":
        "→ build_drift_reasoning(drift_report, ref, current)['reasoning']['why_churn_increased']",
    "should_the_model_be_retrained":
        "→ build_drift_reasoning(drift_report, ref, current)['reasoning']['retraining_note']",
    "which_features_drifted":
        "→ build_drift_reasoning(drift_report, ref, current)['drifted_features']",
}


def list_supported_questions() -> None:
    """Print all supported WHAT/WHY questions and their API calls."""
    print("\n── Supported WHAT/WHY Questions ────────────────────────")
    for q, call in SUPPORTED_QUESTIONS.items():
        print(f"\n  Q: {q.replace('_', ' ').title()}")
        print(f"     {call}")
