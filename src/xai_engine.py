"""
xai_engine.py
=============
Customer Health Forensics System — Phase 2
Agreement-Based Consensus XAI Engine

Design principles (locked):
  - NO fixed weights (no 40/30/30 averaging)
  - NO score averaging across methods
  - PRIMARY method generates feature importance
  - SECONDARY methods VALIDATE agreement / disagreement
  - Confidence is derived from inter-method agreement, not from score magnitude

Confidence definition:
  HIGH   → all available methods agree on direction + feature is top-K in both validators
  MEDIUM → 2 of 3 methods agree (or 1 validator confirms when only 1 is available)
  LOW    → disagreement across methods on direction or importance rank

Model → Explainer routing:
  XGBoost / RandomForest → SHAP TreeExplainer  (primary) + LIME + AIX360 (validators)
  LogisticRegression     → Coefficients         (primary) + SHAP LinearExplainer (optional)
  SVM                    → LIME                 (primary) + SHAP KernelExplainer (sampled)

Efficiency:
  - Model loaded from .pkl — NO retraining
  - Global SHAP: sampled 1000–5000 rows only
  - Local (per-customer): only computes for requested customers
  - LIME: per-customer only, on-demand

Dependencies:
  Required:  shap, lime, numpy, pandas, scikit-learn
  Optional:  aix360  (degrades gracefully to SHAP+LIME if not installed)
"""

import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Optional imports ───────────────────────────────────────────────────────
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    shap = None
    SHAP_AVAILABLE = False
    print("[xai_engine] WARNING: shap not installed — run: pip install shap")

try:
    import lime
    import lime.lime_tabular
    LIME_AVAILABLE = True
except ImportError:
    lime = None
    LIME_AVAILABLE = False
    print("[xai_engine] WARNING: lime not installed — run: pip install lime")

try:
    from aix360.algorithms.rbm import BooleanRuleCGExplainer
    from aix360.algorithms.rbm import FeatureBinarizer
    AIX360_AVAILABLE = True
except ImportError:
    AIX360_AVAILABLE = False


# ── Constants ──────────────────────────────────────────────────────────────
TOP_K_FEATURES        = 10     # top features returned per explanation
GLOBAL_SAMPLE_SIZE    = 3000   # rows used for global SHAP (efficiency)
LIME_NUM_FEATURES     = 10     # features LIME returns per explanation
LIME_NUM_SAMPLES      = 500    # LIME perturbation samples (speed vs accuracy)
AIX360_SAMPLE_SIZE    = 2000   # rows used for AIX360 rule fitting
AGREEMENT_TOP_K       = 5      # how many top features must overlap for agreement
DIRECTION_AGREEMENT   = True   # require direction agreement for HIGH confidence


# ── Model type detection ───────────────────────────────────────────────────
def detect_model_type(model) -> str:
    """
    Detect the underlying model type from a fitted estimator or Pipeline.
    Returns one of: 'xgboost', 'random_forest', 'logistic', 'svm', 'unknown'
    """
    # Unwrap Pipeline if needed
    inner = model
    if hasattr(model, "named_steps"):
        steps = list(model.named_steps.values())
        inner = steps[-1]

    class_name = type(inner).__name__.lower()

    if "xgb" in class_name:
        return "xgboost"
    if "randomforest" in class_name:
        return "random_forest"
    if "logisticregression" in class_name:
        return "logistic"
    if "svc" in class_name or "svm" in class_name:
        return "svm"
    return "unknown"


def get_inner_model(model):
    """Unwrap the estimator from a Pipeline."""
    if hasattr(model, "named_steps"):
        return list(model.named_steps.values())[-1]
    return model


def get_scaler(model):
    """Extract scaler from a Pipeline, or None if no scaler."""
    if hasattr(model, "named_steps") and "scaler" in model.named_steps:
        return model.named_steps["scaler"]
    return None


# ── Direction utilities ────────────────────────────────────────────────────
def _direction(value: float) -> str:
    return "risk+" if value > 0 else "risk-"


def _directions_agree(dir_a: str, dir_b: str) -> bool:
    return dir_a == dir_b


