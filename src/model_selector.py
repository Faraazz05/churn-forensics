"""
model_selector.py
=================
Customer Health Forensics System — Phase 1

Size-aware model selection with XAI-coupled decision logic.

Design decisions locked before build:
  1. Size tiers determine candidate set:
       <50k   → XGBoost, RandomForest, SVM, Logistic
       <500k  → XGBoost, RandomForest, Logistic
       >=500k → XGBoost, Logistic           (scalability only)

  2. Primary metric: Val AUC. Tiebreaker: Val F1.

  3. XAI-coupling rule: if best_model.val_auc - xgboost.val_auc < 0.01
     → prefer XGBoost (SHAP TreeExplainer is exact + fast on trees).
     Sacrificing <1% AUC for guaranteed explainability is the right trade-off
     in a diagnostic system where clarity > marginal accuracy.

  4. Logistic Regression ALWAYS trained as interpretable baseline.
     Its coefficients are saved regardless of which model wins — they
     provide a linear sanity check for XAI explanations in Phase 2.

  5. SMOTE applied only if churn_rate < 0.20 (at 22% base rate it's not needed;
     imbalanced class_weight="balanced" handles it in the models directly).

Outputs saved to models/:
  best_model.pkl           — fitted best model (joblib)
  best_model_info.json     — selection metadata + XAI method recommendation
  leaderboard.csv          — all trained models + scores
  logistic_coefficients.csv — LR weights for XAI reference
  feature_names.json        — feature list used for training
"""

import json
import time
import joblib
import numpy as np
import pandas as pd
from dataclasses import dataclass, field, asdict
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score

try:
    from xgboost import XGBClassifier
    _XGBOOST_OK = True
except ImportError:
    _XGBOOST_OK = False

try:
    from imblearn.over_sampling import SMOTE
    _SMOTE_OK = True
except ImportError:
    SMOTE = None
    _SMOTE_OK = False


# ── Constants ──────────────────────────────────────────────────────────────
XAI_COUPLING_DELTA = 0.01   # if gap to XGBoost < this, prefer XGBoost
SMOTE_THRESHOLD    = 0.20   # apply SMOTE only if churn_rate below this


# ── Data structures ────────────────────────────────────────────────────────
@dataclass
class ModelResult:
    name:             str
    val_auc:          float
    val_f1:           float
    test_auc:         float
    test_f1:          float
    train_time_s:     float
    xai_method:       str
    selected:         bool  = False
    selection_reason: str   = ""


# ── Model builders ─────────────────────────────────────────────────────────
def _build_xgboost() -> object | None:
    if not _XGBOOST_OK:
        print("  [WARN] XGBoost not installed — skipping. Run: pip install xgboost")
        return None
    return XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method="hist",        # memory-efficient for 500k+
        scale_pos_weight=1,        # class_weight handled separately
        eval_metric="auc",
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )


def _build_random_forest() -> object:
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=20,       # prevents overfitting at large scale
        class_weight="balanced",
        n_jobs=-1,
        random_state=42,
    )


def _build_svm() -> object:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(probability=True, kernel="rbf", C=1.0,
                    class_weight="balanced", random_state=42)),
    ])


def _build_logistic() -> object:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(
            max_iter=1000,
            C=0.1,                 # L2 regularization
            solver="saga",         # efficient for large n
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])


def _xai_method_for(model_name: str) -> str:
    """Return the recommended XAI approach for a given model type."""
    return {
        "xgboost":       "SHAP_TreeExplainer",    # exact, fast, native
        "random_forest": "SHAP_TreeExplainer",     # native tree support
        "logistic":      "logistic_coefficients",  # direct, no SHAP needed
        "svm":           "SHAP_KernelExplainer",   # slow fallback
    }.get(model_name, "SHAP_KernelExplainer")


# ── Size-aware candidate selection ────────────────────────────────────────
def get_candidates(dataset_size: int) -> dict[str, object]:
    """
    Return candidate models based on dataset size.
    SVM is O(n²) — unusable at 50k+.
    RandomForest is memory-heavy — dropped at 500k+.
    Logistic always included as interpretable baseline.
    """
    if dataset_size < 50_000:
        names = ["xgboost", "random_forest", "svm", "logistic"]
    elif dataset_size < 500_000:
        names = ["xgboost", "random_forest", "logistic"]
    else:
        names = ["xgboost", "logistic"]

    builders = {
        "xgboost":       _build_xgboost,
        "random_forest": _build_random_forest,
        "svm":           _build_svm,
        "logistic":      _build_logistic,
    }

    candidates = {}
    for name in names:
        model = builders[name]()
        if model is not None:
            candidates[name] = model

    print(f"  Dataset size {dataset_size:,} → candidates: {list(candidates.keys())}")
    return candidates


