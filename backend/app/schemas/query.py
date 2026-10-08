from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChatMessageItem(BaseModel):
    """Chat message turn for multi-turn conversational context."""
    role: str = Field(..., description="Role of the speaker: 'user' or 'assistant'.")
    content: str = Field(..., description="Message text content.")


class QueryRequest(BaseModel):
    """Payload for question submission."""
    question: str = Field(
        ...,
        description="The question to ask the document assistant.",
        json_schema_extra={"example": "What is a hash table and what is its average lookup time?"}
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Number of context chunks to retrieve (1-20)."
    )
    model: Optional[str] = Field(
        default=None,
        description="Ollama model override, e.g. 'llama3:8b', 'mistral', 'phi3'."
    )
    document_filter: Optional[List[str]] = Field(
        default=None,
        description="Optional list of document filenames to restrict search to."
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Maximum cosine distance threshold for context chunks."
    )
    system_prompt_mode: Optional[str] = Field(
        default="academic",
        description="Persona mode: 'academic', 'concise', 'detailed', or 'summary'."
    )
    chat_history: Optional[List[ChatMessageItem]] = Field(
        default=None,
        description="Recent conversation turns for follow-up question context."
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
    confidence_percent: Optional[float] = Field(None, description="Estimated match confidence percentage.")


class QueryResponse(BaseModel):
    """Grounded answer response with citations and execution diagnostics."""
    answer: str = Field(..., description="Grounded answer produced by LLM or fallback engine.")
    sources: List[SourceItem] = Field(default_factory=list, description="Document sources cited.")
    model_used: Optional[str] = Field(None, description="Name of LLM model used.")
    latency_ms: Optional[float] = Field(None, description="Total request latency in milliseconds.")
    retrieval_latency_ms: Optional[float] = Field(None, description="Vector search latency in milliseconds.")
    generation_latency_ms: Optional[float] = Field(None, description="LLM generation latency in milliseconds.")
    fallback_used: Optional[bool] = Field(False, description="Whether offline heuristic fallback was invoked.")


class HealthResponse(BaseModel):
    """Health check diagnostic status."""
    status: str = Field(..., description="System operational status ('healthy' or 'degraded').")
    vector_db_loaded: bool = Field(..., description="Whether persistent vector store is active.")
    ollama_available: bool = Field(..., description="Whether local Ollama daemon is reachable.")
    document_count: Optional[int] = Field(None, description="Total indexed document chunks in DB.")
    active_documents: Optional[List[str]] = Field(default_factory=list, description="List of indexed document files.")


class DocumentInfo(BaseModel):
    """Metadata regarding an indexed document."""
    document_name: str = Field(..., description="Filename of the document.")
    chunk_count: int = Field(..., description="Number of text chunks indexed in vector store.")
    pages: List[int] = Field(default_factory=list, description="List of page numbers present.")
    page_count: int = Field(..., description="Total pages detected.")
    char_count: int = Field(0, description="Total extracted character count.")
    file_size_bytes: Optional[int] = Field(None, description="File size on disk if available.")


class DocumentListResponse(BaseModel):
    """List of all indexed documents in the assistant database."""
    total_documents: int
    total_chunks: int
    documents: List[DocumentInfo]


class UploadResponse(BaseModel):
    """Response returned upon file upload & indexing."""
    message: str
    document_name: str
    pages: int
    chunks_indexed: int
    char_count: int


class DeleteResponse(BaseModel):
    """Response returned upon document deletion."""
    message: str
    document_name: str
    chunks_deleted: int


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics metrics for RAG index and pipeline."""
    total_documents: int
    total_chunks: int
    embedding_model: str
    collection_name: str
    vector_store_path: str
    documents: List[DocumentInfo]
    ollama_status: Dict[str, Any]