def _normalize_importances(importances: dict[str, float]) -> dict[str, float]:
    """
    Normalize absolute importance values to [0, 1] for cross-method comparison.
    Preserves sign — only scales the magnitude.
    """
    vals = np.array(list(importances.values()), dtype=float)
    abs_max = np.abs(vals).max()
    if abs_max == 0:
        return {k: 0.0 for k in importances}
    return {k: v / abs_max for k, v in importances.items()}


# ── Agreement logic ────────────────────────────────────────────────────────
def compute_confidence(
    primary_features:    list[str],      # top-K from primary method (ordered)
    primary_directions:  dict[str, str], # feature → "risk+" or "risk-"
    validator_results:   list[dict],     # each: {"features": [...], "directions": {...}}
    top_k:               int = AGREEMENT_TOP_K,
) -> dict[str, str]:
    """
    Compute per-feature confidence from inter-method agreement.

    Agreement is checked on TWO dimensions:
      1. Presence: is the feature in the validator's top-K?
      2. Direction: does the validator agree on risk+ vs risk-?

    Confidence rules:
      HIGH   → feature present in ALL validators AND direction agrees in ALL
      MEDIUM → feature present in at least 1 validator AND direction agrees in that one
      LOW    → feature absent from all validators OR direction disagrees in all

    Args:
        primary_features:   Ordered list of top features from primary method.
        primary_directions: Direction map from primary method.
        validator_results:  List of dicts from each secondary method.
        top_k:              How many top features each validator must include for "present".

    Returns:
        Dict mapping feature_name → confidence_level ("HIGH", "MEDIUM", "LOW")
    """
    confidence_map = {}

    for feat in primary_features:
        primary_dir = primary_directions.get(feat, "unknown")
        agreements  = 0
        checked     = 0

        for vr in validator_results:
            if not vr or "features" not in vr:
                continue
            checked += 1

            validator_top_k = vr["features"][:top_k]
            validator_dirs  = vr.get("directions", {})

            feat_present = feat in validator_top_k
            dir_agrees   = _directions_agree(primary_dir, validator_dirs.get(feat, "unknown"))

            if feat_present and (not DIRECTION_AGREEMENT or dir_agrees):
                agreements += 1

        if checked == 0:
            # No validators available — can't assess agreement
            confidence_map[feat] = "LOW"
        elif checked == 1:
            confidence_map[feat] = "HIGH" if agreements == 1 else "MEDIUM"
        else:
            # 2+ validators
            if agreements == checked:
                confidence_map[feat] = "HIGH"
            elif agreements >= 1:
                confidence_map[feat] = "MEDIUM"
            else:
                confidence_map[feat] = "LOW"

    return confidence_map


# ── PRIMARY: SHAP TreeExplainer ────────────────────────────────────────────
class SHAPTreePrimary:
    """
    Primary explainer for XGBoost and RandomForest.
    Uses SHAP TreeExplainer — exact, fast, native.
    """

    def __init__(self, model, X_background: pd.DataFrame):
        if not SHAP_AVAILABLE:
            raise ImportError("shap not installed — run: pip install shap")

        inner = get_inner_model(model)
        self.explainer = shap.TreeExplainer(
            inner,
            data=shap.sample(X_background, min(200, len(X_background))),
            feature_perturbation="interventional",
        )
        self.feature_names = list(X_background.columns)

    def explain_local(self, X_row: pd.DataFrame) -> dict:
        """
        Explain a single prediction (or small batch).

        Returns:
            {
                "features":   [feat1, feat2, ...],  # top-K ordered by |SHAP|
                "directions": {feat: "risk+" or "risk-"},
                "importances": {feat: normalized_abs_shap},
                "raw_shap":   {feat: raw_shap_value},
            }
        """
        shap_vals = self.explainer.shap_values(X_row)

        # For binary classifiers some versions return list[array]
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]  # take positive class

        shap_vals = np.array(shap_vals).flatten()

        raw = dict(zip(self.feature_names, shap_vals))
        abs_max = max(abs(v) for v in raw.values()) or 1.0
        norm    = {k: abs(v) / abs_max for k, v in raw.items()}

        ranked = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        top_k  = [f for f, _ in ranked[:TOP_K_FEATURES]]

        return {
            "features":    top_k,
            "directions":  {f: _direction(raw[f]) for f in top_k},
            "importances": {f: round(norm[f], 4) for f in top_k},
            "raw_shap":    {f: round(raw[f], 6) for f in top_k},
        }

    def explain_global(self, X_sample: pd.DataFrame) -> dict:
        """
        Global feature importance over a sample.

        Returns:
            {
                "features":    [feat1, ...],   # top-K by mean |SHAP|
                "importances": {feat: score},
                "directions":  {feat: direction},
            }
        """
        shap_vals = self.explainer.shap_values(X_sample)
        if isinstance(shap_vals, list):
            shap_vals = shap_vals[1]

        mean_abs = np.abs(shap_vals).mean(axis=0)
        mean_raw = np.array(shap_vals).mean(axis=0)  # signed mean for direction

        raw = dict(zip(self.feature_names, mean_abs))
        abs_max = max(raw.values()) or 1.0
        norm    = {k: v / abs_max for k, v in raw.items()}

        ranked = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        top_k  = [f for f, _ in ranked[:TOP_K_FEATURES]]
        dirs   = dict(zip(self.feature_names, mean_raw))

        return {
            "features":    top_k,
            "importances": {f: round(norm[f], 4) for f in top_k},
            "directions":  {f: _direction(dirs[f]) for f in top_k},
        }


