import os
from typing import List
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, status
from app.schemas.query import (
    DocumentListResponse,
    DocumentInfo,
    UploadResponse,
    DeleteResponse,
    AnalyticsResponse
)
from app.services.retrieval import (
    get_indexed_documents_stats,
    delete_document_from_collection
)
from app.services.ingestion import (
    index_uploaded_file,
    build_and_persist_vector_store
)
from app.services.generation import (
    check_ollama_availability,
    get_available_ollama_models
)
from app.utils.logging_config import logger
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["Document Management"])


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List All Indexed Documents",
    description="Returns metadata, chunk statistics, and page breakdowns for all documents currently indexed in ChromaDB."
)
async def list_documents(request: Request):
    """Lists all indexed documents and their chunk counts."""
    collection = getattr(request.app.state, "chroma_collection", None)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is not initialized."
        )

    doc_stats = get_indexed_documents_stats(collection)
    total_chunks = sum(d.chunk_count for d in doc_stats)

    return DocumentListResponse(
        total_documents=len(doc_stats),
        total_chunks=total_chunks,
        documents=doc_stats
    )


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload and Index New Document",
    description="Accepts a PDF, TXT, or Markdown file, extracts text, chunks it, embeds it, and saves it into ChromaDB."
)
async def upload_document(
    request: Request,
    file: UploadFile = File(...)
):
    """Uploads and embeds a document directly into the vector database."""
    collection = getattr(request.app.state, "chroma_collection", None)
    embedding_model = getattr(request.app.state, "embedding_model", None)

    if collection is None or embedding_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database or embedding model is not initialized."
        )

    filename = file.filename
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided.")

    valid_extensions = [".pdf", ".txt", ".md", ".markdown"]
    ext = os.path.splitext(filename)[1].lower()
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(valid_extensions)}"
        )

    try:
        content = await file.read()
        logger.info(f"Processing uploaded file '{filename}' ({len(content)} bytes)")

        result = index_uploaded_file(
            file_bytes=content,
            filename=filename,
            collection=collection,
            embedding_model=embedding_model
        )

        return UploadResponse(
            message=f"Document '{filename}' successfully indexed into vector store.",
            document_name=filename,
            pages=result["pages"],
            chunks_indexed=result["chunks_indexed"],
            char_count=result["char_count"]
        )

    except Exception as e:
        logger.error(f"Failed to process uploaded file '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}"
        )


@router.delete(
    "/{document_name}",
    response_model=DeleteResponse,
    summary="Delete Document from Vector Store",
    description="Deletes all vectors and metadata associated with the specified document from ChromaDB."
)
async def delete_document(document_name: str, request: Request):
    """Deletes a document and its vectors from the assistant index."""
    collection = getattr(request.app.state, "chroma_collection", None)
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store is not initialized."
        )

    deleted_count = delete_document_from_collection(collection, document_name)
    if deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_name}' not found or had no indexed chunks."
        )

    return DeleteResponse(
        message=f"Document '{document_name}' removed from vector index.",
        document_name=document_name,
        chunks_deleted=deleted_count
    )


@router.post(
    "/reindex",
    summary="Trigger Reindexing of Raw Documents",
    description="Re-scans all files in the data directory and rebuilds the ChromaDB vector collection."
)
async def reindex_documents(request: Request):
    """Rebuilds the ChromaDB collection from scratch."""
    try:
        summary = build_and_persist_vector_store()
        # Refresh collection pointer in app state
        from app.services.retrieval import get_chroma_collection
        request.app.state.chroma_collection = get_chroma_collection(
            chroma_path=settings.CHROMA_PATH,
            collection_name=settings.COLLECTION_NAME
        )
        return {
            "message": "Vector store reindexing completed successfully.",
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Reindexing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing error: {str(e)}"
        )


@router.get(
    "/analytics/summary",
    response_model=AnalyticsResponse,
    summary="RAG Analytics and Health Summary",
    description="Provides detailed metrics on vector storage, indexed documents, and connected LLM services."
)
async def get_analytics(request: Request):
    """Detailed analytics metrics for RAG Assistant."""
    collection = getattr(request.app.state, "chroma_collection", None)
    if collection is None:
        doc_stats = []
        total_chunks = 0
    else:
        doc_stats = get_indexed_documents_stats(collection)
        total_chunks = collection.count()

    ollama_ok = await check_ollama_availability(settings.OLLAMA_HOST)
    models_available = await get_available_ollama_models(settings.OLLAMA_HOST) if ollama_ok else []

    return AnalyticsResponse(
        total_documents=len(doc_stats),
        total_chunks=total_chunks,
        embedding_model=settings.EMBEDDING_MODEL_NAME,
        collection_name=settings.COLLECTION_NAME,
        vector_store_path=os.path.abspath(settings.CHROMA_PATH),
        documents=doc_stats,
        ollama_status={
            "available": ollama_ok,
            "host": settings.OLLAMA_HOST,
            "configured_model": settings.OLLAMA_MODEL,
            "available_models": models_available
        }
    )
