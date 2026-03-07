from pinecone import Pinecone
from app.config import settings

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = _pc.Index(host=settings.pinecone_index_host)


def upsert_doc(doc_id: str, title: str, content: str) -> None:
    """Upsert document using Pinecone's inference API for automatic embedding."""
    _index.upsert_records(
        namespace=settings.pinecone_namespace,
        records=[
            {
                "_id": doc_id,
                "chunk_text": content,  # Pinecone embeds this field automatically
                "title": title,  # Stored as metadata
                "content": content,  # Also store as metadata for LLM retrieval
            }
        ],
    )


def query_similar(query_text: str, top_k: int) -> list[dict]:
    """Query similar documents using Pinecone's inference API."""
    result = _index.query(
        namespace=settings.pinecone_namespace,
        top_k=top_k,
        include_metadata=True,
        query={
            "inputs": {"text": query_text}, 
            "top_k": settings.top_k,
        },
    )
    return [
        {
            "id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        }
        for match in result["matches"]
    ]
