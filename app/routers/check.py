from fastapi import APIRouter, HTTPException
from app.models.check import CheckRequest, CheckResponse
from app.services.pinecone_svc import query_similar, query_similar_feedback
from app.services.llm import check_violation
from app.services.db import get_feedback_examples
from app.config import settings

router = APIRouter()


def _get_feedback_examples_for_check(message_text: str) -> list[dict]:
    """
    Get feedback examples: RAG over Pinecone feedback namespace first,
    fall back to recent SQLite examples if RAG returns few results.
    """
    examples: list[dict] = []
    try:
        rag_matches = query_similar_feedback(
            message_text,
            top_k=settings.feedback_rag_top_k,
        )
        for m in rag_matches:
            meta = m.get("metadata", {})
            if meta.get("message_text") and meta.get("feedback_type"):
                examples.append({
                    "message_text": meta["message_text"],
                    "rule": meta.get("rule", ""),
                    "feedback_type": meta["feedback_type"],
                })
    except Exception:
        pass

    # Fallback to recent SQLite examples if RAG returned few
    if len(examples) < 2:
        max_each = max(1, settings.feedback_max_examples // 2)
        sqlite_examples = get_feedback_examples(
            max_false_positives=max_each,
            max_correct=max_each,
            max_false_negatives=2,
        )
        # Dedupe by message_text (RAG might overlap with SQLite)
        seen = {e["message_text"][:100] for e in examples}
        for ex in sqlite_examples:
            key = (ex.get("message_text") or "")[:100]
            if key not in seen:
                examples.append(ex)
                seen.add(key)
        examples = examples[: settings.feedback_max_examples]

    return examples


@router.post("/check-message", response_model=CheckResponse)
async def check_message(request: CheckRequest):
    try:
        sop_docs = query_similar(request.message_text, top_k=settings.top_k)
        feedback_examples = _get_feedback_examples_for_check(request.message_text)
        result = check_violation(request.message_text, sop_docs, feedback_examples=feedback_examples)
        return CheckResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
