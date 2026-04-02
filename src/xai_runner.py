"""
xai_runner.py
=============
Customer Health Forensics System — Phase 2
XAI Consensus Engine Orchestrator.

Loads Phase 1 artifacts (best_model.pkl, feature_names.json) and runs
the full Phase 2 explanation + reasoning pipeline.

NO retraining. NO data regeneration.
Loads → explains → reasons → saves.

Usage:
    # Full global + watchlist explanation:
    python xai_runner.py

    # Single customer:
    python xai_runner.py --customer-id CUST_0000001

    # Batch (first N at-risk customers):
    python xai_runner.py --batch 100

    # Custom paths (Colab):
    python xai_runner.py \\
        --models-dir /content/drive/MyDrive/CustomerHealth/models \\
        --data-dir   /content/drive/MyDrive/CustomerHealth/data \\
        --output-dir /content/drive/MyDrive/CustomerHealth/outputs/xai

    # Print supported WHAT/WHY questions:
    python xai_runner.py --list-questions

Outputs (saved to outputs/xai/):
    global_explanation.json     ← population-level feature importance
    global_reasoning.json       ← WHAT/WHY at population level
    watchlist_explanations.json ← Critical-tier customers (prob > 0.7)
    watchlist_reasoning.json    ← WHAT/WHY per watchlist customer
    confidence_summary.json     ← agreement statistics across explanations
    xai_summary.json            ← full Phase 2 run metadata
"""

import argparse
import json
import sys
import time
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
SRC  = HERE / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from xai_engine      import XAIEngine, confidence_summary, GLOBAL_SAMPLE_SIZE
from reasoning_layer import (
    build_customer_reasoning,
    build_global_reasoning,
    list_supported_questions,
)
from feature_engineering import build_feature_matrix, get_feature_names


# ── Defaults ───────────────────────────────────────────────────────────────
DEFAULT_DATA_DIR   = HERE / "data"
DEFAULT_MODELS_DIR = HERE / "models"
DEFAULT_XAI_DIR    = HERE / "outputs" / "xai"

WATCHLIST_THRESHOLD = 0.70   # churn probability above this → watchlist
HIGH_RISK_THRESHOLD = 0.50   # high risk tier


# ── Artifact loading ───────────────────────────────────────────────────────
def load_phase1_artifacts(models_dir: Path) -> dict:
    """Load all Phase 1 outputs needed by Phase 2."""
    required = ["best_model.pkl", "best_model_info.json", "feature_names.json"]
    for f in required:
        if not (models_dir / f).exists():
            raise FileNotFoundError(
                f"✗ Missing Phase 1 artifact: {models_dir / f}\n"
                f"  Run train.py first."
            )

    model = joblib.load(models_dir / "best_model.pkl")
    with open(models_dir / "best_model_info.json") as f:
        model_info = json.load(f)
    with open(models_dir / "feature_names.json") as f:
        feature_names = json.load(f)

    print(f"\n[xai_runner] Loaded model: {model_info['best_model_name']}")
    print(f"[xai_runner] XAI method (Phase 1 recommendation): {model_info['xai_method']}")
    print(f"[xai_runner] Features: {len(feature_names)}")

    return {
        "model":         model,
        "model_info":    model_info,
        "feature_names": feature_names,
    }


