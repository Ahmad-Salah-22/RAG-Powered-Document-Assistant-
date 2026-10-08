import os
import io
import glob
from typing import List, Dict, Any, Tuple
import pypdf
import chromadb
from sentence_transformers import SentenceTransformer
from app.utils.logging_config import logger
from app.core.config import settings


def extract_pdf_pages(pdf_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extracts text page by page from a PDF file using PyPDF.

    Returns:
        Tuple of (list of page dicts, document stats dict)
    """
    doc_name = os.path.basename(pdf_path)
    pages = []
    stats = {
        "document": doc_name,
        "page_count": 0,
        "char_count": 0,
        "failed_pages": 0,
        "requires_ocr": False
    }

    try:
        reader = pypdf.PdfReader(pdf_path)
        stats["page_count"] = len(reader.pages)

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
                cleaned_text = " ".join(text.split())
                char_len = len(cleaned_text)

                if char_len < 20:  # Potential image-only / OCR page
                    stats["requires_ocr"] = True

                stats["char_count"] += char_len
                pages.append({
                    "document": doc_name,
                    "page": page_num,
                    "text": cleaned_text
                })
            except Exception as e:
                logger.error(f"Error extracting page {page_num} in '{doc_name}': {e}")
                stats["failed_pages"] += 1

    except Exception as e:
        logger.error(f"Failed to read PDF '{doc_name}': {e}")

    return pages, stats


def extract_from_bytes(file_bytes: bytes, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extracts text and page metadata from in-memory file bytes.
    Supports PDF, TXT, and Markdown files.
    """
    ext = os.path.splitext(filename)[1].lower()
    pages = []
    stats = {
        "document": filename,
        "page_count": 0,
        "char_count": 0,
        "failed_pages": 0,
        "requires_ocr": False
    }

    if ext == ".pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            stats["page_count"] = len(reader.pages)
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    text = page.extract_text() or ""
                    cleaned_text = " ".join(text.split())
                    char_len = len(cleaned_text)
                    if char_len < 20:
                        stats["requires_ocr"] = True
                    stats["char_count"] += char_len
                    pages.append({
                        "document": filename,
                        "page": page_num,
                        "text": cleaned_text
                    })
                except Exception as e:
                    logger.error(f"Error reading page {page_num} of {filename}: {e}")
                    stats["failed_pages"] += 1
        except Exception as e:
            logger.error(f"Failed to parse PDF bytes for '{filename}': {e}")
    elif ext in [".txt", ".md", ".markdown"]:
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            cleaned_text = " ".join(text.split())
            stats["page_count"] = 1
            stats["char_count"] = len(cleaned_text)
            pages.append({
                "document": filename,
                "page": 1,
                "text": cleaned_text
            })
        except Exception as e:
            logger.error(f"Failed to decode text file '{filename}': {e}")
    else:
        # Fallback raw decode
        text = file_bytes.decode("utf-8", errors="ignore")
        cleaned_text = " ".join(text.split())
        stats["page_count"] = 1
        stats["char_count"] = len(cleaned_text)
        pages.append({
            "document": filename,
            "page": 1,
            "text": cleaned_text
        })

    return pages, stats


def chunk_text(
    pages: List[Dict[str, Any]],
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """
    Splits page text into overlapping chunks while preserving page metadata.
    """
    chunks = []
    global_chunk_counter = 0

    for page_info in pages:
        text = page_info["text"]
        doc_name = page_info["document"]
        page_num = page_info["page"]

        if not text:
            continue

        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_str = text[start:end].strip()

            if chunk_str:
                global_chunk_counter += 1
                chunk_id = f"{doc_name}_p{page_num}_c{global_chunk_counter}"
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_str,
                    "metadata": {
                        "document": doc_name,
                        "page": page_num,
                        "chunk_id": chunk_id,
                        "char_length": len(chunk_str)
                    }
                })

            if end == text_len:
                break
            start += (chunk_size - chunk_overlap)

    return chunks


