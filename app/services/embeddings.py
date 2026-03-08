from openai import OpenAI
from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1024  # Match Pinecone index dimension


def embed_text(text: str) -> list[float]:
    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS  # Set to match Pinecone index
    )
    return response.data[0].embedding