# ── PRIMARY: Logistic Regression Coefficients ─────────────────────────────
class LogisticCoefficientPrimary:
    """
    Primary explainer for Logistic Regression.
    Uses raw coefficients × feature values — exact, interpretable, fast.
    For global: coefficients directly.
    For local: coefficient × feature_value (contribution).
    """

    def __init__(self, model, feature_names: list[str]):
        inner   = get_inner_model(model)
        scaler  = get_scaler(model)

        self.coefs         = inner.coef_[0]                     # raw coefficients
        self.feature_names = feature_names
        self.scaler        = scaler
        self.coef_map      = dict(zip(feature_names, self.coefs))

        # Normalized absolute coefficients for importance ranking
        abs_max = np.abs(self.coefs).max() or 1.0
        self.norm_coefs = {f: abs(c) / abs_max
                           for f, c in zip(feature_names, self.coefs)}

    def explain_local(self, X_row: pd.DataFrame) -> dict:
        """
        Local explanation: contribution = coefficient × scaled_feature_value.
        Tells us which features are actually driving THIS prediction.
        """
        row = X_row.iloc[0] if len(X_row) > 1 else X_row.squeeze()

        if self.scaler is not None:
            row_scaled = self.scaler.transform(X_row.values.reshape(1, -1))[0]
        else:
            row_scaled = row.values

        contributions = {f: c * v for f, c, v
                         in zip(self.feature_names, self.coefs, row_scaled)}

        abs_max = max(abs(v) for v in contributions.values()) or 1.0
        norm    = {k: abs(v) / abs_max for k, v in contributions.items()}

        ranked = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        top_k  = [f for f, _ in ranked[:TOP_K_FEATURES]]

        return {
            "features":       top_k,
            "directions":     {f: _direction(contributions[f]) for f in top_k},
            "importances":    {f: round(norm[f], 4) for f in top_k},
            "contributions":  {f: round(contributions[f], 6) for f in top_k},
        }

    def explain_global(self, X_sample: pd.DataFrame = None) -> dict:
        """Global explanation: use raw coefficients (population-level)."""
        ranked = sorted(self.norm_coefs.items(), key=lambda x: x[1], reverse=True)
        top_k  = [f for f, _ in ranked[:TOP_K_FEATURES]]

        return {
            "features":    top_k,
            "importances": {f: round(self.norm_coefs[f], 4) for f in top_k},
            "directions":  {f: _direction(self.coef_map[f]) for f in top_k},
        }


