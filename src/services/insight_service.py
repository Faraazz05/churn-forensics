"""
services/insight_service.py
============================
Calls Phase 5 insight engine / loads saved outputs.
"""
import json, os, sys
from pathlib import Path
from typing import Optional
from core.config import get_settings
from utils.logger import log

settings = get_settings()


def _insights_dir() -> Path:
    return settings.OUTPUTS_DIR / "insights"


def load_latest_report() -> Optional[dict]:
    p = _insights_dir() / "intelligence_report.json"
    if not p.exists(): return None
    with open(p) as f: return json.load(f)


def generate_report(llm_mode: str = None) -> dict:
    """Generate a fresh Phase 5 insight report."""
    for src in [settings.PHASE5_SRC, settings.BASE_DIR / "src"]:
        if src.exists() and str(src) not in sys.path:
            sys.path.insert(0, str(src))

    try:
        from insight_runner import run_insights
        mode = llm_mode or os.getenv("LLM_MODE", "rules")
        return run_insights(
            outputs_dir = settings.OUTPUTS_DIR,
            models_dir  = settings.MODELS_DIR,
            save_dir    = _insights_dir(),
            llm_mode    = mode,
        )
    except ImportError as e:
        log.warning(f"[InsightService] insight_runner not found: {e}")
        return {"error": "Phase 5 not available", "detail": str(e)}


def answer_question(question: str) -> dict:
    """Run the Q&A engine against all phase outputs."""
    for src in [settings.PHASE5_SRC, settings.BASE_DIR / "src"]:
        if src.exists() and str(src) not in sys.path:
            sys.path.insert(0, str(src))
    try:
        from qa_engine import QAEngine
        from llm_pipeline import LLMPipeline
        llm = LLMPipeline(mode=os.getenv("LLM_MODE","rules"))
        qa  = QAEngine(outputs_dir=settings.OUTPUTS_DIR, llm=llm)
        return qa.ask(question)
    except Exception as e:
        return {"question": question, "answer": f"QA unavailable: {e}",
                "intent": "unknown", "source": "error", "context_used": []}
