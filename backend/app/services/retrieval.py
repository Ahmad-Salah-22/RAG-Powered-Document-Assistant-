from typing import List, Dict, Any, Tuple, Optional
import os
import chromadb
from sentence_transformers import SentenceTransformer
from app.utils.logging_config import logger
from app.schemas.query import SourceItem, DocumentInfo


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    """Loads and caches the SentenceTransformer model."""
    logger.info(f"Loading SentenceTransformer embedding model: '{model_name}'")
    model = SentenceTransformer(model_name)
    return model


def get_chroma_collection(chroma_path: str, collection_name: str = "rag_documents"):
    """
    Connects to persistent ChromaDB client and fetches target collection.
    Returns collection object or None if path/collection doesn't exist yet.
    """
    abs_chroma_path = os.path.abspath(chroma_path)
    logger.info(f"Connecting to ChromaDB persistent storage at: '{abs_chroma_path}'")
    
    if not os.path.exists(abs_chroma_path):
        os.makedirs(abs_chroma_path, exist_ok=True)
        
    client = chromadb.PersistentClient(path=abs_chroma_path)
    
    try:
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Successfully connected to collection '{collection_name}' (Total items: {collection.count()})")
        return collection
    except Exception as e:
        logger.error(f"Error connecting to ChromaDB collection '{collection_name}': {e}")
        return None


def calculate_confidence(distance: Optional[float]) -> Optional[float]:
    """Calculates an intuitive confidence percentage from cosine distance."""
    if distance is None:
        return None
    # For cosine distance: 0 = identical, 1 = orthogonal, 2 = opposite
    # Typical relevant threshold in dense search is < 0.6
    confidence = max(0.0, min(100.0, (1.0 - min(distance, 1.0)) * 100.0))
    return round(confidence, 1)


def retrieve_context(
    query: str,
    collection,
    embedding_model: SentenceTransformer,
    top_k: int = 4,
    document_filter: Optional[List[str]] = None,
    similarity_threshold: Optional[float] = None
) -> Tuple[str, List[SourceItem]]:
    """
    Retrieves top_k context chunks from ChromaDB vector store relevant to query.
    Supports filtering by specific document titles and similarity distance thresholds.

    Returns:
        Tuple containing:
        - Formatted context string for LLM prompt
        - List of SourceItem citation objects with confidence scores
    """
    if collection is None or collection.count() == 0:
        logger.warning("Vector store collection is empty or not initialized.")
        return "", []

    try:
        # Encode query using SentenceTransformer
        logger.info(f"Encoding query with embedding model: '{query[:60]}...'")
        query_embedding = embedding_model.encode([query]).tolist()[0]

        # Build where clause if document filter is supplied
        where_clause = None
        if document_filter and len(document_filter) > 0:
            cleaned_filters = [d.strip() for d in document_filter if d.strip()]
            if len(cleaned_filters) == 1:
                where_clause = {"document": cleaned_filters[0]}
            elif len(cleaned_filters) > 1:
                where_clause = {"document": {"$in": cleaned_filters}}

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(max(1, top_k), collection.count()),
            "include": ["documents", "metadatas", "distances"]
        }
        if where_clause:
            query_kwargs["where"] = where_clause

        results = collection.query(**query_kwargs)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        context_blocks = []
        sources: List[SourceItem] = []
        seen_sources = set()

        for idx, (doc_text, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            doc_name = meta.get("document", "Unknown Document")
            page_num = int(meta.get("page", 1))
            
            # Distance in cosine space (0 is identical, higher is further)
            score = round(float(dist), 4) if dist is not None else None
            
            # Filter out chunks that exceed similarity threshold if specified
            if similarity_threshold is not None and score is not None and score > similarity_threshold:
                continue

            confidence = calculate_confidence(score)

            # Add context block for prompt
            block = (
                f"[Source {idx+1}: {doc_name}, Page {page_num}]\n"
                f"{doc_text}\n"
            )
            context_blocks.append(block)

            # Deduplicate source citations for user display
            source_key = (doc_name, page_num)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                snippet = doc_text[:140] + "..." if len(doc_text) > 140 else doc_text
                sources.append(
                    SourceItem(
                        document=doc_name,
                        page=page_num,
                        snippet=snippet,
                        score=score,
                        confidence_percent=confidence
                    )
                )

        formatted_context = "\n---\n".join(context_blocks)
        logger.info(f"Retrieved {len(context_blocks)} chunks across {len(sources)} source pages.")
        return formatted_context, sources

    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        return "", []


def get_indexed_documents_stats(collection, raw_dir: str = "./data/raw") -> List[DocumentInfo]:
    """
    Scans the ChromaDB collection to produce aggregated document metadata.
    """
    if collection is None or collection.count() == 0:
        return []

    try:
        data = collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])

        doc_map: Dict[str, Dict[str, Any]] = {}
        for m in metadatas:
            if not m:
                continue
            doc_name = m.get("document", "Unknown")
            page = int(m.get("page", 1))
            char_len = int(m.get("char_length", 0))

            if doc_name not in doc_map:
                doc_map[doc_name] = {
                    "chunks": 0,
                    "pages": set(),
                    "char_count": 0
                }
            doc_map[doc_name]["chunks"] += 1
            doc_map[doc_name]["pages"].add(page)
            doc_map[doc_name]["char_count"] += char_len

        document_list: List[DocumentInfo] = []
        for name, stats in sorted(doc_map.items()):
            pages_sorted = sorted(list(stats["pages"]))
            file_size = None
            candidate_path = os.path.join(raw_dir, name)
            if os.path.exists(candidate_path):
                file_size = os.path.getsize(candidate_path)

            document_list.append(
                DocumentInfo(
                    document_name=name,
                    chunk_count=stats["chunks"],
                    pages=pages_sorted,
                    page_count=len(pages_sorted),
                    char_count=stats["char_count"],
                    file_size_bytes=file_size
                )
            )

        return document_list

    except Exception as e:
        logger.error(f"Error fetching document statistics: {e}", exc_info=True)
        return []


def delete_document_from_collection(collection, document_name: str, raw_dir: str = "./data/raw") -> int:
    """
    Deletes all chunks belonging to a document from ChromaDB and removes the file if stored in raw_dir.
    Returns number of deleted chunks.
    """
    if collection is None:
        return 0

    try:
        # Find matching items
        matching = collection.get(where={"document": document_name})
        ids_to_delete = matching.get("ids", [])
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} vectors for document '{document_name}'.")

        # Optionally remove physical file from raw_dir if present
        raw_file_path = os.path.join(raw_dir, document_name)
        if os.path.exists(raw_file_path):
            try:
                os.remove(raw_file_path)
                logger.info(f"Removed physical file from '{raw_file_path}'.")
            except Exception as e:
                logger.warning(f"Could not delete physical file '{raw_file_path}': {e}")

        return len(ids_to_delete)

    except Exception as e:
        logger.error(f"Error deleting document '{document_name}': {e}", exc_info=True)
        return 0
