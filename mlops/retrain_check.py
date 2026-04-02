"""
mlops/retrain_check.py
======================
Customer Health Forensics — Phase 8 MLOps
Retraining decision orchestrator.

Reads drift output and determines whether model retraining
should be triggered. If yes, archives current model to
versioned directory and flags for retraining.

Usage:
  python mlops/retrain_check.py
  python mlops/retrain_check.py --force
  python mlops/retrain_check.py --dry-run
"""

import argparse
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT     = Path(__file__).resolve().parent.parent
MODELS   = ROOT / "models"
OUTPUTS  = ROOT / "outputs"
RUNS_LOG = OUTPUTS / "pipeline_runs.json"


def load_drift_decision() -> dict:
    path = OUTPUTS / "drift" / "retraining_trigger.json"
    if not path.exists():
        return {"model_retraining_required": False, "reason": "No drift data found"}
    with open(path) as f:
        return json.load(f)


def load_octave_consensus() -> dict:
    path = OUTPUTS / "retrain_consensus.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def archive_current_model() -> Path:
    """Archive current model to versioned subdirectory."""
    ts      = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ver_dir = MODELS / f"v_{ts}"
    ver_dir.mkdir(parents=True, exist_ok=True)

    for artifact in ["best_model.pkl", "best_model_info.json",
                     "leaderboard.csv", "feature_names.json",
                     "logistic_coefficients.csv"]:
        src = MODELS / artifact
        if src.exists():
            shutil.copy2(src, ver_dir / artifact)

    print(f"[MLOps] Current model archived → {ver_dir}")
    return ver_dir


def record_pipeline_run(action: str, reason: str, dry_run: bool) -> None:
    """Append run record to pipeline_runs.json."""
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    runs = []
    if RUNS_LOG.exists():
        with open(RUNS_LOG) as f:
            runs = json.load(f)

    runs.append({
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "action":     action,
        "reason":     reason,
        "dry_run":    dry_run,
        "models_dir": str(MODELS),
    })

    with open(RUNS_LOG, "w") as f:
        json.dump(runs[-100:], f, indent=2)  # keep last 100 runs


def check_and_trigger(dry_run: bool = False, force: bool = False) -> dict:
    print("[MLOps] Checking retraining trigger...")

    drift   = load_drift_decision()
    octave  = load_octave_consensus()

    required_python = drift.get("model_retraining_required", False)
    required_octave = octave.get("octave_retrain", None)
    reason          = drift.get("reason", "—")
    n_drifted       = drift.get("n_features_drifted", 0)

    print(f"[MLOps] Python trigger:  {'YES' if required_python else 'NO'}")
    print(f"[MLOps] Octave confirms: {required_octave}")
    print(f"[MLOps] Reason: {reason}")
    print(f"[MLOps] Features drifted: {n_drifted}")

    should_retrain = force or (required_python and required_octave is not False)

    if not should_retrain:
        print("[MLOps] ✓ No retraining needed.")
        record_pipeline_run("no_retrain", reason, dry_run)
        return {"action": "no_retrain", "reason": reason}

    print(f"\n[MLOps] ⚠ Retraining {'TRIGGERED' if not dry_run else 'WOULD BE TRIGGERED (dry run)'}")

    if not dry_run:
        archived = archive_current_model()
        record_pipeline_run("retrain_triggered", reason, dry_run)
        print("[MLOps] Next step: run python train.py to retrain model")
        return {
            "action":   "retrain_triggered",
            "archived": str(archived),
            "reason":   reason,
        }
    else:
        record_pipeline_run("retrain_dry_run", reason, dry_run)
        return {"action": "retrain_dry_run", "reason": reason}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MLOps retraining check")
    parser.add_argument("--dry-run", action="store_true",
                        help="Check only, do not archive or trigger")
    parser.add_argument("--force",   action="store_true",
                        help="Force retraining regardless of drift decision")
    args = parser.parse_args()

    result = check_and_trigger(dry_run=args.dry_run, force=args.force)
    print(f"\n[MLOps] Result: {json.dumps(result, indent=2)}")
