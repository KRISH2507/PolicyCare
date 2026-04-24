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
    try:
        return ChatResponse(**generate_chat_reply(request))
    except ValueError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                            f"Chat engine failed: {e}")
