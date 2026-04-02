"""
rule_engine.py
==============
Customer Health Forensics — Phase 5
Deterministic rule-based engine.

This is the backbone of the fallback system when LLM is unavailable,
and also the pre-filter that structures data before LLM/ANN processing.

Rules fire independently and combine into:
  - insight flags (what is happening)
  - causal labels (why it is happening)
  - recommendation triggers (what to do)
  - risk projections (what will happen)

Design: pure functions, no state, fully testable.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Any


# ── Risk tiers ─────────────────────────────────────────────────
def risk_tier(prob: float) -> str:
    if prob >= 0.70: return "Critical"
    if prob >= 0.50: return "High"
    if prob >= 0.30: return "Medium"
    return "Safe"


# ── Rule result ────────────────────────────────────────────────
@dataclass
class RuleResult:
    rule_id:     str
    fired:       bool
    category:    str          # engagement / payment / support / satisfaction / contract
    what:        str          # data-level observation
    why:         str          # causal interpretation
    severity:    str          # LOW / MEDIUM / HIGH / CRITICAL
    action:      str          # recommended action
    impact_est:  float = 0.0  # estimated retention impact 0–1
    tags:        list  = field(default_factory=list)


# ── Individual rules ───────────────────────────────────────────
RULES = [

    # ── Inactivity rules ──────────────────────────────────────
    {
        "id": "R01_inactivity_critical",
        "condition": lambda f: f.get("last_login_days_ago", 0) > 30,
        "category": "engagement",
        "severity": "CRITICAL",
        "what": "Customer has not logged in for {last_login_days_ago:.0f} days.",
        "why":  "Extended inactivity (30+ days) is the strongest leading churn indicator. "
                "After 3 weeks without login, re-engagement success rates drop sharply.",
        "action": "Trigger immediate personalised re-engagement email. "
                  "Offer incentive (discount or feature highlight) to return within 7 days.",
        "impact_est": 0.85,
        "tags": ["inactivity", "urgent"],
    },
    {
        "id": "R02_inactivity_high",
        "condition": lambda f: 14 < f.get("last_login_days_ago", 0) <= 30,
        "category": "engagement",
        "severity": "HIGH",
        "what": "Customer last logged in {last_login_days_ago:.0f} days ago.",
        "why":  "Two-week inactivity signals product disengagement. "
                "Customer may be evaluating alternatives.",
        "action": "Send 'we miss you' email with product update or tip. "
                  "Assign CSM check-in if high-value account.",
        "impact_est": 0.65,
        "tags": ["inactivity"],
    },

    # ── Login frequency rules ──────────────────────────────────
    {
        "id": "R03_logins_critical",
        "condition": lambda f: f.get("logins_per_week", 99) < 1,
        "category": "engagement",
        "severity": "CRITICAL",
        "what": "Logins per week dropped to {logins_per_week:.1f} (below 1/week).",
        "why":  "Less than 1 login per week means the product is no longer "
                "part of the customer's workflow. Habit loop is broken.",
        "action": "Escalate to customer success. Schedule a usage review call. "
                  "Identify what blocked their workflow.",
        "impact_est": 0.80,
        "tags": ["engagement_decline", "urgent"],
    },
    {
        "id": "R04_logins_declining",
        "condition": lambda f: 1 <= f.get("logins_per_week", 99) < 3,
        "category": "engagement",
        "severity": "HIGH",
        "what": "Weekly logins are at {logins_per_week:.1f} (below healthy threshold of 3).",
        "why":  "Declining login frequency precedes churn by 4–6 weeks on average.",
        "action": "Send targeted feature education sequence. "
                  "Highlight ROI or key workflows customer is not using.",
        "impact_est": 0.55,
        "tags": ["engagement_decline"],
    },

    # ── Payment rules ──────────────────────────────────────────
    {
        "id": "R05_payment_critical",
        "condition": lambda f: f.get("payment_failures_last_6m", 0) >= 3,
        "category": "payment",
        "severity": "CRITICAL",
        "what": "{payment_failures_last_6m:.0f} payment failures in last 6 months.",
        "why":  "3+ payment failures indicate active financial stress or deliberate "
                "cancellation intent. Without intervention, account will lapse.",
        "action": "Proactively contact billing contact. "
                  "Offer payment plan, grace period, or temporary downgrade.",
        "impact_est": 0.90,
        "tags": ["payment_stress", "urgent", "financial"],
    },
    {
        "id": "R06_payment_high",
        "condition": lambda f: f.get("payment_failures_last_6m", 0) in (1, 2),
        "category": "payment",
        "severity": "HIGH",
        "what": "{payment_failures_last_6m:.0f} payment failure(s) in last 6 months.",
        "why":  "Early payment failures are a leading indicator of budget pressure. "
                "Act before the account enters a failure loop.",
        "action": "Send proactive billing health email. "
                  "Update payment method prompt with clear CTA.",
        "impact_est": 0.70,
        "tags": ["payment_stress"],
    },

    # ── Support rules ──────────────────────────────────────────
    {
        "id": "R07_support_high",
        "condition": lambda f: f.get("support_tickets_last_90d", 0) >= 5,
        "category": "support",
        "severity": "HIGH",
        "what": "{support_tickets_last_90d:.0f} support tickets in last 90 days.",
        "why":  "High support volume signals unresolved product friction or confusion. "
                "Customers who repeatedly hit blockers lose confidence.",
        "action": "Escalate account to senior support. "
                  "Identify ticket patterns and resolve root-cause product issues.",
        "impact_est": 0.60,
        "tags": ["friction", "product_issue"],
    },
    {
        "id": "R08_support_ratio",
        "condition": lambda f: f.get("support_to_usage_ratio", 0) > 1.5,
        "category": "support",
        "severity": "HIGH",
        "what": "Support-to-usage ratio is {support_to_usage_ratio:.2f} — "
                "contacting support nearly as often as using the product.",
        "why":  "High friction ratio means the customer is spending more time "
                "fighting the product than using it.",
        "action": "Schedule a product walkthrough session. "
                  "Identify friction points and escalate to product team.",
        "impact_est": 0.65,
        "tags": ["friction", "product_issue"],
    },

    # ── Satisfaction rules ─────────────────────────────────────
    {
        "id": "R09_nps_detractor",
        "condition": lambda f: f.get("nps_score", 10) < 6,
        "category": "satisfaction",
        "severity": "HIGH",
        "what": "NPS score is {nps_score:.1f}/10 — customer is a detractor.",
        "why":  "Detractors are 3x more likely to churn than passives. "
                "Active dissatisfaction requires direct executive outreach.",
        "action": "Personal reach-out from account executive or founder. "
                  "Ask specifically what would make them a promoter.",
        "impact_est": 0.75,
        "tags": ["satisfaction", "relationship"],
    },
    {
        "id": "R10_nps_passive",
        "condition": lambda f: 6 <= f.get("nps_score", 10) < 7.5,
        "category": "satisfaction",
        "severity": "MEDIUM",
        "what": "NPS score is {nps_score:.1f}/10 — customer is passive.",
        "why":  "Passive customers are vulnerable to competitor switching "
                "when they encounter one better offer or experience.",
        "action": "Send value-focused communication. "
                  "Share customer success stories and upcoming features.",
        "impact_est": 0.40,
        "tags": ["satisfaction"],
    },

    # ── Contract rules ─────────────────────────────────────────
    {
        "id": "R11_monthly_contract",
        "condition": lambda f: f.get("commitment_score", 1.0) == 0.5,
        "category": "contract",
        "severity": "MEDIUM",
        "what": "Customer is on monthly contract — zero switching cost.",
        "why":  "Monthly customers churn at ~2x the rate of annual customers. "
                "No financial barrier to cancellation.",
        "action": "Offer annual plan with 15–20% discount. "
                  "Frame as cost savings, not commitment.",
        "impact_est": 0.50,
        "tags": ["contract", "upsell"],
    },

    # ── Feature adoption rules ─────────────────────────────────
    {
        "id": "R12_low_adoption",
        "condition": lambda f: f.get("features_used_count", 99) < 3,
        "category": "product_adoption",
        "severity": "HIGH",
        "what": "Using only {features_used_count:.0f} product features.",
        "why":  "Shallow product adoption = shallow dependency. "
                "Customers using < 3 features have minimal switching cost.",
        "action": "Trigger feature discovery email series. "
                  "Identify the 2 most impactful unused features for their plan.",
        "impact_est": 0.60,
        "tags": ["adoption", "product"],
    },

    # ── Health score rule ──────────────────────────────────────
    {
        "id": "R13_health_critical",
        "condition": lambda f: f.get("customer_health_score", 100) < 30,
        "category": "overall_health",
        "severity": "CRITICAL",
        "what": "Customer health score is {customer_health_score:.0f}/100.",
        "why":  "Health score below 30 indicates simultaneous failure across "
                "engagement, recency, payment, and satisfaction dimensions.",
        "action": "Immediate executive escalation. "
                  "Dedicated save campaign with personalised recovery plan.",
        "impact_est": 0.95,
        "tags": ["critical", "urgent", "all_dimensions"],
    },

    # ── Tenure rules ───────────────────────────────────────────
    {
        "id": "R14_new_customer_risk",
        "condition": lambda f: f.get("tenure_months", 99) < 3,
        "category": "onboarding",
        "severity": "HIGH",
        "what": "Customer tenure is only {tenure_months:.0f} months.",
        "why":  "First 90 days are critical. Customers who don't reach "
                "'aha moment' within 3 months have 60% churn probability.",
        "action": "Assign dedicated onboarding specialist. "
                  "Ensure activation milestones are met within 30/60/90 days.",
        "impact_est": 0.70,
        "tags": ["onboarding", "new_customer"],
    },

    # ── Stickiness rule ────────────────────────────────────────
    {
        "id": "R15_trapped_customer",
        "condition": lambda f: (f.get("tenure_months", 0) > 12 and
                                f.get("engagement_score", 1) < 0.3),
        "category": "engagement",
        "severity": "HIGH",
        "what": "High tenure ({tenure_months:.0f} months) with very low engagement "
                "(score: {engagement_score:.2f}) — trapped customer pattern.",
        "why":  "Long-tenure customers with declining engagement are waiting for "
                "contract end to cancel. They are not seen as at-risk by naive models.",
        "action": "Pre-renewal outreach 60 days before contract end. "
                  "Re-demonstrate value with personalised ROI report.",
        "impact_est": 0.75,
        "tags": ["trapped", "renewal_risk"],
    },
]


# ── Rule engine ────────────────────────────────────────────────
def evaluate_rules(features: dict) -> list[RuleResult]:
    """
    Evaluate all rules against a feature dict.

    Args:
        features: Dict of feature_name → value for one customer.

    Returns:
        List of fired RuleResult objects, sorted by severity.
    """
    SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    results = []

    for rule in RULES:
        try:
            fired = bool(rule["condition"](features))
        except Exception:
            fired = False

        if not fired:
            continue

        # Format WHAT/WHY with actual values
        what = rule["what"]
        try:
            what = what.format(**{k: float(v) if v is not None else 0
                                  for k, v in features.items()})
        except (KeyError, ValueError):
            pass

        results.append(RuleResult(
            rule_id    = rule["id"],
            fired      = True,
            category   = rule["category"],
            what       = what,
            why        = rule["why"],
            severity   = rule["severity"],
            action     = rule["action"],
            impact_est = rule.get("impact_est", 0.5),
            tags       = rule.get("tags", []),
        ))

    results.sort(key=lambda r: SEVERITY_ORDER.get(r.severity, 9))
    return results


def get_dominant_category(fired_rules: list[RuleResult]) -> str:
    """Return the most frequently occurring rule category."""
    if not fired_rules:
        return "unknown"
    cats = [r.category for r in fired_rules]
    return max(set(cats), key=cats.count)


def rule_summary(fired_rules: list[RuleResult]) -> dict:
    """Summarise fired rules into a structured dict."""
    if not fired_rules:
        return {
            "n_rules_fired": 0,
            "dominant_category": "none",
            "highest_severity": "NONE",
            "top_action": "Monitor — no risk rules triggered",
            "risk_categories": [],
        }

    SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    top = sorted(fired_rules, key=lambda r: SEVERITY_ORDER.get(r.severity, 9))[0]
    categories = list(dict.fromkeys(r.category for r in fired_rules))

    return {
        "n_rules_fired":      len(fired_rules),
        "dominant_category":  get_dominant_category(fired_rules),
        "highest_severity":   fired_rules[0].severity if fired_rules else "NONE",
        "top_action":         top.action,
        "max_impact_est":     max(r.impact_est for r in fired_rules),
        "risk_categories":    categories,
        "what_statements":    [r.what for r in fired_rules[:3]],
        "why_statements":     [r.why  for r in fired_rules[:3]],
        "all_actions":        [r.action for r in fired_rules],
    }


# ── Segment-level rules ────────────────────────────────────────
def evaluate_segment_rules(segment: dict) -> dict:
    """
    Apply rules to a segment-level dict (not customer-level).
    Returns flags + recommended actions for the segment.
    """
    flags   = []
    actions = []

    churn   = segment.get("churn_rate", 0) or 0
    delta   = segment.get("churn_delta", 0) or 0
    revenue = segment.get("revenue_at_risk", 0) or 0
    accel   = segment.get("acceleration", "") == "accelerating_risk"
    status  = segment.get("health_status", "stable")

    if churn > 0.30:
        flags.append("CRITICAL_CHURN_RATE")
        actions.append("Immediate segment-wide intervention required.")
    elif churn > 0.15:
        flags.append("HIGH_CHURN_RATE")
        actions.append("Investigate root cause — run segment deep-dive.")

    if delta > 0.15:
        flags.append("RAPID_DEGRADATION")
        actions.append(f"Churn increased {delta:.1%} — escalate to product/CS leadership.")
    elif delta > 0.08:
        flags.append("MODERATE_DEGRADATION")
        actions.append("Monitor closely — schedule segment review next week.")

    if accel:
        flags.append("ACCELERATING_RISK")
        actions.append("Churn is consistently worsening — proactive save campaign needed.")

    if revenue > 500_000:
        flags.append("HIGH_REVENUE_EXPOSURE")
        actions.append(f"${revenue:,.0f} annual revenue at risk — executive escalation.")

    if segment.get("exceeds_benchmark"):
        flags.append("ABOVE_INDUSTRY_BENCHMARK")
        actions.append("Exceeds SaaS median — benchmark review required.")

    severity = "LOW"
    if "CRITICAL_CHURN_RATE" in flags or "ACCELERATING_RISK" in flags: severity = "CRITICAL"
    elif "HIGH_CHURN_RATE" in flags or "RAPID_DEGRADATION" in flags:   severity = "HIGH"
    elif flags:                                                          severity = "MEDIUM"

    return {
        "flags":    flags,
        "actions":  actions,
        "severity": severity,
    }


# ── Drift rules ────────────────────────────────────────────────
def evaluate_drift_rules(drift_features: list[dict]) -> dict:
    """Apply rules to drift detection output."""
    early_warnings = [f for f in drift_features if f.get("early_warning")]
    high_severity  = [f for f in drift_features if f.get("drift_severity") == "HIGH"]
    xai_confirmed  = [f for f in early_warnings  if f.get("xai_confirmed")]

    actions = []
    if xai_confirmed:
        feats = ", ".join(f["feature"] for f in xai_confirmed[:3])
        actions.append(f"XAI-confirmed drift on: {feats}. "
                       "These features are confirmed churn drivers — immediate response needed.")
    if len(high_severity) >= 3:
        actions.append("3+ features with HIGH severity drift — model retraining recommended.")
    if early_warnings and not xai_confirmed:
        actions.append("Leading indicators declining — prepare retention campaigns now.")

    return {
        "n_early_warnings":  len(early_warnings),
        "n_high_severity":   len(high_severity),
        "n_xai_confirmed":   len(xai_confirmed),
        "actions":           actions,
        "overall_severity":  "HIGH" if len(high_severity) >= 3 else
                             "MEDIUM" if early_warnings else "LOW",
    }
