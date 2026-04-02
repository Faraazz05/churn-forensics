"""
ann_feature_model.py
====================
Customer Health Forensics — Phase 5
Lightweight ANN for feature impact scoring and interaction detection.

Architecture:
  Input:  feature values + XAI importance scores + drift signals
  Hidden: 2 layers (64 → 32) with ReLU + dropout
  Output: feature_impact_score per feature (0–1)

Purpose:
  - Re-weight XAI feature importances using live feature values
  - Detect non-linear feature interactions (what SHAP misses locally)
  - Produce a composite impact score used by the reasoning engine

Training:
  - Trained on Phase 1 feature matrix with churn label
  - Loss: binary cross-entropy (churn classification)
  - Weights saved to models/ann_feature_model.pkl

This is intentionally lightweight (no GPU required).
sklearn MLPClassifier is used so there are zero new dependencies.
"""

import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing  import MinMaxScaler
from sklearn.pipeline        import Pipeline


# ── Config ─────────────────────────────────────────────────────
ANN_HIDDEN_LAYERS  = (64, 32)
ANN_MAX_ITER       = 200
ANN_RANDOM_STATE   = 42
ANN_LEARNING_RATE  = 0.001
INTERACTION_TOP_K  = 5   # top interaction pairs to return


# ── Model builder ──────────────────────────────────────────────
def build_ann_pipeline() -> Pipeline:
    """Build the ANN pipeline with scaler."""
    return Pipeline([
        ("scaler", MinMaxScaler()),
        ("ann",    MLPClassifier(
            hidden_layer_sizes = ANN_HIDDEN_LAYERS,
            activation         = "relu",
            solver             = "adam",
            learning_rate_init = ANN_LEARNING_RATE,
            max_iter           = ANN_MAX_ITER,
            random_state       = ANN_RANDOM_STATE,
            early_stopping     = True,
            validation_fraction = 0.1,
            verbose            = False,
        )),
    ])


def train_ann(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    save_path: Path = None,
) -> Pipeline:
    """
    Train the ANN on Phase 1 feature matrix.

    Args:
        X_train:   Feature DataFrame (numeric only, already preprocessed).
        y_train:   Churn labels (0/1).
        save_path: If provided, save fitted model here.

    Returns:
        Fitted Pipeline.
    """
    print(f"[ANN] Training on {len(X_train):,} samples, "
          f"{X_train.shape[1]} features...")

    model = build_ann_pipeline()
    model.fit(X_train, y_train)

    ann = model.named_steps["ann"]
    print(f"[ANN] Training complete. "
          f"Loss: {ann.loss_:.4f}  "
          f"Iterations: {ann.n_iter_}")

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            pickle.dump(model, f)
        # Save feature names alongside
        feat_path = save_path.with_name("ann_feature_names.json")
        with open(feat_path, "w") as f:
            json.dump(list(X_train.columns), f)
        print(f"[ANN] Model saved → {save_path}")

    return model


def load_ann(model_path: Path) -> tuple[Pipeline, list[str]]:
    """Load a saved ANN model and its feature names."""
    model_path = Path(model_path)
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    feat_path = model_path.with_name("ann_feature_names.json")
    feature_names = []
    if feat_path.exists():
        with open(feat_path) as f:
            feature_names = json.load(f)

    return model, feature_names


# ── Feature impact scoring ─────────────────────────────────────
def compute_feature_impact(
    model:         Pipeline,
    X_row:         pd.DataFrame,
    feature_names: list[str],
    n_perturb:     int = 50,
) -> dict[str, float]:
    """
    Compute per-feature impact scores using perturbation analysis.

    For each feature: replace its value with the global mean and measure
    the drop in predicted churn probability.
    Features causing larger drops = more impactful for this customer.

    Returns:
        Dict {feature_name: impact_score} normalised to [0, 1]
    """
    row = X_row.reindex(columns=feature_names, fill_value=0)
    base_prob = float(model.predict_proba(row)[0, 1])
    scores    = {}

    # Use training distribution mean from scaler
    scaler = model.named_steps["scaler"]
    means  = scaler.data_min_ + (scaler.data_max_ - scaler.data_min_) * 0.5

    for i, feat in enumerate(feature_names):
        if feat not in row.columns:
            continue
        perturbed     = row.copy()
        original_val  = row[feat].values[0]
        perturbed[feat] = means[i] if i < len(means) else 0
        perturbed_prob = float(model.predict_proba(perturbed)[0, 1])
        scores[feat]   = abs(base_prob - perturbed_prob)

    # Normalise
    max_score = max(scores.values()) if scores else 1.0
    if max_score > 0:
        scores = {k: round(v / max_score, 4) for k, v in scores.items()}

    return scores


