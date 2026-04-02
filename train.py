"""
train.py
========
Customer Health Forensics System — Phase 1
Standalone training script — replaces the Colab notebook for repo use.

What this does (mirrors notebook Steps 4 + 5):
  1. Generates 500k synthetic customer dataset (or loads existing)
  2. Engineers features via the modular registry
  3. Splits: stratified 70 / 10 / 20
  4. Trains size-aware candidate models
  5. Selects best model using XAI-coupled logic
  6. Saves all artifacts to --models-dir

Artifacts saved:
  models/best_model.pkl              ← load this for inference + Phase 2 XAI
  models/best_model_info.json        ← selection metadata
  models/leaderboard.csv             ← all models + AUC/F1
  models/logistic_coefficients.csv   ← LR weights (XAI reference)
  models/feature_names.json          ← exact feature list used
  models/phase1_summary.json         ← full run summary
  data/customers.csv                 ← generated dataset
  data/customers_snapshots.csv       ← 12-month snapshots (drift detection)

Usage:
  # Smoke test (fast, 10k rows):
  python train.py --sample 10000

  # Full 500k run:
  python train.py

  # Skip regenerating data if customers.csv already exists:
  python train.py --skip-generate

  # Custom paths (e.g. Google Drive on Colab):
  python train.py --data-dir /content/drive/MyDrive/churn/data \\
                  --models-dir /content/drive/MyDrive/churn/models

  # Colab one-liner (full run, Drive mounted):
  python train.py --data-dir /content/drive/MyDrive/CustomerHealth/data \\
                  --models-dir /content/drive/MyDrive/CustomerHealth/models \\
                  --output-dir /content/drive/MyDrive/CustomerHealth/outputs
"""

import argparse
import json
import sys
import time
from pathlib import Path

# ── Path setup ─────────────────────────────────────────────────────────────
# Works whether train.py is in root/, src/, or anywhere else.
HERE = Path(__file__).resolve().parent
SRC  = HERE / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from data_generator      import generate_main_dataset, generate_snapshot_dataset, validate_dataset
from feature_engineering import add_features, build_feature_matrix, validate_features, get_feature_names
from model               import get_candidates, get_xai_method, extract_logistic_coefs, XAI_COUPLING_DELTA
from model_selector      import run_model_selection


# ── Defaults ──────────────────────────────────────────────────────────────
DEFAULT_DATA_DIR   = HERE / "data"
DEFAULT_MODELS_DIR = HERE / "models"
DEFAULT_OUTPUT_DIR = HERE / "outputs"


# ── Training steps ─────────────────────────────────────────────────────────
def step_data(data_dir: Path, skip_generate: bool, sample_size: int | None) -> pd.DataFrame:
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "customers.csv"

    if not skip_generate or not csv_path.exists():
        generate_main_dataset(csv_path, verbose=True)
    else:
        print(f"[train] Skipping generation — using: {csv_path}")

    if sample_size:
        print(f"[train] Loading sample: {sample_size:,} rows")
        df = pd.read_csv(csv_path, nrows=sample_size)
    else:
        print(f"[train] Loading full dataset...")
        df = pd.read_csv(csv_path)

    validate_dataset(df, label="train")
    print(f"[train] Loaded {len(df):,} rows | churn_rate={df['churned'].mean():.3f}")
    return df


