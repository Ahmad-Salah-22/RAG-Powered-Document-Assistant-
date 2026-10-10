import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, status
from fastapi.responses import FileResponse
from app.schemas.query import (
    DocumentListResponse,
    DocumentInfo,
    UploadResponse,
    DeleteResponse,
    AnalyticsResponse,
    DocumentPageResponse
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

    valid_extensions = [".pdf", ".txt", ".md", ".markdown", ".docx", ".pptx", ".csv", ".xlsx"]
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
            char_count=result["char_count"],
            file_type=result.get("file_type", ext.lstrip(".")),
            requires_ocr=result.get("requires_ocr", False),
            summary_preview=result.get("summary_preview")
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


@router.get(
    "/{document_name}/file",
    summary="Download or Stream Document File",
    description="Returns raw file stream (PDF, DOCX, TXT, etc.) for in-browser visual inspection."
)
async def get_document_file(document_name: str):
    """Streams the physical document file for embedding in browser PDF viewer."""
    possible_paths = [
        os.path.join("./data/raw", document_name),
        os.path.join("data/raw", document_name),
        os.path.abspath(os.path.join("data", "raw", document_name)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raw", document_name))
    ]
    file_path = None
    for p in possible_paths:
        if os.path.isfile(p):
            file_path = p
            break

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Raw document file '{document_name}' not found on server disk."
        )

    ext = os.path.splitext(document_name)[1].lower()
    media_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".csv": "text/csv",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=document_name,
        headers={"Content-Disposition": f"inline; filename={document_name}"}
    )


@router.get(
    "/{document_name}/page/{page_number}",
    response_model=DocumentPageResponse,
    summary="Inspect Document Page Content",
    description="Returns text content, character count, and total page count for a specific page of an indexed document."
)
async def get_document_page(document_name: str, page_number: int, request: Request, highlight: Optional[str] = None):
    """Retrieves text content for a specific page of an indexed document."""
    if page_number < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be >= 1.")

    collection = getattr(request.app.state, "chroma_collection", None)

    # Check if raw file exists
    possible_paths = [
        os.path.join("./data/raw", document_name),
        os.path.join("data/raw", document_name),
        os.path.abspath(os.path.join("data", "raw", document_name)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "raw", document_name))
    ]
    raw_path = next((p for p in possible_paths if os.path.isfile(p)), None)

    ext = os.path.splitext(document_name)[1].lower().lstrip(".") or "pdf"
    page_text = ""
    total_pages = 1

    if raw_path:
        try:
            with open(raw_path, "rb") as f:
                content = f.read()
            from app.services.ingestion import extract_from_bytes
            pages, stats = extract_from_bytes(content, document_name)
            total_pages = max(1, stats.get("page_count", len(pages)))
            target_page = next((p for p in pages if p.get("page") == page_number), None)
            if target_page:
                page_text = target_page.get("text", "")
            elif page_number <= len(pages):
                page_text = pages[page_number - 1].get("text", "")
        except Exception as e:
            logger.warning(f"Could not extract page {page_number} directly from disk file '{document_name}': {e}")

    # Fallback to ChromaDB chunks if raw file reading yielded empty or wasn't found
    if not page_text and collection is not None:
        try:
            results = collection.get(where={"document": document_name})
            if results and results.get("metadatas"):
                doc_chunks = []
                max_page_seen = 1
                for meta, doc_str in zip(results["metadatas"], results.get("documents", [])):
                    p_num = meta.get("page", 1)
                    if p_num > max_page_seen:
                        max_page_seen = p_num
                    if p_num == page_number:
                        doc_chunks.append(doc_str)
                total_pages = max(total_pages, max_page_seen)
                page_text = "\n\n".join(doc_chunks)
        except Exception as e:
            logger.warning(f"Error querying ChromaDB for page {page_number} of '{document_name}': {e}")

    if not page_text and not raw_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_name}' or Page {page_number} not found."
        )

    return DocumentPageResponse(
        document_name=document_name,
        page_number=page_number,
        total_pages=total_pages,
        text_content=page_text,
        char_count=len(page_text),
        has_file=raw_path is not None,
        file_type=ext
    )
