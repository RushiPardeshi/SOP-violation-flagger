from pinecone import Pinecone
from app.config import settings
from app.services.chunking import chunk_sop_document

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = _pc.Index(host=settings.pinecone_index_host)


def upsert_doc(doc_id: str, title: str, content: str) -> dict:
    """
    Upsert document using Pinecone's inference API with intelligent chunking.
    
    Returns:
        Dict with status and number of chunks created
    """
    # Chunk the document intelligently
    chunks = chunk_sop_document(content, title, chunk_size=800, overlap=100)
    
    # Prepare records for Pinecone
    records = []
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}#chunk{idx}"
        records.append({
            "_id": chunk_id,
            "chunk_text": chunk["text"],  # Pinecone embeds this automatically
            "title": title,
            "doc_id": doc_id,  # Parent document ID
            "chunk_index": idx,
            "section": chunk["metadata"].get("section", ""),
            "content": chunk["text"],  # Store for LLM retrieval
        })
    
    # Upsert all chunks
    _index.upsert_records(
        namespace=settings.pinecone_namespace,
        records=records,
    )
    
    return {
        "chunks_created": len(records),
        "doc_id": doc_id
    }


def query_similar(query_text: str, top_k: int) -> list[dict]:
    """Query similar documents using Pinecone's inference API."""
    result = _index.query(
        namespace=settings.pinecone_namespace,
        top_k=top_k,
        include_metadata=True,
        query={
            "inputs": {"text": query_text}
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
