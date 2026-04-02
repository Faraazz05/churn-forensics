"""
api/routes/drift.py
===================
GET /drift          — full drift report
GET /drift/features — feature-level drift details
GET /drift/warnings — early warning signals only
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from core.security  import require_api_key
from schemas.response_models import DriftResponse, DriftFeatureOut
from services       import drift_service as svc

router = APIRouter()


@router.get("/drift", response_model=DriftResponse, tags=["Drift"])
async def get_drift(_=Depends(require_api_key)):
    """
    Full drift detection report: PSI, KS-test, trends, early warnings.
    Source: Phase 4 drift engine outputs.
    """
    report = svc.load_drift_report()
    if not report:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No drift data found. Run Phase 4 drift detection first.",
        )

    all_feats  = svc.get_drift_features()
    warnings   = svc.load_early_warnings()
    retrain    = svc.load_retraining_trigger()

    return DriftResponse(
        overall_severity   = report.get("overall_drift_severity","—"),
        n_features_tracked = report.get("n_features_tracked",0),
        drifted_features   = report.get("drifted_features",[]),
        early_warnings     = [DriftFeatureOut(**_drift_to_schema(w)) for w in warnings],
        retraining_trigger = retrain,
        drift_features     = [DriftFeatureOut(**_drift_to_schema(f)) for f in all_feats[:50]],
    )


@router.get("/drift/features", tags=["Drift"])
async def get_drift_features(
    early_warning: bool = Query(False, description="Return only early warning features"),
    limit:         int  = Query(50, ge=1, le=200),
    _=Depends(require_api_key),
):
    """Detailed feature-level drift scores."""
    feats = svc.get_drift_features(early_warning_only=early_warning)[:limit]
    return {"n_features": len(feats), "features": feats}


@router.get("/drift/warnings", tags=["Drift"])
async def get_early_warnings(_=Depends(require_api_key)):
    """Only features with early_warning=True (leading indicators in decline)."""
    warnings = svc.load_early_warnings()
    if not warnings:
        return {"n_warnings": 0, "warnings": [],
                "message": "No early warning signals detected."}
    return {"n_warnings": len(warnings), "warnings": warnings}


def _drift_to_schema(f: dict) -> dict:
    return {
        "feature":        f.get("feature","—"),
        "psi":            f.get("psi"),
        "psi_status":     f.get("psi_status"),
        "ks_statistic":   f.get("ks_statistic"),
        "p_value":        f.get("p_value"),
        "drift_severity": f.get("drift_severity"),
        "trend":          f.get("trend"),
        "velocity":       f.get("velocity"),
        "early_warning":  bool(f.get("early_warning", False)),
        "xai_confirmed":  bool(f.get("xai_confirmed", False)),
    }