# ── SMOTE ─────────────────────────────────────────────────────────────────
def maybe_smote(
    X: pd.DataFrame, y: pd.Series, churn_rate: float
) -> tuple[pd.DataFrame, pd.Series]:
    """Apply SMOTE only when truly needed (churn_rate < 0.20)."""
    if churn_rate >= SMOTE_THRESHOLD:
        print(f"  Churn rate {churn_rate:.3f} >= {SMOTE_THRESHOLD} — "
              f"skipping SMOTE (class_weight='balanced' handles imbalance)")
        return X, y

    if not _SMOTE_OK:
        print(f"  [WARN] imbalanced-learn not installed — skipping SMOTE. "
              f"Run: pip install imbalanced-learn")
        return X, y

    print(f"  Applying SMOTE (churn_rate={churn_rate:.3f} < {SMOTE_THRESHOLD})...")
    sm = SMOTE(random_state=42, sampling_strategy=0.5)
    X_res, y_res = sm.fit_resample(X, y)
    print(f"  SMOTE: {len(X):,} → {len(X_res):,} samples")
    return X_res, y_res


# ── Train + evaluate single model ─────────────────────────────────────────
def train_one(
    name: str, model,
    X_train: pd.DataFrame, y_train: pd.Series,
    X_val:   pd.DataFrame, y_val:   pd.Series,
    X_test:  pd.DataFrame, y_test:  pd.Series,
) -> ModelResult:
    """Train one model, evaluate on val + test, return ModelResult."""
    print(f"\n  ▶ Training {name}...")
    t0 = time.time()
    model.fit(X_train, y_train)
    elapsed = round(time.time() - t0, 1)

    def _metrics(X, y):
        proba = model.predict_proba(X)[:, 1]
        pred  = model.predict(X)
        return round(roc_auc_score(y, proba), 4), round(f1_score(y, pred, zero_division=0), 4)

    val_auc,  val_f1  = _metrics(X_val,  y_val)
    test_auc, test_f1 = _metrics(X_test, y_test)

    print(f"    Val  AUC={val_auc:.4f}  F1={val_f1:.4f}  |  "
          f"Test AUC={test_auc:.4f}  F1={test_f1:.4f}  |  {elapsed}s")

    return ModelResult(
        name=name, val_auc=val_auc, val_f1=val_f1,
        test_auc=test_auc, test_f1=test_f1,
        train_time_s=elapsed, xai_method=_xai_method_for(name),
    )


# ── Selection logic ────────────────────────────────────────────────────────
def select_best(results: list[ModelResult]) -> tuple[ModelResult, str]:
    """
    Apply XAI-coupled selection logic. Returns (winner, reason_string).

    Priority order:
      1. If XGBoost within XAI_COUPLING_DELTA of top → prefer XGBoost.
      2. Highest Val AUC.
      3. Val F1 tiebreaker.
    """
    if not results:
        raise ValueError("No ModelResult objects to select from.")

    # Sort: AUC desc, then F1 desc
    ranked = sorted(results, key=lambda r: (r.val_auc, r.val_f1), reverse=True)
    top    = ranked[0]

    xgb = next((r for r in results if r.name == "xgboost"), None)

    if xgb and xgb.name != top.name:
        delta = top.val_auc - xgb.val_auc
        if delta < XAI_COUPLING_DELTA:
            reason = (
                f"XGBoost preferred over '{top.name}' — "
                f"AUC delta={delta:.4f} < threshold={XAI_COUPLING_DELTA}. "
                f"SHAP TreeExplainer compatibility prioritised (clarity > marginal accuracy). "
                f"XGBoost AUC={xgb.val_auc:.4f}  F1={xgb.val_f1:.4f}"
            )
            xgb.selected = True
            xgb.selection_reason = reason
            return xgb, reason

    # Standard path
    if len(ranked) > 1 and ranked[0].val_auc == ranked[1].val_auc:
        winner = max(ranked[:2], key=lambda r: r.val_f1)
        reason = (
            f"'{winner.name}' selected via F1 tiebreaker — "
            f"AUC tied at {winner.val_auc:.4f}, F1={winner.val_f1:.4f}"
        )
    else:
        winner = top
        reason = (
            f"'{winner.name}' selected — highest Val AUC={winner.val_auc:.4f}, "
            f"F1={winner.val_f1:.4f}"
        )

    winner.selected = True
    winner.selection_reason = reason
    return winner, reason


