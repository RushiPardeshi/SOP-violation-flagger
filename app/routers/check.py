from fastapi import APIRouter, HTTPException
from app.models.check import CheckRequest, CheckResponse
from app.services.pinecone_svc import query_similar
from app.services.llm import check_violation
from app.config import settings

router = APIRouter()


@router.post("/check-message", response_model=CheckResponse)
async def check_message(request: CheckRequest):
    try:
        sop_docs = query_similar(request.message_text, top_k=settings.top_k)
        result = check_violation(request.message_text, sop_docs)
        return CheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
