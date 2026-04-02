"""
api/routes/customers.py
=======================
GET /customers/risk          — high-risk customer list
GET /customers/{id}          — full customer profile
GET /watchlist               — Critical-tier watchlist
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config    import get_settings
from core.database  import get_db
from core.security  import require_api_key
from db             import crud
from schemas.response_models import CustomerRiskOut, WatchlistResponse
from services.xai_service    import load_watchlist_reasoning

router   = APIRouter()
settings = get_settings()


@router.get("/customers/risk", tags=["Customers"])
async def get_high_risk_customers(
    threshold: float = Query(0.50, ge=0.0, le=1.0),
    limit:     int   = Query(100, ge=1, le=1000),
    db:        AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """Customers with churn probability above threshold, sorted by risk."""
    preds = await crud.get_watchlist(db, threshold=threshold, limit=limit)
    if not preds:
        return {"n_customers": 0, "threshold": threshold, "customers": []}

    customers = []
    for p in preds:
        cust = await crud.get_customer(db, p.customer_id)
        customers.append(CustomerRiskOut(
            customer_id       = p.customer_id,
            churn_probability = p.churn_probability,
            risk_tier         = p.risk_tier or "—",
            plan_type         = cust.plan_type if cust else None,
            region            = cust.region    if cust else None,
            contract_type     = cust.contract_type if cust else None,
            primary_driver    = None,
            top_action        = None,
        ))

    return {"n_customers": len(customers), "threshold": threshold,
            "customers": customers}


@router.get("/customers/{customer_id}", tags=["Customers"])
async def get_customer_profile(
    customer_id: str,
    db:          AsyncSession = Depends(get_db),
    _=Depends(require_api_key),
):
    """
    Full customer intelligence profile:
    raw features + latest prediction + XAI + segment membership.
    """
    cust = await crud.get_customer(db, customer_id)
    pred = await crud.get_latest_prediction(db, customer_id)

    if not cust and not pred:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail=f"Customer '{customer_id}' not found.")

    profile: dict = {}
    if cust:
        profile["profile"] = {
            "customer_id":   cust.customer_id,
            "plan_type":     cust.plan_type,
            "region":        cust.region,
            "contract_type": cust.contract_type,
            "tenure_months": cust.tenure_months,
            "monthly_spend": cust.monthly_spend,
        }
    if pred:
        profile["prediction"] = {
            "churn_probability": pred.churn_probability,
            "risk_tier":         pred.risk_tier,
            "predicted_at":      pred.created_at.isoformat() if pred.created_at else None,
        }

    # Attach saved XAI explanation
    from services.xai_service import get_customer_explanation
    exp = get_customer_explanation(customer_id)
    if exp:
        profile["explanation"] = exp

    return profile


@router.get("/watchlist", response_model=WatchlistResponse, tags=["Customers"])
async def get_watchlist(
    limit:     int   = Query(200, ge=1, le=1000),
    _=Depends(require_api_key),
):
    """
    Critical-tier customers (prob > threshold) from Phase 2 watchlist.
    Includes reasoning, WHAT changed, recommended action.
    """
    threshold = settings.WATCHLIST_THRESHOLD
    watchlist  = load_watchlist_reasoning()[:limit]

    return WatchlistResponse(
        threshold   = threshold,
        n_customers = len(watchlist),
        customers   = watchlist,
    )
