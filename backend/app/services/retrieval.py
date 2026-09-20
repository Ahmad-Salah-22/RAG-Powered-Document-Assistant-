from typing import List, Dict, Any, Tuple
import os
import chromadb
from sentence_transformers import SentenceTransformer
from app.utils.logging_config import logger
from app.schemas.query import SourceItem


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


def retrieve_context(
    query: str,
    collection,
    embedding_model: SentenceTransformer,
    top_k: int = 4
) -> Tuple[str, List[SourceItem]]:
    """
    Retrieves top_k context chunks from ChromaDB vector store relevant to query.

    Returns:
        Tuple containing:
        - Formatted context string for LLM prompt
        - List of SourceItem citation objects
    """
    if collection is None or collection.count() == 0:
        logger.warning("Vector store collection is empty or not initialized.")
        return "", []

    try:
        # Encode query using SentenceTransformer
        logger.info(f"Encoding query with embedding model: '{query[:60]}...'")
        query_embedding = embedding_model.encode([query]).tolist()[0]

        # Query ChromaDB collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"]
        )

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
                snippet = doc_text[:120] + "..." if len(doc_text) > 120 else doc_text
                sources.append(
                    SourceItem(
                        document=doc_name,
                        page=page_num,
                        snippet=snippet,
                        score=score
                    )
                )

        formatted_context = "\n---\n".join(context_blocks)
        logger.info(f"Retrieved {len(documents)} chunks across {len(sources)} source pages.")
        return formatted_context, sources

    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        return "", []
