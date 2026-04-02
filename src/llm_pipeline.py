"""
llm_pipeline.py
===============
Customer Health Forensics — Phase 5
LangChain + HuggingFace LLM pipeline with deterministic fallback.

Supported models (configure via LLM_MODEL_ID):
  - mistralai/Mistral-7B-Instruct-v0.2    (recommended, 7B)
  - mistralai/Mixtral-8x7B-Instruct-v0.1  (better quality, 47B sparse)
  - meta-llama/Llama-2-7b-chat-hf         (Meta LLaMA 2)
  - tiiuae/falcon-7b-instruct             (TII Falcon)
  - google/flan-t5-large                  (lighter, T5-based)

Fallback chain:
  1. HuggingFace Inference API (remote, no GPU needed)
  2. Local HuggingFace model (requires GPU / enough RAM)
  3. Rule-based template (always works, no LLM)

The fallback is transparent — callers always get a string response.
"""

import os
import re
from pathlib import Path
from typing import Optional

from prompt_templates import templates

# ── LLM config ─────────────────────────────────────────────────
LLM_MODEL_ID      = os.getenv("LLM_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
HF_API_TOKEN      = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
LLM_MAX_NEW_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "512"))
LLM_TEMPERATURE   = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MODE          = os.getenv("LLM_MODE", "auto")  # auto / api / local / rules

# ── Optional imports ───────────────────────────────────────────
try:
    from langchain_huggingface import HuggingFaceEndpoint, HuggingFacePipeline
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    from transformers import pipeline as hf_pipeline, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


# ── Rule-based fallbacks ───────────────────────────────────────
# These produce structured outputs when LLM is unavailable.
# Each matches a template name and generates deterministic text.
RULE_FALLBACKS = {

    "executive_summary": lambda ctx: (
        f"Churn rate is {ctx.get('churn_rate', 0):.1%} "
        f"({'up' if ctx.get('churn_delta', 0) > 0 else 'down'} "
        f"{abs(ctx.get('churn_delta', 0)):.1%} vs prior period). "
        f"{ctx.get('n_critical', 0)} customers are at Critical risk. "
        f"Top degrading segment: {ctx.get('top_segment', '—')} "
        f"({ctx.get('top_segment_rate', 0):.1%} churn). "
        f"${ctx.get('revenue_at_risk', 0):,.0f} annual revenue at risk. "
        f"Drift severity: {ctx.get('drift_severity', '—')}. "
        f"Key features declining: {', '.join(ctx.get('early_warning_features', [])[:3])}."
    ),

    "causal_analysis": lambda ctx: (
        f"Primary drivers ({', '.join(ctx.get('top_features', [])[:3])}) "
        f"are causing churn through engagement deterioration → reduced product value → cancellation. "
        f"Behavior change confirmed via drift analysis on: "
        f"{', '.join(ctx.get('drifted_features', [])[:3])}. "
        f"Rule engine identified: {', '.join(ctx.get('rule_categories', [])[:2])} as dominant patterns."
    ),

    "predictive_outlook": lambda ctx: (
        f"If current trends continue ({ctx.get('velocity', 'stable')} churn velocity), "
        f"churn rate will likely persist or worsen over the next 30–60 days. "
        f"Segments at highest escalation risk: {', '.join(ctx.get('accelerating_segments', [])[:2])}. "
        f"Leading indicators to monitor: {', '.join(ctx.get('declining_indicators', [])[:3])}."
        + (" Model retraining is recommended due to significant feature drift." 
           if ctx.get('retrain_required') else "")
    ),

    "recommendations": lambda ctx: (
        f"1. {ctx.get('rule_action', 'Immediate customer success review required')} "
        f"— target {ctx.get('top_segment', 'high-risk customers')} first. "
        f"2. Address {ctx.get('top_drivers', ['engagement decline'])[0] if ctx.get('top_drivers') else 'top churn driver'} "
        f"with targeted campaign for {ctx.get('n_critical', 0)} Critical-tier customers. "
        f"3. Protect ${ctx.get('revenue_at_risk', 0):,.0f} revenue through "
        f"proactive outreach to accelerating-risk segments."
    ),

    "segment_intelligence": lambda ctx: (
        f"{len(ctx.get('degrading_segments', []))} segments are degrading. "
        f"Highest churn: {ctx.get('highest_churn_segment', '—')} at "
        f"{ctx.get('highest_churn_rate', 0):.1%}. "
        f"${ctx.get('total_revenue_at_risk', 0):,.0f} total annual revenue at risk. "
        + (f"Segments above benchmark: {', '.join(ctx.get('above_benchmark', [])[:3])}."
           if ctx.get('above_benchmark') else "All segments within industry benchmarks.")
    ),

    "qa_answer": lambda ctx: (
        f"Based on available data: {ctx.get('context', 'no context provided')[:300]}... "
        f"The answer to '{ctx.get('question', '')}' is not deterministically derivable "
        f"without LLM reasoning. Please enable the LLM pipeline for Q&A."
    ),

    "customer_explanation": lambda ctx: (
        f"Customer {ctx.get('customer_id', '—')} has a {ctx.get('churn_prob', 0):.0%} "
        f"churn probability ({ctx.get('risk_tier', '—')} risk). "
        f"Primary driver: {ctx.get('primary_driver', '—')}. "
        f"Last login: {ctx.get('last_login_days_ago', '?')} days ago. "
        f"Recommended action: {ctx.get('top_action', '—')}."
    ),
}


