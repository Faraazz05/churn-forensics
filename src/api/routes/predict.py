"""
api/routes/predict.py
=====================
POST /predict        — single customer prediction
POST /predict/batch  — batch prediction
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database  import get_db
from core.security  import require_api_key
from db             import crud
from schemas.request_models  import BatchPredictRequest, CustomerFeatures
from schemas.response_models import BatchPredictionOut, PredictionOut
from services       import prediction_service as svc
from utils.logger   import log

router = APIRouter()


@router.post("/predict", response_model=PredictionOut, tags=["Prediction"])
async def predict_single(
    payload: CustomerFeatures,
    db:      AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """
    Predict churn probability for a single customer.
    Stores result in DB and returns prediction.
    """
    try:
        features = payload.model_dump()
        result   = await asyncio.to_thread(svc.predict_single, features)
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Model not loaded: {e}")
    except Exception as e:
        log.error(f"[predict] {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Persist customer + prediction
    try:
        await crud.upsert_customer(
            db, payload.customer_id,
            age=payload.age, region=payload.region,
            plan_type=payload.plan_type, contract_type=payload.contract_type,
            payment_method=payload.payment_method, tenure_months=payload.tenure_months,
            monthly_spend=payload.monthly_spend, raw_features=features,
        )
        await crud.create_prediction(
            db,
            customer_id       = payload.customer_id,
            churn_probability = result["churn_probability"],
            risk_tier         = result["risk_tier"],
            model_name        = result.get("model_name"),
            feature_snapshot  = features,
        )
    except Exception as e:
        log.warning(f"[predict] DB persist failed: {e}")

    return PredictionOut(**result)


@router.post("/predict/batch", response_model=BatchPredictionOut, tags=["Prediction"])
async def predict_batch(
    payload: BatchPredictRequest,
    db:      AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """Batch prediction for multiple customers (up to 10,000)."""
    try:
        records = [c.model_dump() for c in payload.customers]
        results = await asyncio.to_thread(svc.predict_batch, records)
    except FileNotFoundError as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        log.error(f"[predict/batch] {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Summarise
    probs     = [r["churn_probability"] for r in results]
    churn_rate = sum(p >= 0.50 for p in probs) / len(probs)
    risk_dist  = {}
    for r in results:
        risk_dist[r["risk_tier"]] = risk_dist.get(r["risk_tier"], 0) + 1

    return BatchPredictionOut(
        predictions  = [PredictionOut(**r) for r in results],
        n_customers  = len(results),
        churn_rate   = round(churn_rate, 4),
        risk_summary = risk_dist,
    )
