"""
api/routes/segments.py
======================
GET /segments              — all segments + global insights
GET /segments/{segment_id} — deep single-segment analysis
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from core.security  import require_api_key
from schemas.response_models import SegmentOut, SegmentsResponse
from services       import segmentation_service as svc
from utils.logger   import log

router = APIRouter()


@router.get("/segments", response_model=SegmentsResponse, tags=["Segmentation"])
async def get_segments(
    health_status: str  = Query(None, description="Filter: improving/stable/degrading"),
    dimension:     str  = Query(None, description="Filter by dimension, e.g. plan_type"),
    limit:         int  = Query(100, ge=1, le=1000),
    _=Depends(require_api_key),
):
    """
    Return segment churn rates, degradation status, and global insights.
    Source: Phase 3 segmentation engine outputs.
    """
    segs = svc.load_segment_results()
    if health_status:
        segs = [s for s in segs if s.get("health_status") == health_status]
    if dimension:
        segs = [s for s in segs if s.get("dimension") == dimension]
    segs = segs[:limit]

    if not segs and health_status is None and dimension is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No segment data found. Run Phase 3 segmentation first.",
        )

    return SegmentsResponse(
        run_id          = None,
        n_segments      = len(segs),
        segments        = [SegmentOut(**_seg_to_schema(s)) for s in segs],
        global_insights = svc.load_global_insights(),
    )


import csv

@router.get("/segments/trends", tags=["Segmentation"])
async def get_segment_trends(_=Depends(require_api_key)):
    """Return historical trend data from the segmentation engine."""
    p = svc._seg_dir() / "trend_region.csv"
    if not p.exists():
        return []
    
    trends = []
    with open(p, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trends.append(row)
            
    return trends


@router.get("/segments/{segment_id}", tags=["Segmentation"])
async def get_segment(segment_id: str, _=Depends(require_api_key)):
    """Deep analysis for a specific segment."""
    seg = svc.get_segment_by_id(segment_id)
    if not seg:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Segment '{segment_id}' not found.",
        )
    return seg


def _seg_to_schema(s: dict) -> dict:
    return {
        "segment_id":          s.get("segment_id","—"),
        "dimension":           s.get("dimension","—"),
        "value":               str(s.get("value","—")),
        "segment_size":        s.get("segment_size", 0),
        "churn_rate":          s.get("churn_rate"),
        "previous_churn_rate": s.get("previous_churn_rate"),
        "churn_delta":         s.get("churn_delta"),
        "health_status":       s.get("health_status"),
        "risk_level":          s.get("risk_level"),
        "revenue_at_risk":     s.get("revenue_at_risk"),
        "acceleration":        s.get("acceleration"),
        "exceeds_benchmark":   s.get("exceeds_benchmark"),
    }