def step_features(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n[train] Validating feature engineering...")
    validate_features(df.sample(min(2000, len(df)), random_state=42))

    print(f"[train] Computing features on {len(df):,} rows...")
    df_feat = add_features(df)
    print(f"[train] {len(get_feature_names())} engineered features | "
          f"total columns: {len(df_feat.columns)}")
    return df_feat


def step_split(df_feat: pd.DataFrame):
    df_tv, df_test = train_test_split(
        df_feat, test_size=0.20, stratify=df_feat["churned"], random_state=42
    )
    df_train, df_val = train_test_split(
        df_tv, test_size=0.125, stratify=df_tv["churned"], random_state=42
    )

    print(f"\n[train] Stratified 70/10/20 split:")
    for tag, part in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
        print(f"  {tag:5s} {len(part):>7,} rows | churn={part['churned'].mean():.3f}")

    return df_train, df_val, df_test


def step_matrices(df_train, df_val, df_test, models_dir: Path):
    X_train, y_train = build_feature_matrix(df_train)
    X_val,   y_val   = build_feature_matrix(df_val)
    X_test,  y_test  = build_feature_matrix(df_test)

    # Align val/test to train column set (get_dummies can vary across splits)
    X_val  = X_val.reindex(columns=X_train.columns,  fill_value=0)
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    print(f"\n[train] Feature matrix: {X_train.shape[1]} columns")

    models_dir.mkdir(parents=True, exist_ok=True)
    feat_path = models_dir / "feature_names.json"
    with open(feat_path, "w") as f:
        json.dump(list(X_train.columns), f, indent=2)
    print(f"[train] Feature names saved → {feat_path}")

    return X_train, y_train, X_val, y_val, X_test, y_test


def step_snapshots(data_dir: Path, sample_size: int | None) -> None:
    if sample_size is not None:
        print(f"\n[train] Snapshots skipped (sample mode)")
        return

    snap_path = data_dir / "customers_snapshots.csv"
    if snap_path.exists():
        print(f"\n[train] Snapshots already exist: {snap_path}")
        return

    print(f"\n[train] Generating 12-month snapshots for drift detection...")
    generate_snapshot_dataset(snap_path, data_dir / "customers.csv", verbose=True)


# ── Main ───────────────────────────────────────────────────────────────────
def train(
    data_dir:      Path = DEFAULT_DATA_DIR,
    models_dir:    Path = DEFAULT_MODELS_DIR,
    output_dir:    Path = DEFAULT_OUTPUT_DIR,
    skip_generate: bool = False,
    sample_size:   int | None = None,
    verbose:       bool = True,
) -> dict:
    """
    Run the full Phase 1 training pipeline.

    Returns:
        summary dict — also saved to models/phase1_summary.json
    """
    t0 = time.time()

    print("\n" + "="*58)
    print("  CUSTOMER HEALTH FORENSICS — TRAIN")
    print("="*58)

    df           = step_data(data_dir, skip_generate, sample_size)
    df_feat      = step_features(df)
    df_train, df_val, df_test = step_split(df_feat)
    X_train, y_train, X_val, y_val, X_test, y_test = step_matrices(
        df_train, df_val, df_test, models_dir
    )

    # ── Model selection (imported from model_selector.py) ─────────────────
    best_model, model_info, leaderboard = run_model_selection(
        X_train, y_train,
        X_val,   y_val,
        X_test,  y_test,
        dataset_size=len(df),
        models_dir=models_dir,
    )

    # ── Snapshots ─────────────────────────────────────────────────────────
    step_snapshots(data_dir, sample_size)

    # ── Summary ───────────────────────────────────────────────────────────
    elapsed = round(time.time() - t0, 1)
    summary = {
        **model_info,
        "phase":                 1,
        "script":                "train.py",
        "runtime_seconds":       elapsed,
        "n_engineered_features": len(get_feature_names()),
        "sample_mode":           sample_size is not None,
        "sample_size":           sample_size,
    }

    summary_path = models_dir / "phase1_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*58}")
    print(f"  TRAINING COMPLETE  ({elapsed}s)")
    print(f"{'='*58}")
    print(f"  Best model    : {model_info['best_model_name']}")
    print(f"  Val  AUC/F1   : {model_info['val_auc']:.4f} / {model_info['val_f1']:.4f}")
    print(f"  Test AUC/F1   : {model_info['test_auc']:.4f} / {model_info['test_f1']:.4f}")
    print(f"  XAI method    : {model_info['xai_method']}")
    print(f"  Features      : {model_info['n_features']} "
          f"({summary['n_engineered_features']} engineered)")
    print(f"  Churn rate    : {model_info['churn_rate_train']:.3f}")
    print(f"  Artifacts     → {models_dir}")
    print(f"  Next          → python test.py")

    return summary


# ── CLI ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 1 Training — Customer Health Forensics")

    parser.add_argument("--sample", type=int, default=None,
                        help="Rows to use (e.g. 10000 for smoke test). Default: full 500k.")
    parser.add_argument("--skip-generate", action="store_true",
                        help="Skip data generation if customers.csv already exists.")
    parser.add_argument("--data-dir", type=str, default=None,
                        help="Path to data directory. Default: ./data/")
    parser.add_argument("--models-dir", type=str, default=None,
                        help="Path to models output directory. Default: ./models/")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Path to outputs directory (plots, reports). Default: ./outputs/")

    args = parser.parse_args()

    train(
        data_dir      = Path(args.data_dir)    if args.data_dir    else DEFAULT_DATA_DIR,
        models_dir    = Path(args.models_dir)  if args.models_dir  else DEFAULT_MODELS_DIR,
        output_dir    = Path(args.output_dir)  if args.output_dir  else DEFAULT_OUTPUT_DIR,
        skip_generate = args.skip_generate,
        sample_size   = args.sample,
    )
