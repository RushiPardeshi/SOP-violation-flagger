from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index: str
    pinecone_index_host: str
    pinecone_namespace: str = "default"
    top_k: int = 3

    model_config = {"env_file": ".env"}


settings = Settings()
