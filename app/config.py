from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index: str
    pinecone_index_host: str
    pinecone_namespace: str = "default"
    pinecone_feedback_namespace: str = "feedback"  # Separate namespace for RAG over feedback
    top_k: int = 3
    feedback_max_examples: int = 6  # Max few-shot examples (3 false_positive + 3 correct)
    feedback_rag_top_k: int = 4  # How many similar feedback examples to retrieve from Pinecone

    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Ignore extra fields like SLACK_BOT_TOKEN, NOTION_API_KEY
    }


settings = Settings()
