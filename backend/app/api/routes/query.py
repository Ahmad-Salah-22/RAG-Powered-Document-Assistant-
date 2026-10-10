import time
from fastapi import APIRouter, HTTPException, Request, status
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    SourceItem,
    CompareDocumentsRequest,
    CompareDocumentsResponse
)
from app.services.retrieval import retrieve_context, get_indexed_documents_stats
from app.services.generation import generate_grounded_answer, check_ollama_availability
from app.services.agentic_rag import execute_agentic_rag, execute_multi_document_comparison
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
    logger.info(f"Received query request: '{question}' (mode={payload.system_prompt_mode}, top_k={payload.top_k}, agentic={payload.agentic_mode})")

    collection = getattr(request.app.state, "chroma_collection", None)
    embedding_model = getattr(request.app.state, "embedding_model", None)
    reranker_model = getattr(request.app.state, "reranker_model", None)

    if collection is None or embedding_model is None:
        logger.error("Vector store or embedding model not initialized in app.state.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database or embedding service is unavailable."
        )

    # Retrieval parameters
    top_k = payload.top_k or settings.TOP_K
    model_name = payload.model or settings.OLLAMA_MODEL
    retrieval_mode = payload.retrieval_mode or getattr(settings, "DEFAULT_RETRIEVAL_MODE", "hybrid")
    enable_reranker = payload.enable_reranker if payload.enable_reranker is not None else getattr(settings, "ENABLE_RERANKER", False)
    query_expansion = bool(payload.query_expansion)

    # Convert chat history if present
    chat_history_list = None
    if payload.chat_history:
        chat_history_list = [t.model_dump() for t in payload.chat_history]

    # Branch: Agentic Reasoning Mode (CRAG + Multi-hop Decomposition)
    if payload.agentic_mode:
        logger.info(f"Engaging Agentic RAG Pipeline for query: '{question}'")
        agentic_result = await execute_agentic_rag(
            question=question,
            collection=collection,
            embedding_model=embedding_model,
            top_k=top_k,
            document_filter=payload.document_filter,
            similarity_threshold=payload.similarity_threshold,
            retrieval_mode=retrieval_mode,
            reranker_model=reranker_model,
            enable_reranker=enable_reranker,
            system_prompt_mode=payload.system_prompt_mode or "academic",
            chat_history=chat_history_list,
            ollama_host=settings.OLLAMA_HOST,
            ollama_model=model_name
        )

        return QueryResponse(
            answer=agentic_result["answer"],
            sources=agentic_result["sources"],
            model_used=agentic_result["model_used"],
            latency_ms=agentic_result["latency_ms"],
            retrieval_latency_ms=agentic_result["retrieval_latency_ms"],
            generation_latency_ms=agentic_result["generation_latency_ms"],
            fallback_used=agentic_result["fallback_used"],
            retrieval_mode=retrieval_mode,
            reranker_used=enable_reranker,
            agentic_active=True,
            intent_type=agentic_result["intent_type"],
            confidence_score=agentic_result["confidence_score"],
            reasoning_steps=agentic_result["reasoning_steps"]
        )

    # Standard Retrieval pipeline
    start_retrieval = time.perf_counter()
    context, sources = retrieve_context(
        query=question,
        collection=collection,
        embedding_model=embedding_model,
        top_k=top_k,
        document_filter=payload.document_filter,
        similarity_threshold=payload.similarity_threshold,
        retrieval_mode=retrieval_mode,
        reranker_model=reranker_model,
        enable_reranker=enable_reranker,
        query_expansion=query_expansion
    )
    retrieval_latency = (time.perf_counter() - start_retrieval) * 1000.0

    reranker_applied = any(s.retrieval_method == "cross_encoder" for s in sources)

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
            fallback_used=False,
            retrieval_mode=retrieval_mode,
            reranker_used=reranker_applied,
            agentic_active=False
        )

    # Generation via Ollama (or smart grounded fallback)
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
        fallback_used=fallback_used,
        retrieval_mode=retrieval_mode,
        reranker_used=reranker_applied,
        agentic_active=False
    )


@router.post(
    "/query/compare",
    response_model=CompareDocumentsResponse,
    summary="Multi-Document Comparative Analysis",
    description="Performs automated side-by-side comparative analysis of two documents on a selected topic."
)
async def compare_documents_route(payload: CompareDocumentsRequest, request: Request):
    """Executes comparative analysis and returns a markdown comparison matrix."""
    collection = getattr(request.app.state, "chroma_collection", None)
    embedding_model = getattr(request.app.state, "embedding_model", None)
    reranker_model = getattr(request.app.state, "reranker_model", None)

    if collection is None or embedding_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store or embedding model not initialized."
        )

    model_name = payload.model or settings.OLLAMA_MODEL

    result = await execute_multi_document_comparison(
        doc_a=payload.doc_a,
        doc_b=payload.doc_b,
        topic=payload.comparison_topic or "Core concepts, algorithms, complexity trade-offs, and practical use cases",
        collection=collection,
        embedding_model=embedding_model,
        reranker_model=reranker_model,
        ollama_host=settings.OLLAMA_HOST,
        ollama_model=model_name
    )

    return CompareDocumentsResponse(
        doc_a=result["doc_a"],
        doc_b=result["doc_b"],
        topic=result["topic"],
        synthesis=result["synthesis"],
        sources_a=result["sources_a"],
        sources_b=result["sources_b"],
        latency_ms=result["latency_ms"],
        fallback_used=result["fallback_used"]
    )
