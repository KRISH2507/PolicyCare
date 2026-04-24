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
    """
    Authenticated endpoint. Submits a 6-field user profile, retrieves relevant
    policy chunks via RAG, and returns a grounded recommendation.
    """
    try:
        result_dict = generate_recommendation(request)
        return RecommendationResponse(**result_dict)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation engine failed: {str(e)}",
        )
