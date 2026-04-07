"""
pipeline.py
===========
Customer Health Forensics System — Phase 1
Full orchestrator: data → features → split → model selection → artifacts.

This is the single entry point for Phase 1.
Run directly or import run_phase1() from other scripts (e.g. Colab notebook).

Usage:
    # Full 500k run (use on Colab T4):
    python pipeline.py

    # Fast dev/smoke run (10k rows, ~30 seconds):
    python pipeline.py --sample 10000

    # Skip data generation if customers.csv already exists:
    python pipeline.py --skip-generate

    # Custom output directory:
    python pipeline.py --output-dir /content/drive/MyDrive/churn_project
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Local imports ──────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent))

from data_generator      import generate_main_dataset, generate_snapshot_dataset, \
                                generate_snapshots_standalone, validate_dataset
from feature_engineering import add_features, build_feature_matrix, validate_features, get_feature_names
from model_selector      import run_model_selection


# ── Defaults ──────────────────────────────────────────────────────────────
DEFAULT_DATA_DIR   = Path(__file__).parent.parent / "data"
DEFAULT_MODELS_DIR = Path(__file__).parent.parent / "models"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "outputs"


# ── Step helpers ──────────────────────────────────────────────────────────
def step_data(
    data_dir: Path,
    skip_generate: bool,
    sample_size: int | None,
) -> pd.DataFrame:
    """Load or generate the dataset."""
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "customers.csv"

    if not skip_generate or not csv_path.exists():
        generate_main_dataset(csv_path, verbose=True)
    else:
        print(f"  [Data] Using existing dataset: {csv_path}")

    if sample_size:
        print(f"  [Data] Sampling {sample_size:,} rows for dev run...")
        df = pd.read_csv(csv_path, nrows=sample_size)
    else:
        print(f"  [Data] Loading full dataset...")
        df = pd.read_csv(csv_path)

    validate_dataset(df, label="Main dataset")
    return df


def step_features(df: pd.DataFrame) -> pd.DataFrame:
    """Validate + apply all registered engineered features."""
    print(f"\n  [Features] Validating feature engineering on sample...")
    validate_features(df.sample(min(2000, len(df)), random_state=42))

    print(f"  [Features] Computing features on full dataset ({len(df):,} rows)...")
    df_feat = add_features(df)

    n_eng = len(get_feature_names())
    print(f"  [Features] {n_eng} engineered features added. "
          f"Total columns: {len(df_feat.columns)}")
    return df_feat


def step_split(df_feat: pd.DataFrame) -> tuple:
    """Stratified 70/10/20 train/val/test split."""
    df_tv, df_test = train_test_split(
        df_feat, test_size=0.20, stratify=df_feat["churned"], random_state=42
    )
    df_train, df_val = train_test_split(
        df_tv, test_size=0.125,  # 0.125 * 0.80 = 0.10 of total
        stratify=df_tv["churned"], random_state=42
    )

    print(f"\n  [Split] Stratified 70 / 10 / 20:")
    for name, part in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
        print(f"    {name:5s}: {len(part):>7,} rows | churn={part['churned'].mean():.3f}")

    return df_train, df_val, df_test


def step_matrices(
    df_train: pd.DataFrame,
    df_val:   pd.DataFrame,
    df_test:  pd.DataFrame,
    models_dir: Path,
) -> tuple:
    """Build feature matrices, align columns, save feature list."""
    X_train, y_train = build_feature_matrix(df_train)
    X_val,   y_val   = build_feature_matrix(df_val)
    X_test,  y_test  = build_feature_matrix(df_test)

    # Align val/test to train's column set (get_dummies can vary across splits)
    X_val  = X_val.reindex(columns=X_train.columns,  fill_value=0)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    print(f"\n  [Matrices] Feature matrix: {X_train.shape[1]} columns")

    # Save for Phase 2
    models_dir.mkdir(parents=True, exist_ok=True)
    feat_path = models_dir / "feature_names.json"
    with open(feat_path, "w") as f:
        json.dump(list(X_train.columns), f, indent=2)

    return X_train, y_train, X_val, y_val, X_test, y_test


def step_snapshots(data_dir: Path, sample_size: int | None) -> None:
    """Generate 12-month snapshot dataset for drift detection (Phase 4).
    
    Works in both full and sample mode:
      - Full mode:   uses customers.csv as base → 12 months × 500k = 6M rows
      - Sample mode:  generates standalone snapshots → 12 months × sample_size rows
    """
    snap_path = data_dir / "customers_snapshots.csv"
    base_path = data_dir / "customers.csv"

    if snap_path.exists():
        # Verify it actually has multiple months
        import csv
        with open(snap_path, "r") as f:
            reader = csv.DictReader(f)
            months_found = set()
            for i, row in enumerate(reader):
                months_found.add(row.get("snapshot_month"))
                if len(months_found) > 1 or i > 10000:
                    break
        if len(months_found) > 1:
            print(f"\n  [Snapshots] Already exists with multiple months: {snap_path}")
            return
        else:
            print(f"\n  [Snapshots] Existing file only has 1 month — regenerating...")

    if sample_size is not None:
        # Sample mode: generate standalone snapshots (no dependency on customers.csv)
        print(f"\n  [Snapshots] Generating 12-month snapshots (sample mode: "
              f"{sample_size:,} customers × 12 months)...")
        generate_snapshots_standalone(
            output_path=snap_path,
            n_customers=sample_size,
            n_months=12,
            verbose=True,
        )
    else:
        # Full mode: use customers.csv as base
        print(f"\n  [Snapshots] Generating 12-month snapshots for drift detection...")
        generate_snapshot_dataset(snap_path, base_path, verbose=True)


def step_plots(
    best_model,
    X_test:     pd.DataFrame,
    y_test:     pd.Series,
    leaderboard: pd.DataFrame,
    output_dir:  Path,
) -> None:
    """Generate evaluation plots: ROC curve, confusion matrix, leaderboard bar."""
    output_dir.mkdir(parents=True, exist_ok=True)

    from sklearn.metrics import roc_curve, auc

    y_prob = best_model.predict_proba(X_test)[:, 1]
    y_pred = best_model.predict(X_test)
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Phase 1 — Model Evaluation", fontsize=14, fontweight="bold")

    # ── ROC curve ─────────────────────────────────────────────────────────
    ax = axes[0]
    ax.plot(fpr, tpr, color="#1d6fa5", lw=2, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])

    # ── Confusion matrix ──────────────────────────────────────────────────
    ax = axes[1]
    cm = confusion_matrix(y_test, y_pred)
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)
    tick_marks = [0, 1]
    ax.set_xticks(tick_marks); ax.set_xticklabels(["No Churn", "Churn"])
    ax.set_yticks(tick_marks); ax.set_yticklabels(["No Churn", "Churn"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i, j]),
                    ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "black",
                    fontsize=12, fontweight="bold")
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")

    # ── Leaderboard bar ───────────────────────────────────────────────────
    ax = axes[2]
    lb_sorted = leaderboard.sort_values("val_auc")
    colors = ["#1d6fa5" if not sel else "#e05a2b"
              for sel in lb_sorted["selected"]]
    bars = ax.barh(lb_sorted["name"], lb_sorted["val_auc"], color=colors)
    ax.set_xlabel("Val AUC")
    ax.set_title("Model Leaderboard")
    ax.set_xlim([lb_sorted["val_auc"].min() - 0.05, 1.0])
    for bar, val in zip(bars, lb_sorted["val_auc"]):
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f"{val:.4f}", va="center", fontsize=9)
    ax.legend(handles=[
        plt.Rectangle((0,0),1,1, color="#e05a2b", label="Selected"),
        plt.Rectangle((0,0),1,1, color="#1d6fa5", label="Not selected"),
    ], loc="lower right", fontsize=8)

    plt.tight_layout()
    plot_path = output_dir / "phase1_evaluation.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  [Plots] Saved → {plot_path}")


def step_report(y_test, best_model, X_test, model_info, output_dir):
    """Print + save classification report."""
    y_pred = best_model.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=["No Churn", "Churn"])
    print(f"\n── Classification Report ({model_info['best_model_name']}) ──────")
    print(report)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "classification_report.txt"
    with open(report_path, "w") as f:
        f.write(f"Model: {model_info['best_model_name']}\n")
        f.write(f"Selection reason: {model_info['selection_reason']}\n\n")
        f.write(report)
    print(f"  [Report] Saved → {report_path}")


# ── Main pipeline ──────────────────────────────────────────────────────────
def run_phase1(
    data_dir:      Path = DEFAULT_DATA_DIR,
    models_dir:    Path = DEFAULT_MODELS_DIR,
    output_dir:    Path = DEFAULT_OUTPUT_DIR,
    skip_generate: bool = False,
    sample_size:   int  | None = None,
) -> dict:
    """
    Execute Phase 1 end-to-end.

    Returns:
        pipeline_summary dict (also saved to models/phase1_summary.json)
    """
    t_start = time.time()

    print("\n" + "="*60)
    print("  CUSTOMER HEALTH FORENSICS — PHASE 1")
    print("  Data Pipeline + ML Model Selection")
    print("="*60)

    # Step 1: Data
    df = step_data(data_dir, skip_generate, sample_size)

    # Step 2: Features
    df_feat = step_features(df)

    # Step 3: Split
    df_train, df_val, df_test = step_split(df_feat)

    # Step 4: Feature matrices
    X_train, y_train, X_val, y_val, X_test, y_test = step_matrices(
        df_train, df_val, df_test, models_dir
    )

    # Step 5: Model selection
    best_model, model_info, leaderboard = run_model_selection(
        X_train, y_train, X_val, y_val, X_test, y_test,
        dataset_size=len(df),
        models_dir=models_dir,
    )

    # Step 6: Plots + report
    step_plots(best_model, X_test, y_test, leaderboard, output_dir)
    step_report(y_test, best_model, X_test, model_info, output_dir)

    # Step 7: Snapshots (full run only)
    step_snapshots(data_dir, sample_size)

    # ── Summary ───────────────────────────────────────────────────────────
    elapsed = round(time.time() - t_start, 1)

    summary = {
        **model_info,
        "phase":              1,
        "runtime_seconds":    elapsed,
        "n_engineered_features": len(get_feature_names()),
        "sample_mode":        sample_size is not None,
        "sample_size":        sample_size,
    }

    summary_path = models_dir / "phase1_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  PHASE 1 COMPLETE  ({elapsed}s)")
    print(f"{'='*60}")
    print(f"  Best model:   {model_info['best_model_name']}")
    print(f"  Val  AUC:     {model_info['val_auc']:.4f}   F1: {model_info['val_f1']:.4f}")
    print(f"  Test AUC:     {model_info['test_auc']:.4f}   F1: {model_info['test_f1']:.4f}")
    print(f"  XAI method:   {model_info['xai_method']}")
    print(f"  Features:     {model_info['n_features']} (incl. {summary['n_engineered_features']} engineered)")
    print(f"  Churn rate:   {model_info['churn_rate_train']:.3f}")
    print(f"\n  Artifacts → {models_dir}")
    print(f"  Next → Phase 2: XAI Consensus Engine (src/xai_engine.py)")

    return summary


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Customer Health Forensics — Phase 1"
    )
    parser.add_argument("--skip-generate", action="store_true",
                        help="Skip data generation if customers.csv already exists")
    parser.add_argument("--sample", type=int, default=None,
                        help="Use N rows for fast dev/smoke run (e.g. --sample 10000)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Override output directory (useful for Colab Drive)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR

    run_phase1(
        skip_generate=args.skip_generate,
        sample_size=args.sample,
        output_dir=output_dir,
    )
