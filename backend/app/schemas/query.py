from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Payload for question submission."""
    question: str = Field(
        ...,
        description="The question to ask the document assistant.",
        example="What is a hash table and what is its average lookup time?"
    )

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or contain only whitespace.")
        return v.strip()


class SourceItem(BaseModel):
    """Citation item indicating source document and page number."""
    document: str = Field(..., description="Filename of the referenced document.")
    page: int = Field(..., description="1-based page number where context was extracted.")
    snippet: Optional[str] = Field(None, description="Relevant excerpt text snippet.")
    score: Optional[float] = Field(None, description="Relevance distance / similarity score.")


class QueryResponse(BaseModel):
    """Grounded answer response with citations."""
    answer: str = Field(..., description="Grounded answer produced by Ollama LLM.")
    sources: List[SourceItem] = Field(default_factory=list, description="Document sources cited.")
    model_used: Optional[str] = Field(None, description="Name of Ollama LLM model used.")


class HealthResponse(BaseModel):
    """Health check diagnostic status."""
    status: str = Field(..., description="System operational status ('healthy' or 'degraded').")
    vector_db_loaded: bool = Field(..., description="Whether persistent vector store is active.")
    ollama_available: bool = Field(..., description="Whether local Ollama daemon is reachable.")
    document_count: Optional[int] = Field(None, description="Total indexed document chunks in DB.")
