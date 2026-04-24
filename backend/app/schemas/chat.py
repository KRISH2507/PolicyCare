from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_profile: Dict[str, Any]
    recommended_policy_name: str = Field(default="")
    recommended_policy_id: Optional[int] = None
    history: List[Dict[str, str]] = []

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be blank")
        return v.strip()


class ChatResponse(BaseModel):
    reply: str
    citations: List[str] = []
    requires_followup: bool
