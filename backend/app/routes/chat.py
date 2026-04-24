from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.ai.chat_engine import generate_chat_reply
from app.routes.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def process_chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Authenticated endpoint. Accepts a user message and conversation history,
    retrieves relevant policy chunks via RAG, and returns a grounded reply.
    """
    try:
        result_dict = generate_chat_reply(request)
        return ChatResponse(**result_dict)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat engine failed: {str(e)}",
        )
