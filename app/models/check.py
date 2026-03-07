from pydantic import BaseModel
from typing import Optional


class CheckRequest(BaseModel):
    channel_id: str
    user_id: str
    message_text: str
    timestamp: str


class CheckResponse(BaseModel):
    violated: bool
    rule: Optional[str] = None
    severity: Optional[str] = None
    explanation: str