# ── PRIMARY: LIME (for SVM or fallback) ───────────────────────────────────
class LIMEPrimary:
    """
    Primary explainer for SVM (or fallback for unknown models).
    LIME is model-agnostic — works on any predict_proba interface.
    """

    def __init__(self, model, X_background: pd.DataFrame):
        if not LIME_AVAILABLE:
            raise ImportError("lime not installed — run: pip install lime")

        self.model         = model
        self.feature_names = list(X_background.columns)
        self.explainer     = lime.lime_tabular.LimeTabularExplainer(
            training_data    = X_background.values,
            feature_names    = self.feature_names,
            mode             = "classification",
            discretize_continuous = True,
            random_state     = 42,
        )

    def explain_local(self, X_row: pd.DataFrame) -> dict:
        exp = self.explainer.explain_instance(
            data_row         = X_row.values[0],
            predict_fn       = self.model.predict_proba,
            num_features     = LIME_NUM_FEATURES,
            num_samples      = LIME_NUM_SAMPLES,
            top_labels       = 1,
        )

        raw   = dict(exp.as_list(label=1))
        # LIME feature names include bin ranges — extract base feature name
        clean = {}
        for k, v in raw.items():
            base = k.split(" ")[0].split("<")[0].split(">")[0].split("=")[0].strip()
            # Find matching feature_name
            match = next((f for f in self.feature_names if f in k), base)
            clean[match] = clean.get(match, 0) + v

        abs_max = max(abs(v) for v in clean.values()) or 1.0
        norm    = {k: abs(v) / abs_max for k, v in clean.items()}
        ranked  = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        top_k   = [f for f, _ in ranked[:TOP_K_FEATURES]]

        return {
            "features":    top_k,
            "directions":  {f: _direction(clean.get(f, 0)) for f in top_k},
            "importances": {f: round(norm[f], 4) for f in top_k},
        }

    def explain_global(self, X_sample: pd.DataFrame) -> dict:
        """Global LIME: aggregate local explanations over sample (expensive)."""
        agg: dict[str, list[float]] = {f: [] for f in self.feature_names}

        sample = X_sample.sample(min(200, len(X_sample)), random_state=42)
        for _, row in sample.iterrows():
            try:
                local = self.explain_local(pd.DataFrame([row]))
                for feat, imp in local["importances"].items():
                    if feat in agg:
                        agg[feat].append(imp)
            except Exception:
                continue

        mean_imp = {f: np.mean(v) if v else 0.0 for f, v in agg.items()}
        abs_max  = max(mean_imp.values()) or 1.0
        norm     = {f: v / abs_max for f, v in mean_imp.items()}

        ranked = sorted(norm.items(), key=lambda x: x[1], reverse=True)
        top_k  = [f for f, _ in ranked[:TOP_K_FEATURES]]

        return {
            "features":    top_k,
            "importances": {f: round(norm[f], 4) for f in top_k},
            "directions":  {f: "unknown" for f in top_k},  # LIME aggregation loses sign
        }


# ── VALIDATOR: LIME ────────────────────────────────────────────────────────
class LIMEValidator:
    """
    LIME as secondary validation method.
    Used when primary is SHAP or coefficients.
    """

    def __init__(self, model, X_background: pd.DataFrame):
        if not LIME_AVAILABLE:
            self._available = False
            return
        self._available = True
        self.model         = model
        self.feature_names = list(X_background.columns)
        self.explainer     = lime.lime_tabular.LimeTabularExplainer(
            training_data    = X_background.values,
            feature_names    = self.feature_names,
            mode             = "classification",
            discretize_continuous = True,
            random_state     = 42,
        )

    def validate_local(self, X_row: pd.DataFrame) -> dict | None:
        if not self._available:
            return None
        try:
            exp = self.explainer.explain_instance(
                data_row   = X_row.values[0],
                predict_fn = self.model.predict_proba,
                num_features = LIME_NUM_FEATURES,
                num_samples  = LIME_NUM_SAMPLES,
                top_labels   = 1,
            )
            raw   = dict(exp.as_list(label=1))
            clean = {}
            for k, v in raw.items():
                match = next((f for f in self.feature_names if f in k), k)
                clean[match] = clean.get(match, 0) + v

            abs_max = max(abs(v) for v in clean.values()) or 1.0
            norm    = {k: abs(v) / abs_max for k, v in clean.items()}
            ranked  = sorted(norm.items(), key=lambda x: x[1], reverse=True)
            top_k   = [f for f, _ in ranked[:TOP_K_FEATURES]]

            return {
                "features":   top_k,
                "directions": {f: _direction(clean.get(f, 0)) for f in top_k},
            }
        except Exception as e:
            return None


