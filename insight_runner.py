"""
insight_runner.py
=================
Customer Health Forensics — Phase 5
CLI runner — replaces Phase5_Insight_Colab.ipynb.

Usage:
  # Full run (rule fallback, no LLM):
  python insight_runner.py

  # With HuggingFace API:
  HUGGINGFACEHUB_API_TOKEN=hf_xxx python insight_runner.py

  # Choose LLM model:
  python insight_runner.py --llm-model mistralai/Mistral-7B-Instruct-v0.2

  # Q&A only:
  python insight_runner.py --qa-only
  python insight_runner.py --ask "Why are Pro users churning?"

  # Train ANN first (once, from Phase 1 data):
  python insight_runner.py --train-ann

  # Custom paths (Colab):
  python insight_runner.py \\
      --outputs-dir /content/drive/MyDrive/CustomerHealth/outputs \\
      --models-dir  /content/drive/MyDrive/CustomerHealth/models \\
      --save-dir    /content/drive/MyDrive/CustomerHealth/outputs/insights

Outputs saved to outputs/insights/:
  intelligence_report.json   ← full 8-section report
  executive_summary.txt      ← plain text exec summary
  recommendations.json       ← prioritised action list
  qa_log.json                ← Q&A session log
  rl_policy.json             ← RL learned policy
  ann_feature_model.pkl      ← trained ANN (if --train-ann)
"""

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for candidate in [HERE / "src", HERE]:
    sys.path.insert(0, str(candidate))

from insight_engine  import InsightEngine, NumpyEncoder
from qa_engine       import QAEngine
from llm_pipeline    import LLMPipeline
from rl_recommender  import RLRecommender

DEFAULT_OUTPUTS_DIR = HERE / "outputs"
DEFAULT_MODELS_DIR  = HERE / "models"
DEFAULT_SAVE_DIR    = HERE / "outputs" / "insights"

# Standard Q&A questions run on every report
STANDARD_QUESTIONS = [
    "Why are customers churning?",
    "Which segment is at highest risk?",
    "What should we do to reduce churn this month?",
    "Which features are showing the most drift?",
    "What is the total revenue at risk?",
    "Are there any early warning signals?",
    "Should the model be retrained?",
    "Which customers need immediate attention?",
]


def _save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, cls=NumpyEncoder)


def _print_report_summary(report: dict):
    print(f"\n{'='*62}")
    print(f"  PHASE 5 INTELLIGENCE REPORT")
    print(f"{'='*62}")
    print(f"\n── Executive Summary ──────────────────────────────────")
    print(f"  {report.get('executive_summary','—')}")

    bi = report.get("business_impact",{})
    print(f"\n── Business Impact ────────────────────────────────────")
    print(f"  Revenue at risk:     ${bi.get('total_annual_revenue_at_risk',0):,.0f}")
    print(f"  Projected loss:      ${bi.get('projected_loss_if_no_action',0):,.0f}")
    print(f"  Potential recovery:  ${bi.get('potential_recovery',0):,.0f}")
    print(f"  Critical customers:  {bi.get('critical_customers_count',0)}")

    cr = report.get("customer_risk",{})
    dist = cr.get("risk_distribution",{})
    print(f"\n── Risk Distribution ──────────────────────────────────")
    for tier, n in dist.items():
        print(f"  {tier:10s} {n:6,}")

    segs = report.get("segments",{})
    print(f"\n── Segment Intelligence ───────────────────────────────")
    print(f"  {segs.get('narrative','—')[:200]}...")

    drift = report.get("drift_analysis",{})
    print(f"\n── Drift & Behavior ───────────────────────────────────")
    print(f"  Severity: {drift.get('overall_drift_severity','—')}")
    ew = drift.get("early_warning_features",[])
    if ew: print(f"  Early warnings: {', '.join(ew[:5])}")

    recs = report.get("recommendations",[])
    print(f"\n── Recommendations ({len(recs)}) ───────────────────────────────")
    for r in recs[:3]:
        print(f"  {r.get('rank',0)}. {r.get('description','—')[:120]}")


def train_ann_command(outputs_dir: Path, models_dir: Path, data_dir: Path):
    """Train ANN from Phase 1 data."""
    from ann_feature_model import train_from_phase1_artifacts
    save_path = models_dir / "ann_feature_model.pkl"
    print(f"[ANN] Training ANN from Phase 1 data...")
    model = train_from_phase1_artifacts(
        models_dir = models_dir,
        data_dir   = data_dir,
        save_path  = save_path,
    )
    print(f"[ANN] ANN trained and saved → {save_path}")
    return model