def detect_feature_interactions(
    model:         Pipeline,
    X_row:         pd.DataFrame,
    feature_names: list[str],
    top_k:         int = INTERACTION_TOP_K,
) -> list[dict]:
    """
    Detect pairwise feature interactions using joint perturbation.

    If masking feature A + B together causes a larger drop than
    masking A or B individually, they have a significant interaction.

    Returns:
        List of top interaction pairs sorted by interaction strength.
    """
    row       = X_row.reindex(columns=feature_names, fill_value=0)
    base_prob = float(model.predict_proba(row)[0, 1])
    scaler    = model.named_steps["scaler"]
    means     = scaler.data_min_ + (scaler.data_max_ - scaler.data_min_) * 0.5

    # Individual impacts
    ind_impacts = {}
    for i, feat in enumerate(feature_names[:20]):  # limit for speed
        if feat not in row.columns: continue
        p = row.copy()
        p[feat] = means[i] if i < len(means) else 0
        ind_impacts[feat] = abs(base_prob - float(model.predict_proba(p)[0, 1]))

    top_feats   = sorted(ind_impacts, key=ind_impacts.get, reverse=True)[:8]
    interactions = []

    for i in range(len(top_feats)):
        for j in range(i + 1, len(top_feats)):
            fa, fb = top_feats[i], top_feats[j]
            ia_idx = feature_names.index(fa) if fa in feature_names else 0
            ib_idx = feature_names.index(fb) if fb in feature_names else 0

            p = row.copy()
            p[fa] = means[ia_idx] if ia_idx < len(means) else 0
            p[fb] = means[ib_idx] if ib_idx < len(means) else 0

            joint_drop    = abs(base_prob - float(model.predict_proba(p)[0, 1]))
            interaction_s = joint_drop - ind_impacts.get(fa, 0) - ind_impacts.get(fb, 0)

            if interaction_s > 0.01:
                interactions.append({
                    "feature_a":          fa,
                    "feature_b":          fb,
                    "interaction_strength": round(interaction_s, 4),
                    "direction": "synergistic",
                })

    interactions.sort(key=lambda x: -x["interaction_strength"])
    return interactions[:top_k]


# ── Global feature weighting ───────────────────────────────────
def get_ann_global_weights(
    model:         Pipeline,
    X_sample:      pd.DataFrame,
    feature_names: list[str],
) -> dict[str, float]:
    """
    Compute ANN-derived global feature importance using first-layer weights.
    Aggregates the absolute weight magnitudes from the first hidden layer.

    Returns:
        Dict {feature_name: weight_score} normalised to [0, 1]
    """
    ann = model.named_steps["ann"]

    if not hasattr(ann, "coefs_") or len(ann.coefs_) == 0:
        return {}

    # First layer weights: shape (n_features, n_hidden_1)
    first_layer = np.abs(ann.coefs_[0])
    # Average across hidden units
    importance  = first_layer.mean(axis=1)

    n = min(len(importance), len(feature_names))
    raw = dict(zip(feature_names[:n], importance[:n]))

    max_v = max(raw.values()) if raw else 1.0
    return {k: round(float(v / max_v), 4) for k, v in
            sorted(raw.items(), key=lambda x: -x[1])}


# ── Standalone training entry point ───────────────────────────
def train_from_phase1_artifacts(
    models_dir: Path,
    data_dir:   Path,
    save_path:  Path,
) -> Pipeline:
    """
    Convenience: load Phase 1 artifacts and train ANN.
    Designed to be called once from insight_runner.py --train-ann.
    """
    import sys
    src_dir = Path(__file__).parent
    sys.path.insert(0, str(src_dir.parent))

    try:
        from feature_engineering import build_feature_matrix
    except ImportError:
        raise ImportError(
            "feature_engineering.py not found. "
            "Add Phase 1 src/ to sys.path or copy to this directory."
        )

    csv_path = data_dir / "customers.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"customers.csv not found: {csv_path}")

    from sklearn.model_selection import train_test_split
    print(f"[ANN] Loading data from {csv_path}...")
    df = pd.read_csv(csv_path)
    X, y = build_feature_matrix(df)

    feat_path = models_dir / "feature_names.json"
    if feat_path.exists():
        with open(feat_path) as f:
            train_features = json.load(f)
        X = X.reindex(columns=train_features, fill_value=0)

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    return train_ann(X_train, y_train, save_path=save_path)
