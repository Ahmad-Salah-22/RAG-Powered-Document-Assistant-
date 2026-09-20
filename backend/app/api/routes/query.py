from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.query import QueryRequest, QueryResponse, HealthResponse, SourceItem
from app.services.retrieval import retrieve_context
from app.services.generation import generate_grounded_answer, check_ollama_availability
from app.utils.logging_config import logger
from app.core.config import settings

router = APIRouter(tags=["Document Query"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Diagnostic System Health Check",
    description="Returns vector database connection status, total document chunk count, and local Ollama service availability."
)
async def health_check(request: Request):
    """Health check endpoint to inspect system status."""
    collection = getattr(request.app.state, "chroma_collection", None)
    vector_db_loaded = collection is not None
    doc_count = collection.count() if vector_db_loaded else 0

    ollama_available = await check_ollama_availability(settings.OLLAMA_HOST)

    overall_status = "healthy" if (vector_db_loaded and ollama_available) else "degraded"

    return HealthResponse(
        status=overall_status,
        vector_db_loaded=vector_db_loaded,
        ollama_available=ollama_available,
        document_count=doc_count
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit Question to RAG Document Assistant",
    description="Retrieves context chunks from ChromaDB and generates a grounded response with document and page citations using Ollama."
)
async def query_documents(payload: QueryRequest, request: Request):
    """Processes user question through the RAG retrieval and LLM generation pipeline."""
    question = payload.question
    logger.info(f"Received query request: '{question}'")

    collection = getattr(request.app.state, "chroma_collection", None)
    embedding_model = getattr(request.app.state, "embedding_model", None)

    if collection is None or embedding_model is None:
        logger.error("Vector store or embedding model not initialized in app.state.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database or embedding service is unavailable."
        )

    # Step 1: Retrieval
    context, sources = retrieve_context(
        query=question,
        collection=collection,
        embedding_model=embedding_model,
        top_k=settings.TOP_K
    )

    if not context:
        logger.info(f"No context found for query '{question}'. Returning default ungrounded notice.")
        return QueryResponse(
            answer="I could not find relevant information in the provided documents.",
            sources=[],
            model_used=settings.OLLAMA_MODEL
        )

    # Step 2: Generation via Ollama
    answer, success = await generate_grounded_answer(
        question=question,
        context=context,
        ollama_host=settings.OLLAMA_HOST,
        ollama_model=settings.OLLAMA_MODEL,
        timeout=settings.OLLAMA_TIMEOUT
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        model_used=settings.OLLAMA_MODEL
    )
