"""
test.py
=======
Customer Health Forensics System — Phase 1
Standalone evaluation script — replaces notebook Steps 6 + 7.

Loads the trained model from models/ and runs a full evaluation:
  - Classification report (precision, recall, F1 per class)
  - ROC curve + AUC
  - Confusion matrix
  - Leaderboard printout
  - Logistic coefficient table (top 15)
  - Feature registry inspection
  - Saves all plots to outputs/

Run AFTER train.py has completed.

Usage:
  python test.py

  # Custom paths:
  python test.py --models-dir /content/drive/MyDrive/churn/models \\
                 --data-dir   /content/drive/MyDrive/churn/data \\
                 --output-dir /content/drive/MyDrive/churn/outputs

  # Quick check (no plots saved, just prints):
  python test.py --no-plots
"""

import argparse
import json
import sys
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_curve,
    roc_auc_score,
    f1_score,
    auc,
)

from feature_engineering import (
    add_features,
    build_feature_matrix,
    get_feature_names,
    get_feature_docs,
)
from model import extract_logistic_coefs


# ── Defaults ───────────────────────────────────────────────────────────────
DEFAULT_DATA_DIR   = HERE / "data"
DEFAULT_MODELS_DIR = HERE / "models"
DEFAULT_OUTPUT_DIR = HERE / "outputs"


# ── Helpers ────────────────────────────────────────────────────────────────
def _load_artifacts(models_dir: Path) -> dict:
    """Load all Phase 1 artifacts from models/."""
    required = ["best_model.pkl", "best_model_info.json", "feature_names.json"]
    for f in required:
        if not (models_dir / f).exists():
            raise FileNotFoundError(
                f"\n  ✗ Missing: {models_dir / f}"
                f"\n  Run train.py first to generate artifacts."
            )

    best_model = joblib.load(models_dir / "best_model.pkl")
    with open(models_dir / "best_model_info.json") as f:
        model_info = json.load(f)
    with open(models_dir / "feature_names.json") as f:
        feature_names = json.load(f)

    leaderboard = None
    lb_path = models_dir / "leaderboard.csv"
    if lb_path.exists():
        leaderboard = pd.read_csv(lb_path)

    coefs = None
    coef_path = models_dir / "logistic_coefficients.csv"
    if coef_path.exists():
        coefs = pd.read_csv(coef_path)

    return {
        "best_model":   best_model,
        "model_info":   model_info,
        "feature_names": feature_names,
        "leaderboard":  leaderboard,
        "coefs":        coefs,
    }


def _load_test_data(data_dir: Path, models_dir: Path, sample_size: int | None = None) -> tuple:
    """
    Load data, engineer features, build test matrix.
    Aligns to the exact feature columns used during training.
    """
    csv_path = data_dir / "customers.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"  ✗ Data not found: {csv_path}\n"
            f"  Run train.py first."
        )

    print(f"[test] Loading data from {csv_path}...")
    if sample_size:
        df = pd.read_csv(csv_path, nrows=sample_size)
    else:
        df = pd.read_csv(csv_path)

    print(f"[test] {len(df):,} rows | churn_rate={df['churned'].mean():.3f}")

    # Use only the 20% test split (consistent with train.py)
    from sklearn.model_selection import train_test_split
    _, df_test = train_test_split(df, test_size=0.20, stratify=df["churned"], random_state=42)
    print(f"[test] Test split: {len(df_test):,} rows")

    X_test, y_test = build_feature_matrix(df_test)

    # Load exact training feature list and align
    with open(models_dir / "feature_names.json") as f:
        train_features = json.load(f)

    X_test = X_test.reindex(columns=train_features, fill_value=0)
    return X_test, y_test, df_test


# ── Evaluation sections ────────────────────────────────────────────────────
def section_header(title: str) -> None:
    print(f"\n{'─'*58}")
    print(f"  {title}")
    print(f"{'─'*58}")


def eval_model_info(model_info: dict) -> None:
    section_header("MODEL SELECTION SUMMARY")
    print(f"  Best model     : {model_info['best_model_name']}")
    print(f"  Val  AUC       : {model_info['val_auc']:.4f}")
    print(f"  Val  F1        : {model_info['val_f1']:.4f}")
    print(f"  Test AUC       : {model_info['test_auc']:.4f}")
    print(f"  Test F1        : {model_info['test_f1']:.4f}")
    print(f"  XAI method     : {model_info['xai_method']}")
    print(f"  Features       : {model_info['n_features']}")
    print(f"  Dataset size   : {model_info['dataset_size']:,}")
    print(f"  Churn rate     : {model_info['churn_rate_train']:.3f}")
    print(f"  Selection      : {model_info['selection_reason']}")