def index_uploaded_file(
    file_bytes: bytes,
    filename: str,
    collection,
    embedding_model: SentenceTransformer,
    raw_data_dir: str = "./data/raw"
) -> Dict[str, Any]:
    """
    Takes an uploaded file's bytes, saves a copy in raw_data_dir, extracts, chunks,
    generates embeddings, and appends to the active ChromaDB collection.
    """
    os.makedirs(raw_data_dir, exist_ok=True)
    saved_path = os.path.join(raw_data_dir, filename)
    with open(saved_path, "wb") as f:
        f.write(file_bytes)
    logger.info(f"Saved uploaded file to disk at '{saved_path}'")

    # If document already existed in collection, remove old chunks first
    try:
        existing = collection.get(where={"document": filename})
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
            logger.info(f"Cleaned up {len(existing['ids'])} existing chunks for overwritten document '{filename}'")
    except Exception as e:
        logger.warning(f"Could not purge existing chunks for '{filename}': {e}")

    pages, stats = extract_from_bytes(file_bytes, filename)
    chunks = chunk_text(pages)

    if not chunks:
        logger.warning(f"No chunks created from uploaded file '{filename}'")
        return {
            "document_name": filename,
            "pages": len(pages),
            "chunks_indexed": 0,
            "char_count": stats.get("char_count", 0)
        }

    chunk_texts = [c["text"] for c in chunks]
    embeddings = embedding_model.encode(chunk_texts, show_progress_bar=False).tolist()

    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=chunk_texts[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )

    logger.info(f"Successfully indexed {len(chunks)} chunks for uploaded file '{filename}'.")
    return {
        "document_name": filename,
        "pages": len(pages),
        "chunks_indexed": len(chunks),
        "char_count": stats.get("char_count", 0)
    }


def build_and_persist_vector_store(
    raw_data_dir: str = "./data/raw",
    chroma_path: str = settings.CHROMA_PATH,
    collection_name: str = settings.COLLECTION_NAME,
    embedding_model_name: str = settings.EMBEDDING_MODEL_NAME
) -> Dict[str, Any]:
    """
    Full pipeline to load raw documents (PDF, TXT, MD), chunk, compute embeddings, and persist to ChromaDB.
    """
    logger.info("=== Starting Data Ingestion Pipeline ===")
    supported_extensions = ["*.pdf", "*.txt", "*.md"]
    doc_files = []
    for ext in supported_extensions:
        doc_files.extend(glob.glob(os.path.join(raw_data_dir, ext)))
    
    if not doc_files:
        logger.warning(f"No documents found in raw data directory '{raw_data_dir}'.")
        return {"documents_processed": 0, "total_chunks": 0}

    all_pages = []
    all_doc_stats = []

    for file_path in doc_files:
        logger.info(f"Processing document: '{file_path}'")
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            b = f.read()
        pages, stats = extract_from_bytes(b, filename)
        all_pages.extend(pages)
        all_doc_stats.append(stats)

    chunks = chunk_text(all_pages)
    logger.info(f"Extracted {len(all_pages)} total pages across {len(doc_files)} documents.")
    logger.info(f"Generated {len(chunks)} text chunks (size={settings.CHUNK_SIZE}, overlap={settings.CHUNK_OVERLAP}).")

    if not chunks:
        logger.warning("No text chunks generated.")
        return {"documents_processed": len(doc_files), "total_chunks": 0}

    # Load embedding model
    model = SentenceTransformer(embedding_model_name)
    chunk_texts = [c["text"] for c in chunks]

    logger.info(f"Generating embeddings using '{embedding_model_name}'...")
    embeddings = model.encode(chunk_texts, show_progress_bar=False).tolist()

    # ChromaDB persistent store initialization
    abs_chroma_path = os.path.abspath(chroma_path)
    os.makedirs(abs_chroma_path, exist_ok=True)

    client = chromadb.PersistentClient(path=abs_chroma_path)
    
    # Reset/recreate collection for fresh indexing
    try:
        client.delete_collection(name=collection_name)
        logger.info(f"Reset existing collection '{collection_name}'.")
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Add to ChromaDB in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        collection.add(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            documents=chunk_texts[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )

    logger.info(f"Successfully saved {collection.count()} vectors into persistent database at '{abs_chroma_path}'.")

    pipeline_summary = {
        "documents_processed": len(doc_files),
        "total_pages": sum(s["page_count"] for s in all_doc_stats),
        "total_chunks": len(chunks),
        "vector_store_path": abs_chroma_path,
        "doc_stats": all_doc_stats
    }

    logger.info("=== Ingestion Pipeline Completed Successfully ===")
    return pipeline_summary


if __name__ == "__main__":
    summary = build_and_persist_vector_store()
    print("Ingestion Summary:", summary)