# ── LLM pipeline ───────────────────────────────────────────────
class LLMPipeline:
    """
    LangChain-based LLM pipeline with automatic fallback.

    Usage:
        llm = LLMPipeline()
        text = llm.generate("executive_summary", churn_rate=0.26, ...)
    """

    def __init__(self, model_id: str = None, mode: str = None):
        self.model_id = model_id or LLM_MODEL_ID
        self.mode     = mode     or LLM_MODE
        self._llm     = None
        self._mode_active = "rules"  # resolved mode

        self._initialize()

    def _initialize(self):
        """Try to initialise LLM in priority order: API → local → rules."""
        if self.mode == "rules":
            print("[LLM] Mode: rule-based fallback (LLM disabled)")
            self._mode_active = "rules"
            return

        # Try HuggingFace Inference API
        if self.mode in ("auto", "api") and LANGCHAIN_AVAILABLE and HF_API_TOKEN:
            try:
                self._llm = HuggingFaceEndpoint(
                    repo_id             = self.model_id,
                    huggingfacehub_api_token = HF_API_TOKEN,
                    max_new_tokens      = LLM_MAX_NEW_TOKENS,
                    temperature         = LLM_TEMPERATURE,
                    task                = "text-generation",
                )
                self._mode_active = "api"
                print(f"[LLM] Mode: HuggingFace API → {self.model_id}")
                return
            except Exception as e:
                print(f"[LLM] API init failed ({e}) — trying local...")

        # Try local HuggingFace model
        if self.mode in ("auto", "local") and LANGCHAIN_AVAILABLE and TRANSFORMERS_AVAILABLE:
            try:
                pipe = hf_pipeline(
                    "text-generation",
                    model            = self.model_id,
                    max_new_tokens   = LLM_MAX_NEW_TOKENS,
                    temperature      = LLM_TEMPERATURE,
                    do_sample        = True,
                    device_map       = "auto",
                )
                self._llm         = HuggingFacePipeline(pipeline=pipe)
                self._mode_active = "local"
                print(f"[LLM] Mode: local model → {self.model_id}")
                return
            except Exception as e:
                print(f"[LLM] Local model init failed ({e}) — using rules")

        # Fallback
        self._mode_active = "rules"
        if not HF_API_TOKEN:
            print("[LLM] No HUGGINGFACEHUB_API_TOKEN set. "
                  "Using rule-based fallback.\n"
                  "  To enable LLM: export HUGGINGFACEHUB_API_TOKEN=hf_...")
        else:
            print("[LLM] Falling back to rule-based system.")

    def generate(self, template_name: str, **context) -> str:
        """
        Generate text using LLM if available, otherwise rule fallback.

        Args:
            template_name: Key in TEMPLATES / RULE_FALLBACKS
            **context:     Template variables

        Returns:
            Generated text string.
        """
        if self._mode_active == "rules" or self._llm is None:
            return self._rule_fallback(template_name, context)

        try:
            prompt_text = templates.render(template_name, **context)

            if LANGCHAIN_AVAILABLE:
                lc_prompt = PromptTemplate.from_template("{prompt}")
                chain     = lc_prompt | self._llm | StrOutputParser()
                response  = chain.invoke({"prompt": prompt_text})
            else:
                response = self._llm(prompt_text)

            # Clean up common LLM artifacts
            response = self._clean_response(response, prompt_text)
            return response.strip()

        except Exception as e:
            print(f"[LLM] Generation failed ({e}) — using rule fallback")
            return self._rule_fallback(template_name, context)

    def _rule_fallback(self, template_name: str, context: dict) -> str:
        """Call the deterministic fallback for a template."""
        fallback = RULE_FALLBACKS.get(template_name)
        if fallback:
            try:
                return fallback(context)
            except Exception:
                pass
        return f"[Rule fallback] Analysis for '{template_name}' completed. " \
               f"Key context: {list(context.keys())}"

    def _clean_response(self, response: str, prompt: str) -> str:
        """Remove prompt echo and LLM artifacts."""
        # Remove echoed prompt
        if prompt[:50] in response:
            response = response.replace(prompt, "")
        # Remove common LLM preambles
        for prefix in ["Sure!", "Certainly!", "Of course!", "Here is", "Here's"]:
            if response.startswith(prefix):
                response = re.sub(rf"^{re.escape(prefix)}[,:]?\s*", "", response)
        return response.strip()

    @property
    def is_llm_active(self) -> bool:
        return self._mode_active in ("api", "local")

    @property
    def active_mode(self) -> str:
        return self._mode_active

    def __repr__(self):
        return f"LLMPipeline(model={self.model_id}, mode={self._mode_active})"
