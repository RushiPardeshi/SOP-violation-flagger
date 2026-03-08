"""Feedback API for recording false positive / correct on violations."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.db import record_feedback, get_violation_by_bot_message

router = APIRouter(tags=["feedback"])


class FeedbackRequest(BaseModel):
    channel_id: str
    bot_message_ts: str
    feedback_type: str  # "false_positive" | "correct"
    user_id: str


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Record user feedback on a violation (from Slack reaction or API)."""
    if req.feedback_type not in ("false_positive", "correct"):
        raise HTTPException(400, "feedback_type must be 'false_positive' or 'correct'")
    violation = get_violation_by_bot_message(req.channel_id, req.bot_message_ts)
    if not violation:
        raise HTTPException(404, "Violation not found for this message")
    record_feedback(violation["id"], req.feedback_type, req.user_id)
    return {"status": "ok", "feedback_type": req.feedback_type}
