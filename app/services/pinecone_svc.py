from pinecone import Pinecone
from app.config import settings
from app.services.embeddings import embed_text

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = _pc.Index(host=settings.pinecone_index_host)


def check_doc_exists(doc_id: str) -> bool:
    """Check if a document already exists in Pinecone."""
    try:
        result = _index.fetch(ids=[doc_id], namespace=settings.pinecone_namespace)
        return doc_id in result.get("vectors", {})
    except Exception:
        return False


def upsert_doc(doc_id: str, title: str, content: str) -> dict:
    """
    Upsert document with manual embedding.
    - If doc_id exists: updates the existing document
    - If doc_id doesn't exist: creates a new document
    - Other documents remain untouched
    
    Returns:
        dict with 'action' ("added" or "updated") and 'doc_id'
    """
    # Check if document already exists
    exists = check_doc_exists(doc_id)
    
    # Create embedding
    vector = embed_text(content)
    
    # Upsert to Pinecone (will update if exists, insert if new)
    _index.upsert(
        vectors=[
            {
                "id": doc_id,
                "values": vector,
                "metadata": {
                    "title": title,
                    "content": content,
                }
            }
        ],
        namespace=settings.pinecone_namespace
    )
    
    return {
        "action": "updated" if exists else "added",
        "doc_id": doc_id
    }


def query_similar(query_text: str, top_k: int) -> list[dict]:
    """Query similar documents using manual embedding."""
    # Create query embedding
    query_vector = embed_text(query_text)
    
    # Query Pinecone
    result = _index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.pinecone_namespace
    )
    
    return [
        {
            "id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        }
        for match in result["matches"]
    ]


def upsert_feedback(feedback_id: int, message_text: str, rule: str, feedback_type: str) -> None:
    """Upsert a feedback example to Pinecone (feedback namespace) for RAG over feedback."""
    vector = embed_text(message_text)
    _index.upsert(
        vectors=[
            {
                "id": f"feedback-{feedback_id}",
                "values": vector,
                "metadata": {
                    "message_text": message_text[:1000],  # Pinecone metadata limit
                    "rule": rule[:500] if rule else "",
                    "feedback_type": feedback_type,
                },
            }
        ],
        namespace=settings.pinecone_feedback_namespace,
    )


def upsert_reported_violation(reported_id: int, message_text: str, rule: str = "") -> None:
    """Upsert a reported violation (false negative) to Pinecone feedback namespace."""
    vector = embed_text(message_text)
    _index.upsert(
        vectors=[
            {
                "id": f"reported-{reported_id}",
                "values": vector,
                "metadata": {
                    "message_text": message_text[:1000],
                    "rule": (rule or "")[:500],
                    "feedback_type": "false_negative",
                },
            }
        ],
        namespace=settings.pinecone_feedback_namespace,
    )


def query_similar_feedback(query_text: str, top_k: int) -> list[dict]:
    """Query similar feedback examples from Pinecone (feedback namespace)."""
    query_vector = embed_text(query_text)
    result = _index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.pinecone_feedback_namespace,
    )
    return [
        {
            "id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        }
        for match in result["matches"]
    ]
