"""
prompt_templates.py
===================
Customer Health Forensics — Phase 5
Jinja2 prompt templates for all LLM interactions.

Templates are registered in TEMPLATE_REGISTRY and rendered
by llm_pipeline.py before being sent to the LLM.

Design principles:
  - Each template has a clear role (summarization / reasoning / Q&A)
  - Templates include structured context to keep LLM focused
  - All templates degrade to rule-based output if LLM unavailable
  - Max context window kept under 2048 tokens
"""

from jinja2 import Environment, BaseLoader

_env = Environment(loader=BaseLoader())


# ── Template definitions ────────────────────────────────────────
TEMPLATES = {

    # ── Executive summary ──────────────────────────────────────
    "executive_summary": """
You are a senior customer success analyst. Write a concise executive summary (3–4 sentences) based on the data below.
Focus on: overall churn risk, most affected segments, and urgency level.
Be specific with numbers. Do NOT use filler phrases like "it is important to note".

DATA:
- Overall churn rate: {{ churn_rate | round(3) }} ({{ (churn_rate * 100) | round(1) }}%)
- Churn change vs previous period: {{ churn_delta | round(3) }} ({{ '+' if churn_delta > 0 else '' }}{{ (churn_delta * 100) | round(1) }}%)
- Customers at Critical risk (prob > 0.7): {{ n_critical }}
- Top degrading segment: {{ top_segment }} (churn {{ top_segment_rate | round(1) }}%)
- Revenue at risk: ${{ revenue_at_risk | int | format_number }}
- Early warning features drifting: {{ early_warning_features | join(', ') }}
- Overall drift severity: {{ drift_severity }}

Executive Summary:
""".strip(),

    # ── Causal analysis ────────────────────────────────────────
    "causal_analysis": """
You are a churn analyst. Explain WHY churn is happening based on the evidence below.
Provide 2–3 specific causal chains. Format: [Signal] → [Mechanism] → [Outcome].
Be analytical, not generic. Avoid advice — only explain causes.

EVIDENCE:
- Top churn drivers (from XAI): {{ top_features | join(', ') }}
- Drifting features (behavior change): {{ drifted_features | join(', ') }}
- Primary rule triggers: {{ rule_categories | join(', ') }}
- Segment patterns: {{ segment_patterns }}
- Statistical validation: {{ r_findings }}

Causal Analysis:
""".strip(),

    # ── Predictive outlook ─────────────────────────────────────
    "predictive_outlook": """
You are a data scientist writing a risk projection for a SaaS business.
Based on the trends below, describe what will likely happen over the next 30–60 days
if no action is taken. Be specific about which segments and features to watch.

TREND DATA:
- Current churn rate: {{ current_churn_rate | round(3) }}
- Churn velocity: {{ velocity }}
- Accelerating segments: {{ accelerating_segments | join(', ') }}
- Leading indicators declining: {{ declining_indicators | join(', ') }}
- Retraining flag: {{ retrain_required }}
- High-risk drift features: {{ high_drift_features | join(', ') }}

30–60 Day Risk Projection:
""".strip(),

    # ── Recommendations ────────────────────────────────────────
    "recommendations": """
You are a customer success director. Based on the analysis below, provide 3–5 specific,
prioritised retention recommendations. Each must include: WHO to target, WHAT to do, WHY it works.
Rank by expected impact. Be concrete — no generic advice.

ANALYSIS:
- Top degrading segment: {{ top_segment }}
- Primary churn drivers: {{ top_drivers | join(', ') }}
- Critical customers: {{ n_critical }} (churn prob > 0.70)
- Top RL-recommended actions: {{ rl_actions | join(', ') }}
- Revenue at risk: ${{ revenue_at_risk | int }}
- Drift early warnings: {{ early_warnings | join(', ') }}
- Rule engine top action: {{ rule_action }}

Prioritised Recommendations:
""".strip(),

    # ── Segment intelligence ───────────────────────────────────
    "segment_intelligence": """
You are a growth analyst. Explain the segment dynamics below in 2–3 sentences.
Focus on: what is unusual, what is worsening fastest, and where revenue risk is concentrated.

SEGMENT DATA:
- Degrading segments: {{ degrading_segments }}
- Improving segments: {{ improving_segments }}
- Highest churn segment: {{ highest_churn_segment }} at {{ highest_churn_rate | round(1) }}%
- Total revenue at risk: ${{ total_revenue_at_risk | int }}
- Segments exceeding benchmark: {{ above_benchmark | join(', ') }}

Segment Intelligence:
""".strip(),

    # ── Q&A system ────────────────────────────────────────────
    "qa_answer": """
You are an AI analyst for a customer health platform.
Answer the question below using ONLY the provided data. Be concise and specific.
If the data doesn't support a definitive answer, say so clearly.

AVAILABLE DATA CONTEXT:
{{ context }}

QUESTION: {{ question }}

Answer:
""".strip(),

    # ── Single customer explanation ────────────────────────────
    "customer_explanation": """
You are a customer success manager. Write a brief, actionable explanation of why
customer {{ customer_id }} is at risk, and what to do immediately.
Use plain English — this will be read by a non-technical CSM.
Keep it to 3–4 sentences maximum.

CUSTOMER DATA:
- Churn probability: {{ churn_prob | round(2) }} ({{ risk_tier }} risk)
- Top risk factors: {{ top_factors | join('; ') }}
- Primary driver: {{ primary_driver }}
- Last login: {{ last_login_days_ago }} days ago
- Health score: {{ health_score }}/100
- Recommended action: {{ top_action }}

Explanation:
""".strip(),

}


# ── Template registry ──────────────────────────────────────────
class PromptTemplates:
    """Registry of all Jinja2 prompt templates."""

    def __init__(self):
        self._compiled = {
            name: _env.from_string(tpl)
            for name, tpl in TEMPLATES.items()
        }

    def render(self, template_name: str, **context) -> str:
        """
        Render a template with the given context.

        Adds custom Jinja2 filter: format_number (comma thousands separator).
        """
        if template_name not in self._compiled:
            raise ValueError(f"Unknown template: '{template_name}'. "
                             f"Available: {list(self._compiled.keys())}")

        # Custom filter for number formatting
        _env.filters["format_number"] = lambda n: f"{int(n):,}"

        tpl = self._compiled[template_name]
        try:
            return tpl.render(**context).strip()
        except Exception as e:
            # Return a safe fallback prompt on Jinja rendering errors
            return f"Summarise the following data: {context}"

    def list_templates(self) -> list[str]:
        return list(self._compiled.keys())


# Module-level singleton
templates = PromptTemplates()
