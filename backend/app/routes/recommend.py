from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.recommend import RecommendationRequest, RecommendationResponse
from app.ai.recommend_engine import generate_recommendation
from app.routes.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=RecommendationResponse)
def get_recommendation(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        return RecommendationResponse(**generate_recommendation(request))
    except ValueError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            f"Recommendation engine failed: {e}")
