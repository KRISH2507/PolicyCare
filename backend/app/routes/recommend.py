import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.recommend import RecommendationRequest, RecommendationResponse
from app.ai.recommend_engine import generate_recommendation
from app.routes.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=RecommendationResponse)
def get_recommendation(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = generate_recommendation(request)
        return RecommendationResponse(**result)
    except Exception as e:
        logger.error(
            "[recommend route] Unexpected error: %s\n%s",
            e,
            traceback.format_exc(),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate recommendation right now. Please try again.",
        )
