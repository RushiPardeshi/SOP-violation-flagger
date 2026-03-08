from fastapi import APIRouter, HTTPException
from app.models.check import CheckRequest, CheckResponse
from app.services.pinecone_svc import query_similar
from app.services.llm import check_violation
from app.services.db import get_feedback_examples
from app.config import settings

router = APIRouter()


@router.post("/check-message", response_model=CheckResponse)
async def check_message(request: CheckRequest):
    try:
        sop_docs = query_similar(request.message_text, top_k=settings.top_k)
        max_each = max(1, settings.feedback_max_examples // 2)
        feedback_examples = get_feedback_examples(
            max_false_positives=max_each,
            max_correct=max_each,
        )
        result = check_violation(request.message_text, sop_docs, feedback_examples=feedback_examples)
        return CheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
