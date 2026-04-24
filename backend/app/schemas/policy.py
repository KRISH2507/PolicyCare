from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    insurer: Optional[str] = None

class PolicyResponse(BaseModel):
    id: int
    name: str
    insurer: str
    file_type: str
    uploaded_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)