# ── Data loading ───────────────────────────────────────────────────────────
def load_data_for_xai(
    data_dir:      Path,
    models_dir:    Path,
    sample_size:   int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Load customer data, apply feature engineering, split to recover test set.
    Returns (df_raw, X_test, y_test, customer_ids_test) — consistent with train.py split.
    """
    csv_path = data_dir / "customers.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"✗ customers.csv not found at {csv_path}\n  Run train.py first.")

    print(f"\n[xai_runner] Loading data from {csv_path}...")
    if sample_size:
        df = pd.read_csv(csv_path, nrows=sample_size)
    else:
        df = pd.read_csv(csv_path)

    print(f"[xai_runner] {len(df):,} rows loaded | churn_rate={df['churned'].mean():.3f}")

    # Recover test split (same seed as train.py)
    _, df_test = train_test_split(df, test_size=0.20, stratify=df["churned"], random_state=42)

    X_test, y_test = build_feature_matrix(df_test)

    # Align to training feature list
    with open(models_dir / "feature_names.json") as f:
        train_features = json.load(f)

    X_test = X_test.reindex(columns=train_features, fill_value=0)

    customer_ids = df_test["customer_id"].reset_index(drop=True)
    X_test       = X_test.reset_index(drop=True)
    y_test       = y_test.reset_index(drop=True)

    print(f"[xai_runner] Test set: {len(X_test):,} customers")
    return df_test.reset_index(drop=True), X_test, y_test, customer_ids


# ── Prediction helper ──────────────────────────────────────────────────────
def get_predictions(model, X: pd.DataFrame) -> np.ndarray:
    """Return churn probabilities for all rows in X."""
    return model.predict_proba(X)[:, 1]


# ── Core runner steps ──────────────────────────────────────────────────────
def run_global_explanation(
    engine:     XAIEngine,
    X_test:     pd.DataFrame,
    df_test:    pd.DataFrame,
    output_dir: Path,
) -> tuple[dict, dict]:
    """Run global explanation + reasoning. Save to output_dir."""
    print(f"\n[xai_runner] Running global explanation "
          f"(sample={min(GLOBAL_SAMPLE_SIZE, len(X_test))} rows)...")

    global_exp = engine.explain_global(X_test, sample_size=GLOBAL_SAMPLE_SIZE)

    print(f"[xai_runner] Top 5 global churn drivers:")
    for i, feat in enumerate(global_exp["top_features"][:5], 1):
        print(f"  {i}. {feat['feature']:35s} "
              f"importance={feat['importance']:.4f}  {feat['direction']}")

    global_reason = build_global_reasoning(global_exp, df_test)

    output_dir.mkdir(parents=True, exist_ok=True)
    _save_json(global_exp,    output_dir / "global_explanation.json")
    _save_json(global_reason, output_dir / "global_reasoning.json")

    print(f"[xai_runner] Global explanation saved → {output_dir}")
    return global_exp, global_reason


def run_watchlist_explanation(
    engine:       XAIEngine,
    X_test:       pd.DataFrame,
    churn_probs:  np.ndarray,
    customer_ids: pd.Series,
    df_test:      pd.DataFrame,
    output_dir:   Path,
    max_watchlist: int = 200,
) -> tuple[list, list]:
    """
    Explain Critical-tier customers (churn_prob > WATCHLIST_THRESHOLD).
    This is the primary deliverable for customer success managers.
    """
    # Select watchlist customers
    watchlist_mask = churn_probs >= WATCHLIST_THRESHOLD
    n_watchlist    = watchlist_mask.sum()

    print(f"\n[xai_runner] Watchlist: {n_watchlist:,} customers at Critical risk "
          f"(prob ≥ {WATCHLIST_THRESHOLD})")

    if n_watchlist == 0:
        print("[xai_runner] No customers in Critical tier.")
        return [], []

    # Cap at max_watchlist for efficiency
    watchlist_idx = np.where(watchlist_mask)[0]
    if len(watchlist_idx) > max_watchlist:
        # Sort by probability descending — explain highest risk first
        watchlist_idx = watchlist_idx[np.argsort(churn_probs[watchlist_idx])[::-1]]
        watchlist_idx = watchlist_idx[:max_watchlist]
        print(f"[xai_runner] Capped at {max_watchlist} (sorted by risk, highest first)")

    X_wl   = X_test.iloc[watchlist_idx]
    ids_wl = customer_ids.iloc[watchlist_idx].tolist()
    prob_wl = churn_probs[watchlist_idx].tolist()

    print(f"[xai_runner] Explaining {len(watchlist_idx)} watchlist customers...")

    explanations = []
    reasonings   = []

    for i, (idx, cid, prob) in enumerate(zip(watchlist_idx, ids_wl, prob_wl)):
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(watchlist_idx)}")

        X_row = X_wl.iloc[[i]]

        try:
            exp = engine.explain_local(
                X_row       = X_row,
                customer_id = str(cid),
                churn_prob  = float(prob),
            )
            reason = build_customer_reasoning(exp, X_row)

            # Add risk tier and context
            exp["risk_tier"] = reason["risk_tier"]
            explanations.append(exp)
            reasonings.append(reason)

        except Exception as e:
            explanations.append({
                "customer_id":      str(cid),
                "churn_probability": float(prob),
                "error":             str(e),
                "explanations":      [],
            })
            reasonings.append({
                "customer_id":      str(cid),
                "churn_probability": float(prob),
                "error":             str(e),
            })

    # Remove _raw from saved output (too large for JSON files)
    clean_exps = []
    for exp in explanations:
        clean = {k: v for k, v in exp.items() if k != "_raw"}
        clean_exps.append(clean)

    _save_json(clean_exps, output_dir / "watchlist_explanations.json")
    _save_json(reasonings,  output_dir / "watchlist_reasoning.json")

    print(f"[xai_runner] Watchlist explanations saved → {output_dir}")
    return explanations, reasonings


def run_single_customer(
    engine:      XAIEngine,
    customer_id: str,
    X_test:      pd.DataFrame,
    customer_ids: pd.Series,
    churn_probs: np.ndarray,
    output_dir:  Path,
) -> dict | None:
    """Explain a single customer by ID."""
    if customer_id not in customer_ids.values:
        print(f"[xai_runner] Customer {customer_id} not found in test set.")
        return None

    idx   = customer_ids[customer_ids == customer_id].index[0]
    X_row = X_test.iloc[[idx]]
    prob  = float(churn_probs[idx])

    print(f"\n[xai_runner] Explaining customer {customer_id} (prob={prob:.4f})...")
    exp    = engine.explain_local(X_row=X_row, customer_id=customer_id, churn_prob=prob)
    reason = build_customer_reasoning(exp, X_row)

    _print_customer_result(reason)

    output_dir.mkdir(parents=True, exist_ok=True)
    clean = {k: v for k, v in exp.items() if k != "_raw"}
    _save_json(clean,  output_dir / f"explanation_{customer_id}.json")
    _save_json(reason, output_dir / f"reasoning_{customer_id}.json")

    return reason


# ── Print helpers ──────────────────────────────────────────────────────────
def _print_customer_result(reasoning: dict) -> None:
    cid   = reasoning["customer_id"]
    prob  = reasoning["churn_probability"]
    tier  = reasoning["risk_tier"]
    r     = reasoning.get("reasoning", {})

    print(f"\n{'─'*60}")
    print(f"  Customer:          {cid}")
    print(f"  Churn probability: {prob:.4f}")
    print(f"  Risk tier:         {tier}")
    print(f"\n  WHAT changed:")
    for w in r.get("what_changed", []):
        print(f"    • {w}")
    if r.get("protective_factors"):
        print(f"\n  Protective factors:")
        for p in r["protective_factors"]:
            print(f"    ✓ {p}")
    why = r.get("why", {})
    print(f"\n  WHY at risk:")
    print(f"    Primary driver:   {why.get('primary_driver', '—')}")
    print(f"    Category:         {why.get('primary_category', '—')}")
    print(f"    Interpretation:   {why.get('primary_why', '—')}")
    if why.get("secondary_driver"):
        print(f"    Secondary driver: {why.get('secondary_driver')}")
    print(f"\n  Recommended action:")
    print(f"    → {why.get('recommended_action', '—')}")
    if r.get("high_confidence_drivers"):
        print(f"\n  HIGH confidence features: {r['high_confidence_drivers']}")
    print(f"{'─'*60}")


def _print_summary(summary: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  PHASE 2 XAI COMPLETE")
    print(f"{'='*60}")
    print(f"  Model:           {summary['model_name']}")
    print(f"  Primary method:  {summary['primary_method']}")
    print(f"  Watchlist size:  {summary['watchlist_size']}")
    print(f"  Confidence:")
    cs = summary.get("confidence_summary", {})
    print(f"    HIGH:   {cs.get('HIGH', 0)} features")
    print(f"    MEDIUM: {cs.get('MEDIUM', 0)} features")
    print(f"    LOW:    {cs.get('LOW', 0)} features")
    print(f"    Trust score: {cs.get('trust_score', 0):.3f}")
    print(f"  Runtime:         {summary['runtime_seconds']}s")
    print(f"  Artifacts → {summary['output_dir']}")
    print(f"\n  Next → Phase 3: Cohort & Segmentation Engine")


# ── JSON helper ────────────────────────────────────────────────────────────
def _save_json(obj, path: Path) -> None:
    """Save object as JSON. Handles numpy types."""
    class NumpyEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.integer,)): return int(o)
            if isinstance(o, (np.floating,)): return float(o)
            if isinstance(o, np.ndarray):    return o.tolist()
            return super().default(o)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, cls=NumpyEncoder)


# ── Main orchestrator ──────────────────────────────────────────────────────
def run_xai(
    data_dir:    Path = DEFAULT_DATA_DIR,
    models_dir:  Path = DEFAULT_MODELS_DIR,
    output_dir:  Path = DEFAULT_XAI_DIR,
    customer_id: str  = None,
    batch_size:  int  = None,
    sample_size: int  = None,
    max_watchlist: int = 200,
) -> dict:
    """
    Full Phase 2 XAI pipeline.

    Args:
        data_dir:     Path to data/ (contains customers.csv)
        models_dir:   Path to models/ (Phase 1 artifacts)
        output_dir:   Where to save XAI outputs
        customer_id:  If set, explain only this customer
        batch_size:   If set, explain first N at-risk customers
        sample_size:  Limit data loaded (for dev/testing)
        max_watchlist: Max customers to explain in watchlist mode

    Returns:
        summary dict
    """
    t0 = time.time()

    print("\n" + "="*60)
    print("  CUSTOMER HEALTH FORENSICS — PHASE 2")
    print("  XAI Consensus Engine")
    print("="*60)

    # ── Load Phase 1 artifacts ─────────────────────────────────────────────
    arts         = load_phase1_artifacts(models_dir)
    model        = arts["model"]
    model_info   = arts["model_info"]
    feature_names = arts["feature_names"]

    # ── Load data ─────────────────────────────────────────────────────────
    df_test, X_test, y_test, customer_ids = load_data_for_xai(
        data_dir, models_dir, sample_size
    )

    # ── Build predictions ─────────────────────────────────────────────────
    print(f"\n[xai_runner] Generating predictions...")
    churn_probs = get_predictions(model, X_test)

    # ── Build XAI engine ─────────────────────────────────────────────────
    # Use training portion for background + AIX360 fitting
    # (Recover from test split — use the 80% train+val portion)
    df_full = pd.read_csv(data_dir / "customers.csv",
                          nrows=sample_size if sample_size else None)
    df_train_full, _ = train_test_split(
        df_full, test_size=0.20, stratify=df_full["churned"], random_state=42
    )

    X_train_full, y_train_full = build_feature_matrix(df_train_full)
    X_train_full = X_train_full.reindex(columns=feature_names, fill_value=0)
    y_train_full = y_train_full.reset_index(drop=True)

    print(f"\n[xai_runner] Building XAI engine...")
    engine = XAIEngine(
        model         = model,
        X_train       = X_train_full,
        y_train       = y_train_full,
        feature_names = feature_names,
        verbose       = True,
    )

    # ── Route: single customer, batch, or full watchlist ──────────────────
    if customer_id:
        run_single_customer(engine, customer_id, X_test,
                            customer_ids, churn_probs, output_dir)
        summary = {
            "mode": "single_customer",
            "customer_id": customer_id,
            "model_name": model_info["best_model_name"],
            "primary_method": engine._method_name(),
            "output_dir": str(output_dir),
            "runtime_seconds": round(time.time() - t0, 1),
        }
    else:
        # Global explanation (always)
        global_exp, global_reason = run_global_explanation(
            engine, X_test, df_test, output_dir
        )

        # Watchlist (Critical tier) explanation
        n_to_explain = batch_size if batch_size else max_watchlist
        explanations, reasonings = run_watchlist_explanation(
            engine       = engine,
            X_test       = X_test,
            churn_probs  = churn_probs,
            customer_ids = customer_ids,
            df_test      = df_test,
            output_dir   = output_dir,
            max_watchlist = n_to_explain,
        )

        # Confidence summary
        conf_summary = confidence_summary(explanations)
        _save_json(conf_summary, output_dir / "confidence_summary.json")

        # Risk tier distribution
        n_critical = int((churn_probs >= 0.70).sum())
        n_high     = int(((churn_probs >= 0.50) & (churn_probs < 0.70)).sum())
        n_medium   = int(((churn_probs >= 0.30) & (churn_probs < 0.50)).sum())
        n_safe     = int((churn_probs < 0.30).sum())

        summary = {
            "phase":            2,
            "model_name":       model_info["best_model_name"],
            "primary_method":   engine._method_name(),
            "total_customers":  len(X_test),
            "risk_distribution": {
                "critical": n_critical,
                "high":     n_high,
                "medium":   n_medium,
                "safe":     n_safe,
            },
            "watchlist_size":     len(explanations),
            "confidence_summary": conf_summary,
            "output_dir":         str(output_dir),
            "runtime_seconds":    round(time.time() - t0, 1),
        }
        _save_json(summary, output_dir / "xai_summary.json")
        _print_summary(summary)

    return summary


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 2 XAI Consensus Engine — Customer Health Forensics"
    )
    parser.add_argument("--models-dir",  type=str, default=None)
    parser.add_argument("--data-dir",    type=str, default=None)
    parser.add_argument("--output-dir",  type=str, default=None)
    parser.add_argument("--customer-id", type=str, default=None,
                        help="Explain a single customer by ID.")
    parser.add_argument("--batch",       type=int, default=None,
                        help="Explain first N at-risk customers.")
    parser.add_argument("--sample",      type=int, default=None,
                        help="Limit data to N rows (dev/testing).")
    parser.add_argument("--max-watchlist", type=int, default=200,
                        help="Max Critical-tier customers to explain (default: 200).")
    parser.add_argument("--list-questions", action="store_true",
                        help="Print all supported WHAT/WHY questions and exit.")

    args = parser.parse_args()

    if args.list_questions:
        list_supported_questions()
        sys.exit(0)

    run_xai(
        data_dir     = Path(args.data_dir)   if args.data_dir   else DEFAULT_DATA_DIR,
        models_dir   = Path(args.models_dir) if args.models_dir else DEFAULT_MODELS_DIR,
        output_dir   = Path(args.output_dir) if args.output_dir else DEFAULT_XAI_DIR,
        customer_id  = args.customer_id,
        batch_size   = args.batch,
        sample_size  = args.sample,
        max_watchlist = args.max_watchlist,
    )
