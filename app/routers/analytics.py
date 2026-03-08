"""Analytics and reporting API (no UI)."""

from fastapi import APIRouter, Query
from app.services.db import get_violations, get_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/stats")
async def get_stats(
    since: str | None = Query(None, description="ISO datetime filter, e.g. 2025-01-01T00:00:00"),
):
    """Aggregate analytics: violation counts, by channel/user/rule, feedback stats."""
    return get_analytics(since=since)


@router.get("/violations")
async def list_violations(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    channel_id: str | None = None,
    user_id: str | None = None,
    since: str | None = Query(None, description="ISO datetime filter"),
):
    """List violations with optional filters."""
    return get_violations(limit=limit, offset=offset, channel_id=channel_id, user_id=user_id, since=since)


@router.get("/export")
async def export_violations(
    format: str = Query("json", description="json or csv"),
    since: str | None = Query(None, description="ISO datetime filter"),
    limit: int = Query(1000, ge=1, le=10000),
):
    """Export violations as JSON or CSV."""
    import csv
    import io

    violations = get_violations(limit=limit, since=since)
    fields = ["channel_id", "user_id", "message_ts", "rule", "severity", "created_at"]

    if format == "csv":
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for v in violations:
            writer.writerow({k: v.get(k, "") for k in fields})
        return {"content": out.getvalue(), "format": "csv"}
    return {"violations": violations, "format": "json"}