def eval_classification(best_model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    section_header("CLASSIFICATION REPORT")
    y_pred = best_model.predict(X_test)
    y_prob = best_model.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred, target_names=["No Churn", "Churn"])
    print(report)

    live_auc = roc_auc_score(y_test, y_prob)
    live_f1  = f1_score(y_test, y_pred)
    print(f"  Live AUC (test set): {live_auc:.4f}")
    print(f"  Live F1  (test set): {live_f1:.4f}")

    return {
        "y_pred": y_pred,
        "y_prob": y_prob,
        "report": report,
        "live_auc": live_auc,
        "live_f1":  live_f1,
    }


def eval_leaderboard(leaderboard: pd.DataFrame | None) -> None:
    section_header("MODEL LEADERBOARD")
    if leaderboard is None:
        print("  leaderboard.csv not found — skipping.")
        return

    cols = ["name", "val_auc", "val_f1", "test_auc", "test_f1",
            "train_time_s", "xai_method", "selected"]
    display_cols = [c for c in cols if c in leaderboard.columns]
    print(leaderboard[display_cols].to_string(index=False))


def eval_logistic_coefs(coefs: pd.DataFrame | None, top_n: int = 15) -> None:
    section_header(f"LOGISTIC REGRESSION COEFFICIENTS (top {top_n})")
    if coefs is None:
        print("  logistic_coefficients.csv not found — skipping.")
        return

    display = coefs[["feature", "coefficient", "direction"]].head(top_n)
    print(display.to_string(index=False))
    print()
    print("  Interpretation:")
    print("    risk+ → increases churn probability")
    print("    risk- → decreases churn probability (protective)")


def eval_feature_registry() -> None:
    section_header("ENGINEERED FEATURE REGISTRY")
    docs = get_feature_docs()
    print(f"  Total registered features: {len(docs)}")
    print()
    for name, desc in docs.items():
        print(f"  {name}")
        print(f"    {desc}")


# ── Plots ──────────────────────────────────────────────────────────────────
def save_plots(
    best_model,
    X_test:     pd.DataFrame,
    y_test:     pd.Series,
    y_prob:     np.ndarray,
    y_pred:     np.ndarray,
    leaderboard: pd.DataFrame | None,
    model_info: dict,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc     = auc(fpr, tpr)
    cm          = confusion_matrix(y_test, y_pred)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle(
        f"Phase 1 Evaluation — {model_info['best_model_name'].upper()} "
        f"(AUC={roc_auc:.4f})",
        fontsize=13, fontweight="bold"
    )

    # ── ROC ───────────────────────────────────────────────────────────────
    ax = axes[0]
    ax.plot(fpr, tpr, color="#1d6fa5", lw=2.5, label=f"AUC = {roc_auc:.4f}")
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.fill_between(fpr, tpr, alpha=0.08, color="#1d6fa5")
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve"); ax.legend(loc="lower right")
    ax.set_xlim([0, 1]); ax.set_ylim([0, 1.02])

    # ── Confusion matrix ──────────────────────────────────────────────────
    ax = axes[1]
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["No Churn", "Churn"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["No Churn", "Churn"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i,j]:,}",
                    ha="center", va="center", fontsize=12, fontweight="bold",
                    color="white" if cm[i, j] > cm.max() / 2 else "black")
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix")

    # ── Leaderboard ───────────────────────────────────────────────────────
    ax = axes[2]
    if leaderboard is not None:
        lb = leaderboard.sort_values("val_auc")
        colors = ["#e05a2b" if s else "#1d6fa5" for s in lb["selected"]]
        bars = ax.barh(lb["name"], lb["val_auc"], color=colors, edgecolor="white")
        for bar, val in zip(bars, lb["val_auc"]):
            ax.text(bar.get_width() + 0.002,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.4f}", va="center", fontsize=9)
        ax.set_xlim([lb["val_auc"].min() - 0.05, 1.0])
        ax.set_xlabel("Val AUC")
        ax.set_title("Model Leaderboard")
        ax.legend(handles=[
            plt.Rectangle((0,0),1,1, color="#e05a2b", label="Selected"),
            plt.Rectangle((0,0),1,1, color="#1d6fa5", label="Not selected"),
        ], loc="lower right", fontsize=8)
    else:
        ax.text(0.5, 0.5, "leaderboard.csv\nnot found",
                ha="center", va="center", transform=ax.transAxes)

    plt.tight_layout()
    plot_path = output_dir / "phase1_evaluation.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n[test] Plot saved → {plot_path}")