# ── Logistic coefficient extraction ───────────────────────────────────────
def extract_logistic_coefs(
    logistic_model, feature_names: list[str]
) -> pd.DataFrame:
    """
    Extract Logistic Regression coefficients as interpretability reference.
    Called regardless of which model was selected.
    """
    lr = (logistic_model.named_steps["lr"]
          if hasattr(logistic_model, "named_steps")
          else logistic_model)

    coefs = pd.DataFrame({
        "feature":     feature_names,
        "coefficient": lr.coef_[0],
    })
    coefs["abs_coef"]   = coefs["coefficient"].abs()
    coefs["direction"]  = np.where(coefs["coefficient"] > 0, "risk+", "risk-")
    coefs = coefs.sort_values("abs_coef", ascending=False).round(4)

    print("\n── Logistic Regression Coefficients (top 10) ─────")
    print(coefs[["feature", "coefficient", "direction"]].head(10).to_string(index=False))
    return coefs


# ── Main entry point ───────────────────────────────────────────────────────
def run_model_selection(
    X_train: pd.DataFrame, y_train: pd.Series,
    X_val:   pd.DataFrame, y_val:   pd.Series,
    X_test:  pd.DataFrame, y_test:  pd.Series,
    dataset_size: int,
    models_dir:   Path,
) -> tuple[object, dict, pd.DataFrame]:
    """
    Full model selection pipeline.

    Returns:
        best_model:  fitted estimator (best selected model)
        model_info:  selection metadata dict (saved as best_model_info.json)
        leaderboard: DataFrame of all trained models + metrics
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  MODEL SELECTION PIPELINE")
    print(f"{'='*60}")
    print(f"  Train: {len(X_train):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}")
    print(f"  Features: {X_train.shape[1]}")

    # SMOTE if needed
    churn_rate = float(y_train.mean())
    print(f"  Train churn rate: {churn_rate:.3f}")
    X_tr, y_tr = maybe_smote(X_train, y_train, churn_rate)

    # Build + train candidates
    candidates    = get_candidates(dataset_size)
    trained       = {}
    results       = []

    for name, model in candidates.items():
        result = train_one(name, model, X_tr, y_tr, X_val, y_val, X_test, y_test)
        results.append(result)
        trained[name] = model

    # Select best
    winner, reason = select_best(results)
    best_model     = trained[winner.name]

    print(f"\n{'='*60}")
    print(f"  SELECTED: {winner.name.upper()}")
    print(f"  {reason}")
    print(f"  Test AUC={winner.test_auc:.4f}  Test F1={winner.test_f1:.4f}")
    print(f"{'='*60}")

    # ── Save best model ────────────────────────────────────────────────────
    model_path = models_dir / "best_model.pkl"
    joblib.dump(best_model, model_path)
    print(f"\n  Saved best model → {model_path}")

    # ── Save logistic coefficients (always) ───────────────────────────────
    if "logistic" in trained:
        coef_df   = extract_logistic_coefs(trained["logistic"], list(X_train.columns))
        coef_path = models_dir / "logistic_coefficients.csv"
        coef_df.to_csv(coef_path, index=False)
        print(f"  Saved logistic coefficients → {coef_path}")

    # ── Save feature names (needed by Phase 2 XAI) ────────────────────────
    feat_path = models_dir / "feature_names.json"
    with open(feat_path, "w") as f:
        json.dump(list(X_train.columns), f, indent=2)
    print(f"  Saved feature names → {feat_path}")

    # ── Leaderboard ────────────────────────────────────────────────────────
    leaderboard = (
        pd.DataFrame([asdict(r) for r in results])
        .sort_values(["val_auc", "val_f1"], ascending=False)
        .reset_index(drop=True)
    )
    lb_path = models_dir / "leaderboard.csv"
    leaderboard.to_csv(lb_path, index=False)
    print(f"  Saved leaderboard → {lb_path}")

    # ── model_info dict ────────────────────────────────────────────────────
    model_info = {
        "best_model_name":   winner.name,
        "val_auc":           winner.val_auc,
        "val_f1":            winner.val_f1,
        "test_auc":          winner.test_auc,
        "test_f1":           winner.test_f1,
        "selection_reason":  reason,
        "xai_method":        winner.xai_method,
        "dataset_size":      dataset_size,
        "n_features":        X_train.shape[1],
        "churn_rate_train":  round(churn_rate, 4),
        "smote_applied":     churn_rate < SMOTE_THRESHOLD and _SMOTE_OK,
        "models_trained":    [r.name for r in results],
        "xai_coupling_delta": XAI_COUPLING_DELTA,
    }

    info_path = models_dir / "best_model_info.json"
    with open(info_path, "w") as f:
        json.dump(model_info, f, indent=2)
    print(f"  Saved model info → {info_path}")

    return best_model, model_info, leaderboard
