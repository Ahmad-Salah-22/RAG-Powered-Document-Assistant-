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
    retrieval_mode: Optional[str] = Field(
        default="hybrid",
        description="Retrieval strategy: 'hybrid' (Dense + BM25 RRF), 'dense' (Vector only), or 'bm25' (Lexical only)."
    )
    enable_reranker: Optional[bool] = Field(
        default=False,
        description="Whether to apply Cross-Encoder re-ranking to top candidate chunks."
    )
    query_expansion: Optional[bool] = Field(
        default=False,
        description="Whether to apply query expansion before search."
    )
    agentic_mode: Optional[bool] = Field(
        default=False,
        description="Whether to execute Agentic Corrective RAG (CRAG) with multi-hop decomposition and reflection."
    )

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or contain only whitespace.")
        return v.strip()


class AgenticReasoningStep(BaseModel):
    """Execution step inside the Agentic RAG reasoning and reflection trace."""
    step_number: int = Field(..., description="Chronological sequence number.")
    phase: str = Field(..., description="Pipeline phase name.")
    status: str = Field(default="success", description="Status outcome: 'success', 'warning', 'info'.")
    title: str = Field(..., description="Short headline summary of the action.")
    description: str = Field(..., description="Detailed description of the reasoning decision.")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Structured diagnostics payload.")


class SourceItem(BaseModel):
    """Citation item indicating source document and page number."""
    document: str = Field(..., description="Filename of the referenced document.")
    page: int = Field(..., description="1-based page number where context was extracted.")
    snippet: Optional[str] = Field(None, description="Relevant excerpt text snippet.")
    full_text: Optional[str] = Field(None, description="Complete chunk text for synthesis and inspection.")
    score: Optional[float] = Field(None, description="Relevance distance / similarity score.")
    confidence_percent: Optional[float] = Field(None, description="Estimated match confidence percentage.")
    retrieval_method: Optional[str] = Field(default="dense", description="Method used: 'dense', 'bm25', 'hybrid_rrf', or 'reranked'.")
    dense_rank: Optional[int] = Field(default=None, description="Rank from dense vector search (if applicable).")
    bm25_rank: Optional[int] = Field(default=None, description="Rank from BM25 lexical search (if applicable).")
    rerank_score: Optional[float] = Field(default=None, description="Score from Cross-Encoder re-ranking.")


class QueryResponse(BaseModel):
    """Grounded answer response with citations and execution diagnostics."""
    answer: str = Field(..., description="Grounded answer produced by LLM or fallback engine.")
    sources: List[SourceItem] = Field(default_factory=list, description="Document sources cited.")
    model_used: Optional[str] = Field(None, description="Name of LLM model used.")
    latency_ms: Optional[float] = Field(None, description="Total request latency in milliseconds.")
    retrieval_latency_ms: Optional[float] = Field(None, description="Vector search latency in milliseconds.")
    generation_latency_ms: Optional[float] = Field(None, description="LLM generation latency in milliseconds.")
    fallback_used: Optional[bool] = Field(False, description="Whether offline heuristic fallback was invoked.")
    retrieval_mode: Optional[str] = Field(default="hybrid", description="Active retrieval mode used.")
    reranker_used: Optional[bool] = Field(default=False, description="Whether Cross-Encoder re-ranking was executed.")
    agentic_active: Optional[bool] = Field(default=False, description="Whether Agentic Reasoning mode was engaged.")
    intent_type: Optional[str] = Field(default=None, description="Detected question intent classification.")
    confidence_score: Optional[float] = Field(default=None, description="Self-reflected grounding confidence score (0-100).")
    reasoning_steps: Optional[List[AgenticReasoningStep]] = Field(default=None, description="Step-by-step reasoning trace.")


class CompareDocumentsRequest(BaseModel):
    """Request payload to perform comparative analysis between two documents."""
    doc_a: str = Field(..., description="Filename of the first document.")
    doc_b: str = Field(..., description="Filename of the second document.")
    comparison_topic: Optional[str] = Field(
        default="Core concepts, algorithms, complexity trade-offs, and practical use cases",
        description="Focal topic or theme for the comparative evaluation."
    )
    model: Optional[str] = Field(default=None, description="Optional LLM model override.")


class CompareDocumentsResponse(BaseModel):
    """Response payload containing comparative matrix and citations."""
    doc_a: str
    doc_b: str
    topic: str
    synthesis: str
    sources_a: List[SourceItem] = Field(default_factory=list)
    sources_b: List[SourceItem] = Field(default_factory=list)
    latency_ms: float
    fallback_used: bool = False


class DocumentPageResponse(BaseModel):
    """Details for a single page of an indexed document for interactive visual inspection."""
    document_name: str
    page_number: int
    total_pages: int
    text_content: str
    char_count: int
    has_file: bool = False
    file_type: str = "pdf"
    highlight_positions: Optional[List[Dict[str, Any]]] = None


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
    file_type: Optional[str] = Field("pdf", description="Document format extension: 'pdf', 'docx', 'pptx', 'csv', 'xlsx', 'md', 'txt'.")
    requires_ocr: Optional[bool] = Field(False, description="Flag indicating image-heavy or scanned pages.")
    summary_preview: Optional[str] = Field(None, description="Auto-generated document abstract preview.")


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
    file_type: Optional[str] = "pdf"
    requires_ocr: Optional[bool] = False
    summary_preview: Optional[str] = None


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
