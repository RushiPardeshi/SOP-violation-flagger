"""API for reporting missed violations (false negatives)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.db import record_reported_violation
from app.services.pinecone_svc import upsert_reported_violation

router = APIRouter(tags=["report"])


class ReportViolationRequest(BaseModel):
    message_text: str
    user_id: str
    channel_id: str | None = None
    rule: str | None = None  # Optional: from check-message if we run it


@router.post("/report-violation")
async def report_violation(req: ReportViolationRequest):
    """Record a user-reported violation (we missed it - false negative)."""
    if not req.message_text.strip():
        raise HTTPException(400, "message_text is required")
    reported_id = record_reported_violation(
        message_text=req.message_text.strip(),
        user_id=req.user_id,
        channel_id=req.channel_id,
        rule=req.rule,
    )
    try:
        upsert_reported_violation(
            reported_id=reported_id,
            message_text=req.message_text.strip(),
            rule=req.rule or "",
        )
    except Exception:
        pass
    return {"status": "ok", "id": reported_id}
