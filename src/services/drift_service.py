"""
services/drift_service.py
=========================
Calls Phase 4 drift engine / loads saved outputs.
"""
import json
from pathlib import Path
from typing import Optional
from core.config import get_settings

settings = get_settings()


def _drift_dir() -> Path:
    return settings.OUTPUTS_DIR / "drift"


def load_drift_report() -> dict:
    p = _drift_dir() / "drift_report.json"
    if not p.exists(): return {}
    with open(p) as f: return json.load(f)


def load_early_warnings() -> list[dict]:
    p = _drift_dir() / "early_warnings.json"
    if not p.exists(): return []
    with open(p) as f: return json.load(f)


def load_retraining_trigger() -> dict:
    p = _drift_dir() / "retraining_trigger.json"
    if not p.exists(): return {}
    with open(p) as f: return json.load(f)


def get_drift_features(early_warning_only: bool = False) -> list[dict]:
    report = load_drift_report()
    feats  = report.get("drift_report", [])
    if early_warning_only:
        feats = [f for f in feats if f.get("early_warning")]
    return sorted(feats, key=lambda x: -(x.get("psi") or 0))
