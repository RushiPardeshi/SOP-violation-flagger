from pinecone import Pinecone
from app.config import settings
from app.services.chunking import chunk_sop_document
from app.services.embeddings import embed_text

_pc = Pinecone(api_key=settings.pinecone_api_key)
_index = _pc.Index(host=settings.pinecone_index_host)


def check_doc_exists(doc_id: str) -> bool:
    """Check if any chunk of a document already exists in Pinecone."""
    try:
        # Check for the first chunk to determine if doc exists
        chunk_id = f"{doc_id}#chunk0"
        result = _index.fetch(ids=[chunk_id], namespace=settings.pinecone_namespace)
        return chunk_id in result.get("vectors", {})
    except Exception:
        return False


def upsert_doc(doc_id: str, title: str, content: str) -> dict:
    """
    Upsert document with intelligent chunking and manual embedding.
    - Chunks the document intelligently (sections/paragraphs)
    - Creates embeddings for each chunk
    - If doc_id exists: updates existing chunks and adds new ones
    - Returns chunk count and action status
    
    Returns:
        dict with 'action' ("added" or "updated"), 'doc_id', and 'chunks_created'
    """
    # Check if document already exists
    exists = check_doc_exists(doc_id)
    
    # Chunk the document intelligently
    chunks = chunk_sop_document(content, title, chunk_size=800, overlap=100)
    
    # Prepare vectors for upsert
    vectors = []
    for idx, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}#chunk{idx}"
        vector = embed_text(chunk["text"])
        
        vectors.append({
            "id": chunk_id,
            "values": vector,
            "metadata": {
                "title": title,
                "doc_id": doc_id,
                "chunk_index": idx,
                "section": chunk["metadata"].get("section", ""),
                "content": chunk["text"],
            }
        })
    
    # Upsert all chunks to Pinecone
    _index.upsert(
        vectors=vectors,
        namespace=settings.pinecone_namespace
    )
    
    return {
        "action": "updated" if exists else "added",
        "doc_id": doc_id,
        "chunks_created": len(vectors)
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
