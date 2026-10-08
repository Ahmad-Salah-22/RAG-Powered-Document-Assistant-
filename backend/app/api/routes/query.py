import time
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.query import QueryRequest, QueryResponse, HealthResponse, SourceItem
from app.services.retrieval import retrieve_context, get_indexed_documents_stats
from app.services.generation import generate_grounded_answer, check_ollama_availability
from app.utils.logging_config import logger
from app.core.config import settings

router = APIRouter(tags=["Document Query"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Diagnostic System Health Check",
    description="Returns vector database connection status, total document chunk count, active document list, and local Ollama service availability."
)
async def health_check(request: Request):
    """Health check endpoint to inspect system status."""
    collection = getattr(request.app.state, "chroma_collection", None)
    vector_db_loaded = collection is not None
    doc_count = collection.count() if vector_db_loaded else 0

    ollama_available = await check_ollama_availability(settings.OLLAMA_HOST)
    overall_status = "healthy" if (vector_db_loaded and ollama_available) else "degraded"

    active_docs = []
    if vector_db_loaded and doc_count > 0:
        stats = get_indexed_documents_stats(collection)
        active_docs = [d.document_name for d in stats]

    return HealthResponse(
        status=overall_status,
        vector_db_loaded=vector_db_loaded,
        ollama_available=ollama_available,
        document_count=doc_count,
        active_documents=active_docs
    )


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit Question to RAG Document Assistant",
    description="Retrieves context chunks from ChromaDB and generates a grounded response with document and page citations using Ollama or fallback synthesis."
)
async def query_documents(payload: QueryRequest, request: Request):
    """Processes user question through the RAG retrieval and LLM generation pipeline."""
    start_total = time.perf_counter()
    question = payload.question
    logger.info(f"Received query request: '{question}' (mode={payload.system_prompt_mode}, top_k={payload.top_k})")

    collection = getattr(request.app.state, "chroma_collection", None)
    embedding_model = getattr(request.app.state, "embedding_model", None)

    if collection is None or embedding_model is None:
        logger.error("Vector store or embedding model not initialized in app.state.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database or embedding service is unavailable."
        )

    # Retrieval parameters
    top_k = payload.top_k or settings.TOP_K
    model_name = payload.model or settings.OLLAMA_MODEL

    # Step 1: Retrieval
    start_retrieval = time.perf_counter()
    context, sources = retrieve_context(
        query=question,
        collection=collection,
        embedding_model=embedding_model,
        top_k=top_k,
        document_filter=payload.document_filter,
        similarity_threshold=payload.similarity_threshold
    )
    retrieval_latency = (time.perf_counter() - start_retrieval) * 1000.0

    if not context:
        logger.info(f"No context found for query '{question}'. Returning default ungrounded notice.")
        total_latency = (time.perf_counter() - start_total) * 1000.0
        return QueryResponse(
            answer="I could not find relevant information in the provided documents.",
            sources=[],
            model_used=model_name,
            latency_ms=round(total_latency, 2),
            retrieval_latency_ms=round(retrieval_latency, 2),
            generation_latency_ms=0.0,
            fallback_used=False
        )

    # Convert chat history if present
    chat_history_list = None
    if payload.chat_history:
        chat_history_list = [t.model_dump() for t in payload.chat_history]

    # Step 2: Generation via Ollama (or smart grounded fallback)
    start_gen = time.perf_counter()
    answer, success, fallback_used = await generate_grounded_answer(
        question=question,
        context=context,
        ollama_host=settings.OLLAMA_HOST,
        ollama_model=model_name,
        timeout=settings.OLLAMA_TIMEOUT,
        system_prompt_mode=payload.system_prompt_mode or "academic",
        chat_history=chat_history_list,
        allow_fallback=True
    )
    generation_latency = (time.perf_counter() - start_gen) * 1000.0
    total_latency = (time.perf_counter() - start_total) * 1000.0

    return QueryResponse(
        answer=answer,
        sources=sources,
        model_used=model_name if not fallback_used else "Extractive Fallback",
        latency_ms=round(total_latency, 2),
        retrieval_latency_ms=round(retrieval_latency, 2),
        generation_latency_ms=round(generation_latency, 2),
        fallback_used=fallback_used
    )
