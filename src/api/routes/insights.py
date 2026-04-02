"""
api/routes/insights.py
======================
GET  /insights        — full intelligence report
POST /insights/qa     — natural language Q&A
POST /insights/refresh — regenerate report
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from core.security  import require_api_key, require_admin
from schemas.request_models  import QARequest
from schemas.response_models import InsightResponse, QAResponse
from services       import insight_service as svc
from utils.logger   import log

router = APIRouter()


@router.get("/insights", response_model=InsightResponse, tags=["Insights"])
async def get_insights(_=Depends(require_api_key)):
    """
    Full intelligence report: executive summary, causal analysis,
    predictive outlook, recommendations, business impact.
    Source: Phase 5 insight engine outputs.
    """
    report = svc.load_latest_report()
    if not report:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="No insight report found. Run Phase 5 or POST /insights/refresh.",
        )
    return InsightResponse(
        executive_summary  = report.get("executive_summary",""),
        customer_risk      = report.get("customer_risk", {}),
        segments           = report.get("segments", {}),
        drift_analysis     = report.get("drift_analysis", {}),
        causal_analysis    = report.get("causal_analysis", {}),
        prediction_outlook = report.get("prediction_outlook", {}),
        recommendations    = report.get("recommendations", []),
        business_impact    = report.get("business_impact", {}),
        generated_at       = None,
        llm_mode           = report.get("llm_mode"),
    )


@router.post("/insights/qa", response_model=QAResponse, tags=["Insights"])
async def qa(payload: QARequest, _=Depends(require_api_key)):
    """
    Natural language Q&A system.
    Example questions:
      - "Why are Pro users churning?"
      - "Which segment is at highest risk?"
      - "What should we do to reduce churn?"
    """
    try:
        result = await asyncio.to_thread(svc.answer_question, payload.question)
    except Exception as e:
        log.error(f"[insights/qa] {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return QAResponse(**result)


@router.post("/insights/refresh", tags=["Insights"])
async def refresh_insights(_=Depends(require_admin)):
    """Regenerate the insight report from current phase outputs."""
    try:
        report = await asyncio.to_thread(svc.generate_report)
        return {"status": "ok", "sections": list(report.keys())}
    except Exception as e:
        log.error(f"[insights/refresh] {e}", exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
