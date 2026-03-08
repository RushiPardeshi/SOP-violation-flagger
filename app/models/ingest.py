from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    doc_id: str
    title: str
    content: str


class IngestResponse(BaseModel):
    status: str
    doc_id: str
    chunks_created: int
    action: Optional[str] = None  # "added" or "updated"
