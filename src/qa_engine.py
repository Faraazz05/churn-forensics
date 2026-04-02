"""
qa_engine.py
============
Customer Health Forensics — Phase 5
Natural language Q&A system.

Supports queries like:
  "Why are Pro users churning?"
  "Which segment is at highest risk?"
  "What should we do to reduce churn?"
  "Which features are drifting the most?"
  "What is the revenue at risk?"

Architecture:
  1. Intent classifier — map question to data source
  2. Context builder — pull relevant data from outputs
  3. LLM pipeline — generate answer (or rule fallback)

Context window budget: ~1000 tokens (fits within all models).
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

from llm_pipeline import LLMPipeline


# ── Question intent patterns ────────────────────────────────────
INTENT_PATTERNS = [
    # (pattern, intent_id, data_sources_needed)
    (r"why.*(churn|leaving|cancel)", "why_churning",      ["xai", "segments", "drift"]),
    (r"which.*(segment|plan|region).*(risk|churn)",        "highest_risk_segment",
                                                           ["segments"]),
    (r"what.*(do|action|recommend|fix|reduce)",            "recommendations",
                                                           ["segments", "drift", "rl"]),
    (r"which.*(feature|signal).*(drift|chang)",            "drifting_features",
                                                           ["drift"]),
    (r"revenue.*(risk|loss|impact)",                       "revenue_impact",
                                                           ["segments"]),
    (r"(early warning|leading indicator)",                 "early_warnings",
                                                           ["drift"]),
    (r"(customer|who).*(critical|highest|most)",           "critical_customers",
                                                           ["watchlist"]),
    (r"(segment|group).*(degrad|worsen|declin)",           "degrading_segments",
                                                           ["segments"]),
    (r"retrain|model.*stale",                              "retraining",
                                                           ["drift"]),
    (r"(what|how).*(churn rate|overall)",                  "overall_churn",
                                                           ["segments", "drift"]),
    (r"(enterprise|pro|basic).*(churn|leaving)",           "plan_churn",
                                                           ["segments"]),
    (r"(east|west|north|south|central).*(churn)",          "region_churn",
                                                           ["segments"]),
]


def classify_intent(question: str) -> tuple[str, list[str]]:
    """
    Classify question intent and return needed data sources.

    Returns:
        (intent_id, [data_sources])
    """
    q_lower = question.lower()
    for pattern, intent, sources in INTENT_PATTERNS:
        if re.search(pattern, q_lower):
            return intent, sources
    return "general", ["segments", "drift", "xai"]


# ── Context builders ────────────────────────────────────────────
def _fmt(val, default="—"):
    if val is None: return default
    if isinstance(val, float): return f"{val:.4f}"
    return str(val)


def build_context_for_intent(
    intent:   str,
    sources:  list[str],
    all_data: dict,
) -> str:
    """
    Build a focused context string for the LLM based on intent.
    Keeps context under ~800 tokens.
    """
    parts = []

    if "segments" in sources and "segments" in all_data:
        seg_data = all_data["segments"]
        insights = seg_data.get("global_insights", {})
        parts.append("SEGMENT DATA:")

        # Overall
        if "overall_churn_rate" in seg_data:
            parts.append(f"  Overall churn rate: {seg_data['overall_churn_rate']:.3f}")

        # Top degrading
        top_deg = insights.get("top_degrading_segments", [])[:3]
        if top_deg:
            parts.append("  Top degrading segments:")
            for s in top_deg:
                parts.append(
                    f"    {s.get('segment_id','—')}: churn={s.get('churn_rate',0):.3f}, "
                    f"delta=+{s.get('churn_delta',0):.3f}, "
                    f"revenue_risk=${s.get('revenue_at_risk',0):,.0f}"
                )

        parts.append(
            f"  Total revenue at risk: ${insights.get('total_revenue_at_risk',0):,.0f}\n"
            f"  Degrading: {insights.get('n_degrading',0)} | "
            f"Improving: {insights.get('n_improving',0)}"
        )

    if "drift" in sources and "drift" in all_data:
        drift = all_data["drift"]
        report = drift.get("drift_report", [])
        warnings = drift.get("early_warnings", [])
        retrain  = drift.get("retraining_trigger", {})

        parts.append("\nDRIFT DATA:")
        parts.append(f"  Overall drift severity: {drift.get('overall_drift_severity','—')}")
        if warnings:
            parts.append(f"  Early warning features ({len(warnings)}):")
            for w in warnings[:4]:
                xai = " [XAI-confirmed]" if w.get("xai_confirmed") else ""
                parts.append(f"    {w['feature']}: PSI={w['psi']:.3f}, "
                              f"trend={w['trend']}{xai}")
        parts.append(f"  Model retraining required: "
                     f"{retrain.get('model_retraining_required', False)}")

    if "xai" in sources and "xai" in all_data:
        xai = all_data["xai"]
        top = xai.get("top_features", [])[:5]
        if top:
            parts.append("\nXAI DATA (global feature importance):")
            for f in top:
                parts.append(
                    f"  {f.get('feature','—')}: "
                    f"importance={f.get('importance',0):.4f}, "
                    f"direction={f.get('direction','—')}"
                )

    if "watchlist" in sources and "watchlist" in all_data:
        watchlist = all_data["watchlist"][:3]
        parts.append(f"\nCRITICAL CUSTOMERS (top 3 of {len(all_data['watchlist'])}):")
        for c in watchlist:
            r = c.get("reasoning", {})
            why = r.get("why", {})
            parts.append(
                f"  {c.get('customer_id','—')}: "
                f"prob={c.get('churn_probability',0):.3f}, "
                f"driver={why.get('primary_driver','—')}"
            )

    if "rl" in sources and "rl_policy" in all_data:
        policy = all_data["rl_policy"]
        parts.append("\nRL POLICY (best learned actions):")
        for state, rec in list(policy.items())[:3]:
            parts.append(f"  {state}: {rec.get('description','—')}")

    return "\n".join(parts)


# ── Rule-based Q&A answers ─────────────────────────────────────
def rule_answer(intent: str, all_data: dict) -> str:
    """Generate a deterministic answer when LLM unavailable."""
    seg_insights = all_data.get("segments", {}).get("global_insights", {})
    drift_data   = all_data.get("drift", {})
    xai_data     = all_data.get("xai", {})

    if intent == "why_churning":
        top_feats = [f.get("feature","—") for f in xai_data.get("top_features",[])[:3]]
        top_degs  = [s.get("segment_id","—") for s in seg_insights.get("top_degrading_segments",[])[:2]]
        return (f"Churn is primarily driven by: {', '.join(top_feats) or 'see XAI outputs'}. "
                f"Most affected segments: {', '.join(top_degs) or 'see segmentation'}.")

    elif intent == "highest_risk_segment":
        top = seg_insights.get("highest_churn_segments", seg_insights.get("top_degrading_segments",[]))
        if top:
            s = top[0]
            return (f"Highest risk segment: {s.get('segment_id','—')} "
                    f"(churn rate: {s.get('churn_rate',0):.1%}, "
                    f"revenue at risk: ${s.get('revenue_at_risk',0):,.0f}).")
        return "Segment data not available."

    elif intent == "recommendations":
        top_deg = seg_insights.get("top_degrading_segments",[])
        seg_name = top_deg[0].get("segment_id","—") if top_deg else "high-risk segment"
        warnings = drift_data.get("early_warnings",[])
        warn_feats = [w["feature"] for w in warnings[:3]]
        return (f"1. Launch targeted re-engagement campaign for {seg_name}. "
                f"2. Address declining leading indicators: {', '.join(warn_feats) or 'see drift outputs'}. "
                f"3. Escalate Critical-tier customers (>0.7 probability) to CSM immediately.")

    elif intent == "drifting_features":
        drifted = drift_data.get("drifted_features",[])
        warnings = [w["feature"] for w in drift_data.get("early_warnings",[])]
        return (f"{len(drifted)} features have significant drift. "
                f"Early warning features: {', '.join(warnings[:5]) or 'none'}.")

    elif intent == "revenue_impact":
        rev = seg_insights.get("total_revenue_at_risk",0)
        return f"Total annual revenue at risk across all segments: ${rev:,.0f}."

    elif intent == "retraining":
        retrain = drift_data.get("retraining_trigger",{})
        req = retrain.get("model_retraining_required", False)
        return (f"Model retraining {'IS' if req else 'is NOT'} required. "
                f"Reason: {retrain.get('reason','—')}")

    elif intent == "early_warnings":
        warnings = drift_data.get("early_warnings",[])
        if not warnings:
            return "No early warning signals detected."
        return (f"{len(warnings)} early warning signals: "
                + ", ".join(w["feature"] for w in warnings[:5]) + ". "
                + "These features are declining AND are confirmed churn drivers.")

    else:
        return (f"Based on current data: churn rate is "
                f"{all_data.get('segments',{}).get('overall_churn_rate',0):.1%}, "
                f"with {seg_insights.get('n_degrading',0)} degrading segments. "
                f"See phase34_intelligence.json for full details.")


# ── Q&A Engine ─────────────────────────────────────────────────
class QAEngine:
    """
    Natural language Q&A over Customer Health Forensics outputs.

    Usage:
        qa = QAEngine(outputs_dir=Path("outputs"))
        answer = qa.ask("Why are Pro users churning?")
    """

    def __init__(self, outputs_dir: Path, llm: LLMPipeline = None):
        self.outputs_dir = Path(outputs_dir)
        self.llm         = llm or LLMPipeline()
        self._data_cache: dict = {}
        self._load_all_data()

    def _load_json(self, rel_path: str) -> Any:
        p = self.outputs_dir / rel_path
        if p.exists():
            with open(p) as f:
                return json.load(f)
        return None

    def _load_all_data(self):
        """Pre-load all phase outputs into memory."""
        # Segmentation
        seg = self._load_json("segmentation/segmentation_results.json") or []
        seg_insights = self._load_json("segmentation/global_insights.json") or {}
        overall_churn = None
        if seg:
            rates = [s.get("churn_rate") for s in (seg if isinstance(seg,list) else []) if s.get("churn_rate")]
            if rates: overall_churn = sum(rates) / len(rates)
        self._data_cache["segments"] = {
            "segments":          seg if isinstance(seg,list) else [],
            "global_insights":   seg_insights,
            "overall_churn_rate": overall_churn or 0,
        }

        # Drift
        drift = self._load_json("drift/drift_report.json") or {}
        self._data_cache["drift"] = drift

        # XAI
        xai = self._load_json("xai/global_explanation.json") or {}
        self._data_cache["xai"] = xai

        # Watchlist
        wl = self._load_json("xai/watchlist_reasoning.json") or []
        self._data_cache["watchlist"] = wl if isinstance(wl,list) else []

        # Intelligence
        intel = self._load_json("phase34_intelligence.json") or {}
        self._data_cache["intelligence"] = intel

        loaded = [k for k,v in self._data_cache.items() if v]
        print(f"[QA] Data loaded: {loaded}")

    def ask(self, question: str, verbose: bool = False) -> dict:
        """
        Answer a natural language question about customer health.

        Args:
            question: Natural language question string.
            verbose:  Print debug info.

        Returns:
            {
                "question": str,
                "answer":   str,
                "intent":   str,
                "source":   "llm" or "rules",
                "context_used": [sources]
            }
        """
        intent, sources = classify_intent(question)

        if verbose:
            print(f"[QA] Intent: {intent} | Sources: {sources}")

        context_str = build_context_for_intent(intent, sources, self._data_cache)

        # Try LLM first
        if self.llm.is_llm_active:
            answer = self.llm.generate(
                "qa_answer",
                question = question,
                context  = context_str,
            )
            source = "llm"
        else:
            answer = rule_answer(intent, self._data_cache)
            source = "rules"

        return {
            "question":     question,
            "answer":       answer,
            "intent":       intent,
            "source":       source,
            "context_used": sources,
        }

    def interactive(self):
        """Start an interactive Q&A session (CLI)."""
        print("\n── Customer Health Q&A System ──────────────────────────")
        print("  Ask any question about churn, segments, drift, or actions.")
        print("  Type 'quit' to exit.\n")
        while True:
            try:
                q = input("  Q: ").strip()
                if q.lower() in ("quit", "exit", "q"):
                    break
                if not q:
                    continue
                result = self.ask(q)
                print(f"\n  A: {result['answer']}")
                print(f"     [source: {result['source']} | intent: {result['intent']}]\n")
            except (KeyboardInterrupt, EOFError):
                break

    def ask_batch(self, questions: list[str]) -> list[dict]:
        """Answer a batch of questions."""
        return [self.ask(q) for q in questions]
