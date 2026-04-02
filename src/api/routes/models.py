"""
api/routes/models.py
====================
GET /models — model leaderboard + active model info
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database  import get_db
from core.security  import require_api_key
from db             import crud
from schemas.response_models import LeaderboardResponse, ModelOut
from services.prediction_service import get_model_info

router = APIRouter()


@router.get("/models", response_model=LeaderboardResponse, tags=["Models"])
async def get_models(db: AsyncSession = Depends(get_db), _=Depends(require_api_key)):
    """Model leaderboard and active model metadata."""
    models  = await crud.list_models(db)
    active  = await crud.get_active_model(db)

    if not models:
        # Fall back to JSON artifact
        info = get_model_info()
        if info and "best_model_name" in info:
            best = ModelOut(
                model_name  = info.get("best_model_name","—"),
                val_auc     = info.get("val_auc"),
                val_f1      = info.get("val_f1"),
                test_auc    = info.get("test_auc"),
                test_f1     = info.get("test_f1"),
                n_features  = info.get("n_features"),
                xai_method  = info.get("xai_method"),
                is_active   = True,
                trained_at  = None,
            )
            return LeaderboardResponse(best_model=best, all_models=[best], n_models=1)
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            detail="No model metadata found.")

    def _to_out(m) -> ModelOut:
        return ModelOut(
            model_name  = m.model_name,
            val_auc     = m.val_auc,
            val_f1      = m.val_f1,
            test_auc    = m.test_auc,
            test_f1     = m.test_f1,
            n_features  = m.n_features,
            xai_method  = m.xai_method,
            is_active   = m.is_active,
            trained_at  = m.trained_at,
        )

    best = _to_out(active) if active else (_to_out(models[0]) if models else None)
    return LeaderboardResponse(
        best_model = best,
        all_models = [_to_out(m) for m in models],
        n_models   = len(models),
    )