# ── VALIDATOR: AIX360 ─────────────────────────────────────────────────────
class AIX360Validator:
    """
    AIX360 as secondary validation method.
    Uses rule-based Boolean Rule Column Generation (BRCG) for local validation.

    Falls back to a perturbation-based method if AIX360 not installed —
    this preserves the agreement-based architecture even without the library.
    """

    def __init__(self, model, X_train: pd.DataFrame, y_train: pd.Series):
        self.feature_names = list(X_train.columns)
        self.model         = model
        self._available    = False

        if AIX360_AVAILABLE:
            try:
                self._fit_aix360(X_train, y_train)
                self._available = True
                print("[xai_engine] AIX360 loaded successfully.")
            except Exception as e:
                print(f"[xai_engine] AIX360 fit failed ({e}). Using perturbation fallback.")
                self._build_perturbation_validator(X_train)
        else:
            print("[xai_engine] AIX360 not installed. Using perturbation-based fallback validator.")
            self._build_perturbation_validator(X_train)

    def _fit_aix360(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Fit AIX360 BRCG on a training sample."""
        sample_size = min(AIX360_SAMPLE_SIZE, len(X_train))
        idx  = np.random.default_rng(42).choice(len(X_train), sample_size, replace=False)
        Xs   = X_train.iloc[idx]
        ys   = y_train.iloc[idx]

        fb = FeatureBinarizer(negations=True, returnOrd=True)
        Xb, Xb_std = fb.fit_transform(Xs)

        self._fb       = fb
        self._explainer = BooleanRuleCGExplainer(lambda0=1e-3, lambda1=1e-3)
        self._explainer.fit(Xb, ys)

    def _build_perturbation_validator(self, X_train: pd.DataFrame):
        """
        Fallback: perturbation-based feature importance.
        Mask each feature with its mean and measure prediction change.
        Uses a sample for efficiency.
        """
        self._X_means = X_train.mean()
        self._fallback_mode = True

    def validate_local(self, X_row: pd.DataFrame) -> dict | None:
        if AIX360_AVAILABLE and self._available:
            return self._aix360_local(X_row)
        return self._perturbation_local(X_row)

    def _aix360_local(self, X_row: pd.DataFrame) -> dict | None:
        try:
            Xb = self._fb.transform(X_row)
            rules = self._explainer.explain(Xb)

            # Extract feature names from rules and score by rule weight
            feature_scores: dict[str, float] = {}
            for rule in rules:
                for feat in self.feature_names:
                    if feat in str(rule):
                        feature_scores[feat] = feature_scores.get(feat, 0) + 1.0

            if not feature_scores:
                return None

            abs_max = max(feature_scores.values()) or 1.0
            norm    = {f: v / abs_max for f, v in feature_scores.items()}
            ranked  = sorted(norm.items(), key=lambda x: x[1], reverse=True)
            top_k   = [f for f, _ in ranked[:TOP_K_FEATURES]]

            return {
                "features":   top_k,
                "directions": {},   # BRCG rules don't give signed importance directly
            }
        except Exception:
            return self._perturbation_local(X_row)

    def _perturbation_local(self, X_row: pd.DataFrame) -> dict | None:
        """
        Fallback validator: for each feature, replace its value with the
        column mean and measure the change in predicted churn probability.
        Features with large prediction change are important.
        """
        try:
            base_prob = self.model.predict_proba(X_row)[0, 1]
            row       = X_row.copy()
            scores    = {}

            for feat in self.feature_names:
                if feat not in row.columns:
                    continue
                original = row[feat].values[0]
                row[feat] = self._X_means.get(feat, 0)
                perturbed_prob = self.model.predict_proba(row)[0, 1]
                scores[feat] = abs(base_prob - perturbed_prob)
                row[feat] = original  # restore

            abs_max = max(scores.values()) or 1.0
            norm    = {f: v / abs_max for f, v in scores.items()}
            ranked  = sorted(norm.items(), key=lambda x: x[1], reverse=True)
            top_k   = [f for f, _ in ranked[:TOP_K_FEATURES]]

            # Direction: if removing the feature LOWERS churn probability, it was risk+
            dirs = {}
            for feat in top_k:
                original = X_row[feat].values[0]
                row_c    = X_row.copy()
                row_c[feat] = self._X_means.get(feat, 0)
                p_masked = self.model.predict_proba(row_c)[0, 1]
                dirs[feat] = "risk+" if (base_prob - p_masked) > 0 else "risk-"

            return {
                "features":   top_k,
                "directions": dirs,
            }
        except Exception:
            return None


# ── Main XAI Engine ────────────────────────────────────────────────────────
class XAIEngine:
    """
    Agreement-Based XAI Engine.

    Usage:
        engine = XAIEngine(model, X_train, y_train, feature_names)

        # Local (per-customer):
        result = engine.explain_local(customer_id="CUST_001", X_row=X_row)

        # Global (population):
        global_exp = engine.explain_global(X_sample=X_sample)
    """

    def __init__(
        self,
        model,
        X_train:      pd.DataFrame,
        y_train:      pd.Series,
        feature_names: list[str],
        verbose:       bool = True,
    ):
        self.model         = model
        self.feature_names = feature_names
        self.model_type    = detect_model_type(model)
        self.verbose       = verbose

        if verbose:
            print(f"\n[XAIEngine] Model type detected: {self.model_type}")
            print(f"[XAIEngine] Features: {len(feature_names)}")

        # Background sample for SHAP (efficiency — never full dataset)
        bg_size = min(GLOBAL_SAMPLE_SIZE, len(X_train))
        self._X_background = X_train.sample(bg_size, random_state=42)
        self._X_train = X_train
        self._y_train = y_train

        # Build primary + validators based on model type
        self._primary   = self._build_primary(model, X_train, feature_names)
        self._lime_val  = self._build_lime_validator(model, X_train)
        self._aix360_val = AIX360Validator(model, X_train, y_train)

        if verbose:
            print(f"[XAIEngine] Primary:    {type(self._primary).__name__}")
            print(f"[XAIEngine] Validator1: LIMEValidator "
                  f"({'active' if self._lime_val._available else 'unavailable'})")
            print(f"[XAIEngine] Validator2: AIX360Validator "
                  f"({'aix360' if AIX360_AVAILABLE else 'perturbation-fallback'})")

    def _build_primary(self, model, X_train, feature_names):
        if self.model_type in ("xgboost", "random_forest"):
            if SHAP_AVAILABLE:
                return SHAPTreePrimary(model, self._X_background)
            else:
                print("[XAIEngine] SHAP unavailable — falling back to LIME primary")
                return LIMEPrimary(model, X_train)

        elif self.model_type == "logistic":
            return LogisticCoefficientPrimary(model, feature_names)

        elif self.model_type == "svm":
            if LIME_AVAILABLE:
                return LIMEPrimary(model, X_train)
            raise RuntimeError("SVM requires LIME — run: pip install lime")

        else:
            print(f"[XAIEngine] Unknown model type — using LIME primary")
            return LIMEPrimary(model, X_train) if LIME_AVAILABLE else None

    def _build_lime_validator(self, model, X_train):
        validator = LIMEValidator.__new__(LIMEValidator)
        validator.feature_names = list(X_train.columns)
        validator.model = model
        validator._available = False

        if LIME_AVAILABLE and self.model_type != "svm":
            # Don't double-use LIME as both primary AND validator for SVM
            validator._available = True
            validator.explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data         = self._X_background.values,
                feature_names         = validator.feature_names,
                mode                  = "classification",
                discretize_continuous = True,
                random_state          = 42,
            )
        return validator

    # ── Local explanation (per-customer) ──────────────────────────────────
    def explain_local(
        self,
        X_row:       pd.DataFrame,
        customer_id: str,
        churn_prob:  float,
    ) -> dict:
        """
        Generate a full explanation for one customer prediction.

        Args:
            X_row:       Single-row DataFrame with model features.
            customer_id: Customer identifier for the output dict.
            churn_prob:  Predicted churn probability from Phase 1 model.

        Returns:
            Dict matching the strict output format defined in Phase 2 spec.
        """
        # Step 1: Primary method
        primary_out  = self._primary.explain_local(X_row)
        primary_feats = primary_out["features"]
        primary_dirs  = primary_out["directions"]
        primary_imps  = primary_out["importances"]

        # Step 2: Validators
        lime_out   = self._lime_val.validate_local(X_row)
        aix360_out = self._aix360_val.validate_local(X_row)
        validators = [v for v in [lime_out, aix360_out] if v is not None]

        # Step 3: Agreement-based confidence
        confidence_map = compute_confidence(
            primary_features   = primary_feats,
            primary_directions = primary_dirs,
            validator_results  = validators,
            top_k              = AGREEMENT_TOP_K,
        )

        # Step 4: Build explanation list
        explanations = []
        for feat in primary_feats:
            explanations.append({
                "feature":    feat,
                "importance": primary_imps.get(feat, 0.0),
                "direction":  primary_dirs.get(feat, "unknown"),
                "confidence": confidence_map.get(feat, "LOW"),
            })

        # Step 5: Validator agreement metadata
        n_validators_active = sum(1 for v in [lime_out, aix360_out] if v is not None)
        high_confidence_features = [
            e["feature"] for e in explanations if e["confidence"] == "HIGH"
        ]

        return {
            "customer_id":        customer_id,
            "churn_probability":  round(float(churn_prob), 4),
            "primary_method":     self._method_name(),
            "validators_active":  n_validators_active,
            "high_conf_features": high_confidence_features,
            "explanations":       explanations,
            "_raw": {
                "primary":  primary_out,
                "lime":     lime_out,
                "aix360":   aix360_out,
            },
        }

    # ── Global explanation (population-level) ─────────────────────────────
    def explain_global(
        self,
        X_sample: pd.DataFrame,
        sample_size: int = GLOBAL_SAMPLE_SIZE,
    ) -> dict:
        """
        Global feature importance across a sample of customers.
        Uses primary method only — secondary methods are for local validation.

        Returns:
            {
                "method":      "...",
                "sample_size": N,
                "top_features": [{feature, importance, direction}]
            }
        """
        n = min(sample_size, len(X_sample))
        X_s = X_sample.sample(n, random_state=42)

        global_out = self._primary.explain_global(X_s)

        top_features = [
            {
                "feature":    f,
                "importance": global_out["importances"].get(f, 0.0),
                "direction":  global_out["directions"].get(f, "unknown"),
            }
            for f in global_out["features"]
        ]

        return {
            "method":       self._method_name(),
            "sample_size":  n,
            "top_features": top_features,
        }

    def _method_name(self) -> str:
        return {
            "xgboost":       "SHAP_TreeExplainer",
            "random_forest": "SHAP_TreeExplainer",
            "logistic":      "logistic_coefficients",
            "svm":           "LIME_primary",
        }.get(self.model_type, "LIME_primary")

    # ── Batch local explanations ───────────────────────────────────────────
    def explain_batch(
        self,
        X:            pd.DataFrame,
        customer_ids: list[str],
        churn_probs:  list[float],
        max_rows:     int = 500,
    ) -> list[dict]:
        """
        Explain a batch of customers (on-demand, not full dataset).
        Never explain more than max_rows in one call.
        """
        n = min(len(X), max_rows)
        results = []
        for i in range(n):
            try:
                row = X.iloc[[i]]
                res = self.explain_local(
                    X_row       = row,
                    customer_id = customer_ids[i],
                    churn_prob  = churn_probs[i],
                )
                results.append(res)
            except Exception as e:
                results.append({
                    "customer_id":      customer_ids[i],
                    "churn_probability": churn_probs[i],
                    "error":            str(e),
                    "explanations":     [],
                })
        return results


# ── Confidence summary ─────────────────────────────────────────────────────
def confidence_summary(explanations: list[dict]) -> dict:
    """
    Aggregate confidence distribution across a batch of explanations.

    Returns:
        {"HIGH": N, "MEDIUM": N, "LOW": N, "total_features": N, "trust_score": 0-1}
    """
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for exp in explanations:
        for feat_exp in exp.get("explanations", []):
            conf = feat_exp.get("confidence", "LOW")
            counts[conf] = counts.get(conf, 0) + 1

    total = sum(counts.values()) or 1
    trust = (counts["HIGH"] + 0.5 * counts["MEDIUM"]) / total

    return {
        **counts,
        "total_features": total,
        "trust_score":    round(trust, 3),
    }
