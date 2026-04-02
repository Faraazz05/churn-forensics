"""
api/routes/explain.py
=====================
POST /explain — XAI explanation for a customer
GET  /explain/global — population-level feature importance
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database  import get_db
from core.security  import require_api_key
from db             import crud
from schemas.request_models  import ExplainRequest
from schemas.response_models import ExplanationOut, FeatureExplanation
from services       import xai_service as svc
from utils.logger   import log

router = APIRouter()


@router.post("/explain", response_model=ExplanationOut, tags=["XAI"])
async def explain_customer(
    payload: ExplainRequest,
    db:      AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """
    Return consensus XAI explanation for a customer.
    First checks saved watchlist outputs; falls back to on-demand.
    """
    # Saved explanation (fast path)
    saved = svc.get_customer_explanation(payload.customer_id)
    if saved:
        return _to_explanation_out(saved)

    # On-demand: need feature snapshot from DB
    pred = await crud.get_latest_prediction(db, payload.customer_id)
    if pred is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"No prediction found for customer '{payload.customer_id}'. "
                   "Call POST /predict first.",
        )

    features = pred.feature_snapshot or {}
    try:
        result = await asyncio.to_thread(
            svc.explain_on_demand, features, pred.churn_probability
        )
    except Exception as e:
        log.error(f"[explain] {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return _to_explanation_out(result)


@router.get("/explain/global", tags=["XAI"])
async def global_explanation(_=Depends(require_api_key)):
    """Population-level global feature importance (from Phase 2 outputs)."""
    data = svc.load_global_explanation()
    if not data:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Global XAI output not found. Run Phase 2 first.",
        )
    return data


@router.get("/explain/confidence", tags=["XAI"])
async def confidence_summary(_=Depends(require_api_key)):
    """Explanation confidence distribution (HIGH/MEDIUM/LOW)."""
    return svc.load_confidence_summary()


def _to_explanation_out(raw: dict) -> ExplanationOut:
    exps = [
        FeatureExplanation(
            feature    = e.get("feature","—"),
            importance = e.get("importance", 0.0),
            direction  = e.get("direction","unknown"),
            confidence = e.get("confidence","LOW"),
        )
        for e in raw.get("explanations", [])
    ]
    reasoning = raw.get("reasoning") or {}
    if not reasoning and "reasoning" in raw:
        reasoning = raw["reasoning"]
    return ExplanationOut(
        customer_id        = raw.get("customer_id","—"),
        churn_probability  = raw.get("churn_probability",0.0),
        primary_method     = raw.get("primary_method","—"),
        validators_active  = raw.get("validators_active",0),
        high_conf_features = raw.get("high_conf_features",[]),
        explanations       = exps,
        reasoning          = reasoning or None,
    )
