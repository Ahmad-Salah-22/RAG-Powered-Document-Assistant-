import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application Metadata
    PROJECT_NAME: str = "RAG-Powered Document Assistant"
    API_V1_STR: str = "/api/v1"

    # Ollama Local LLM Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b"
    OLLAMA_TIMEOUT: float = 60.0

    # ChromaDB & Vector Store Configuration
    CHROMA_PATH: str = "./data/vector_store"
    COLLECTION_NAME: str = "rag_documents"

    # Embedding & RAG Parameters
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 4

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