# ── Main ───────────────────────────────────────────────────────────────────
def test(
    data_dir:   Path = DEFAULT_DATA_DIR,
    models_dir: Path = DEFAULT_MODELS_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    save_plots_flag: bool = True,
    sample_size: int | None = None,
) -> dict:
    """
    Run full Phase 1 evaluation on the trained model.

    Returns:
        results dict with live AUC, F1, classification report
    """
    print("\n" + "="*58)
    print("  CUSTOMER HEALTH FORENSICS — TEST")
    print("="*58)

    # ── Load artifacts ─────────────────────────────────────────────────────
    print(f"\n[test] Loading artifacts from {models_dir}...")
    arts = _load_artifacts(models_dir)
    best_model   = arts["best_model"]
    model_info   = arts["model_info"]
    leaderboard  = arts["leaderboard"]
    coefs        = arts["coefs"]

    # ── Load + prepare test data ───────────────────────────────────────────
    X_test, y_test, _ = _load_test_data(data_dir, models_dir, sample_size)

    # ── Evaluation sections ────────────────────────────────────────────────
    eval_model_info(model_info)
    eval_results = eval_classification(best_model, X_test, y_test)
    eval_leaderboard(leaderboard)
    eval_logistic_coefs(coefs)
    eval_feature_registry()

    # ── Plots ──────────────────────────────────────────────────────────────
    if save_plots_flag:
        save_plots(
            best_model=best_model,
            X_test=X_test, y_test=y_test,
            y_prob=eval_results["y_prob"],
            y_pred=eval_results["y_pred"],
            leaderboard=leaderboard,
            model_info=model_info,
            output_dir=output_dir,
        )

    # ── Save text report ───────────────────────────────────────────────────
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "test_report.txt"
    with open(report_path, "w") as f:
        f.write(f"Model: {model_info['best_model_name']}\n")
        f.write(f"Selection: {model_info['selection_reason']}\n\n")
        f.write(eval_results["report"])
        f.write(f"\nLive AUC: {eval_results['live_auc']:.4f}\n")
        f.write(f"Live F1 : {eval_results['live_f1']:.4f}\n")
    print(f"[test] Report saved → {report_path}")

    results = {
        "model_name": model_info["best_model_name"],
        "live_auc":   eval_results["live_auc"],
        "live_f1":    eval_results["live_f1"],
        "xai_method": model_info["xai_method"],
    }

    print(f"\n{'='*58}")
    print(f"  TEST COMPLETE")
    print(f"{'='*58}")
    print(f"  Model    : {results['model_name']}")
    print(f"  AUC      : {results['live_auc']:.4f}")
    print(f"  F1       : {results['live_f1']:.4f}")
    print(f"  Next     → Phase 2: python src/xai_engine.py")

    return results


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 1 Evaluation — Customer Health Forensics")

    parser.add_argument("--models-dir", type=str, default=None,
                        help="Path to models directory. Default: ./models/")
    parser.add_argument("--data-dir", type=str, default=None,
                        help="Path to data directory. Default: ./data/")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Path to outputs directory. Default: ./outputs/")
    parser.add_argument("--no-plots", action="store_true",
                        help="Skip saving evaluation plots.")
    parser.add_argument("--sample", type=int, default=None,
                        help="Use N rows for quick eval (loads from existing data).")

    args = parser.parse_args()

    test(
        data_dir        = Path(args.data_dir)   if args.data_dir   else DEFAULT_DATA_DIR,
        models_dir      = Path(args.models_dir) if args.models_dir else DEFAULT_MODELS_DIR,
        output_dir      = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR,
        save_plots_flag = not args.no_plots,
        sample_size     = args.sample,
    )
