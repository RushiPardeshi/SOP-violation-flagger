"""Record violations for analytics and feedback."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.db import record_violation, init_db

router = APIRouter(tags=["violations"])


class RecordViolationRequest(BaseModel):
    channel_id: str
    user_id: str
    message_text: str
    message_ts: str
    rule: str
    severity: str
    explanation: str
    bot_message_ts: str | None = None


@router.post("/violations")
async def record_violation_endpoint(req: RecordViolationRequest):
    """Record a violation (called by Slack bot when it posts a warning)."""
    init_db()
    vid = record_violation(
        channel_id=req.channel_id,
        user_id=req.user_id,
        message_text=req.message_text,
        message_ts=req.message_ts,
        rule=req.rule,
        severity=req.severity,
        explanation=req.explanation,
        bot_message_ts=req.bot_message_ts,
    )
    return {"id": vid, "status": "ok"}
