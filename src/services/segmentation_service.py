"""
services/segmentation_service.py
=================================
Calls Phase 3 segmentation engine / loads saved outputs.
"""
import json
from pathlib import Path
from typing import Optional
from core.config import get_settings

settings = get_settings()


def _seg_dir() -> Path:
    return settings.OUTPUTS_DIR / "segmentation"


def load_segment_results() -> list[dict]:
    p = _seg_dir() / "segment_results.json"
    if not p.exists(): return []
    with open(p) as f: return json.load(f)


def load_global_insights() -> dict:
    p = _seg_dir() / "global_insights.json"
    if not p.exists(): return {}
    with open(p) as f: return json.load(f)


def get_segment_by_id(segment_id: str) -> Optional[dict]:
    for seg in load_segment_results():
        if seg.get("segment_id") == segment_id:
            return seg
    return None


def get_segments_by_status(health_status: str) -> list[dict]:
    return [s for s in load_segment_results()
            if s.get("health_status") == health_status]


def get_revenue_at_risk() -> float:
    return sum(s.get("revenue_at_risk", 0) or 0
               for s in load_segment_results())