def run_insights(
    outputs_dir: Path = DEFAULT_OUTPUTS_DIR,
    models_dir:  Path = DEFAULT_MODELS_DIR,
    save_dir:    Path = DEFAULT_SAVE_DIR,
    llm_model:   str  = None,
    llm_mode:    str  = "auto",
    qa_only:     bool = False,
    ask:         str  = None,
    train_ann:   bool = False,
    interactive_qa: bool = False,
    data_dir:    Path = None,
) -> dict:

    save_dir.mkdir(parents=True, exist_ok=True)
    data_dir = data_dir or outputs_dir.parent / "data"

    # ── Train ANN if requested ─────────────────────────────────
    ann_model     = None
    feature_names = []
    if train_ann:
        ann_model = train_ann_command(outputs_dir, models_dir, data_dir)
        import json as _j
        fn_path = models_dir / "feature_names.json"
        if fn_path.exists():
            with open(fn_path) as f: feature_names = _j.load(f)
    else:
        # Try loading existing ANN
        ann_path = models_dir / "ann_feature_model.pkl"
        if ann_path.exists():
            try:
                from ann_feature_model import load_ann
                ann_model, feature_names = load_ann(ann_path)
                print(f"[ANN] Loaded from {ann_path}")
            except Exception as e:
                print(f"[ANN] Could not load model: {e}")

    # ── LLM setup ──────────────────────────────────────────────
    if llm_model:
        os.environ["LLM_MODEL_ID"] = llm_model
    if llm_mode:
        os.environ["LLM_MODE"] = llm_mode

    llm = LLMPipeline()

    # ── RL setup ───────────────────────────────────────────────
    rl_path = save_dir / "rl_policy.json"
    rl = RLRecommender(load_path=rl_path if rl_path.exists() else None)

    # ── Q&A only mode ──────────────────────────────────────────
    if qa_only or ask:
        qa = QAEngine(outputs_dir=outputs_dir, llm=llm)
        if ask:
            result = qa.ask(ask)
            print(f"\nQ: {result['question']}")
            print(f"A: {result['answer']}")
            _save_json([result], save_dir / "qa_log.json")
            return result
        elif interactive_qa:
            qa.interactive()
            return {}
        else:
            qa_log = qa.ask_batch(STANDARD_QUESTIONS)
            _save_json(qa_log, save_dir / "qa_log.json")
            for r in qa_log:
                print(f"\nQ: {r['question']}")
                print(f"A: {r['answer'][:200]}...")
            return {"qa_log": qa_log}

    # ── Full insight report ─────────────────────────────────────
    engine = InsightEngine(
        outputs_dir   = outputs_dir,
        models_dir    = models_dir,
        llm           = llm,
        rl            = rl,
        ann_model     = ann_model,
        feature_names = feature_names,
        verbose       = True,
    )

    report = engine.run(save_path=save_dir / "intelligence_report.json")

    # Save individual sections
    exec_sum = report.get("executive_summary","")
    (save_dir / "executive_summary.txt").write_text(exec_sum)
    _save_json(report.get("recommendations",[]), save_dir / "recommendations.json")
    _save_json(report.get("business_impact",{}),  save_dir / "business_impact.json")

    # Run standard Q&A
    print(f"\n[QA] Running {len(STANDARD_QUESTIONS)} standard questions...")
    qa = QAEngine(outputs_dir=outputs_dir, llm=llm)
    qa_log = qa.ask_batch(STANDARD_QUESTIONS)
    _save_json(qa_log, save_dir / "qa_log.json")

    # Save RL policy
    rl.save(rl_path)

    # Print summary
    _print_report_summary(report)

    print(f"\n{'='*62}")
    print(f"  PHASE 5 COMPLETE  ({report.get('runtime_seconds','?')}s)")
    print(f"{'='*62}")
    print(f"  LLM mode:    {llm.active_mode}")
    print(f"  Artifacts → {save_dir}")
    print(f"  intelligence_report.json  ← full 8-section report")
    print(f"  qa_log.json               ← {len(qa_log)} Q&A answers")
    print(f"  rl_policy.json            ← RL learned actions")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 5 Insight Engine — Customer Health Forensics"
    )
    parser.add_argument("--outputs-dir",    type=str, default=None)
    parser.add_argument("--models-dir",     type=str, default=None)
    parser.add_argument("--save-dir",       type=str, default=None)
    parser.add_argument("--data-dir",       type=str, default=None)
    parser.add_argument("--llm-model",      type=str, default=None,
                        help="HuggingFace model ID (e.g. mistralai/Mistral-7B-Instruct-v0.2)")
    parser.add_argument("--llm-mode",       type=str, default="auto",
                        choices=["auto","api","local","rules"])
    parser.add_argument("--qa-only",        action="store_true")
    parser.add_argument("--ask",            type=str, default=None,
                        help="Ask a single question and print answer")
    parser.add_argument("--interactive",    action="store_true",
                        help="Start interactive Q&A session")
    parser.add_argument("--train-ann",      action="store_true",
                        help="Train ANN from Phase 1 data before generating insights")
    args = parser.parse_args()

    run_insights(
        outputs_dir    = Path(args.outputs_dir) if args.outputs_dir else DEFAULT_OUTPUTS_DIR,
        models_dir     = Path(args.models_dir)  if args.models_dir  else DEFAULT_MODELS_DIR,
        save_dir       = Path(args.save_dir)    if args.save_dir    else DEFAULT_SAVE_DIR,
        data_dir       = Path(args.data_dir)    if args.data_dir    else None,
        llm_model      = args.llm_model,
        llm_mode       = args.llm_mode,
        qa_only        = args.qa_only,
        ask            = args.ask,
        train_ann      = args.train_ann,
        interactive_qa = args.interactive,
    )
