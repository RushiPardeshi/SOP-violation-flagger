from pydantic import BaseModel


class IngestRequest(BaseModel):
    doc_id: str
    title: str
    content: str


class IngestResponse(BaseModel):
    status: str
    doc_id: str
