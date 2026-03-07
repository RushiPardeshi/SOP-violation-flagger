from fastapi import APIRouter, HTTPException
from app.models.ingest import IngestRequest, IngestResponse
from app.services.pinecone_svc import upsert_doc

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    try:
        upsert_doc(
            doc_id=request.doc_id,
            title=request.title,
            content=request.content,
        )
        return IngestResponse(status="ok", doc_id=request.doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
