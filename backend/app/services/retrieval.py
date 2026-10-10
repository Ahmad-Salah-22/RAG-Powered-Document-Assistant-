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


import math
import re
from collections import Counter

_reranker_instance = None


class BM25OkapiIndex:
    """
    Lightweight, fast in-memory BM25Okapi implementation for lexical search over chunk collections.
    """
    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lens: List[int] = []
        self.doc_freqs: List[Counter] = []
        self.nd: Dict[str, int] = {}
        self.avgdl = 0.0
        self.idf: Dict[str, float] = {}
        self._initialize(corpus)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b\w+\b", text) if len(w) > 1]

    def _initialize(self, corpus: List[str]):
        total_len = 0
        for doc in corpus:
            tokens = self.tokenize(doc)
            self.doc_lens.append(len(tokens))
            total_len += len(tokens)
            freqs = Counter(tokens)
            self.doc_freqs.append(freqs)
            for term in freqs:
                self.nd[term] = self.nd.get(term, 0) + 1

        self.avgdl = (total_len / self.corpus_size) if self.corpus_size > 0 else 0.0
        for term, freq in self.nd.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: str) -> List[float]:
        query_tokens = self.tokenize(query)
        scores = [0.0] * self.corpus_size
        if self.avgdl == 0.0 or not query_tokens:
            return scores

        for q in query_tokens:
            if q not in self.idf:
                continue
            q_idf = self.idf[q]
            for idx in range(self.corpus_size):
                freq = self.doc_freqs[idx].get(q, 0)
                if freq > 0:
                    denom = freq + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[idx] / self.avgdl))
                    scores[idx] += q_idf * (freq * (self.k1 + 1.0)) / denom
        return scores


def load_reranker_model(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
    """Loads and caches the CrossEncoder model with graceful fallback."""
    global _reranker_instance
    if _reranker_instance is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading Cross-Encoder reranker: '{model_name}'")
            _reranker_instance = CrossEncoder(model_name)
        except Exception as e:
            logger.warning(f"Could not load CrossEncoder model '{model_name}': {e}. Reranking will be disabled.")
            _reranker_instance = None
    return _reranker_instance


def expand_query(query: str) -> str:
    """Expands technical terms or common abbreviations for better keyword recall."""
    acronyms = {
        "rag": "retrieval augmented generation dense vector embeddings",
        "oop": "object oriented programming inheritance encapsulation polymorphism abstraction",
        "llm": "large language model generative ai",
        "ml": "machine learning supervised unsupervised training",
        "api": "application programming interface endpoint rest",
        "db": "database vector store sql nosql",
        "bfs": "breadth first search graph traversal queue",
        "dfs": "depth first search graph traversal stack",
    }
    words = re.findall(r"\b\w+\b", query.lower())
    expansions = []
    for w in words:
        if w in acronyms:
            expansions.append(acronyms[w])
    if expansions:
        return f"{query} {' '.join(expansions)}"
    return query


def retrieve_context(
    query: str,
    collection,
    embedding_model: SentenceTransformer,
    top_k: int = 4,
    document_filter: Optional[List[str]] = None,
    similarity_threshold: Optional[float] = None,
    retrieval_mode: str = "hybrid",
    reranker_model = None,
    enable_reranker: bool = False,
    query_expansion: bool = False
) -> Tuple[str, List[SourceItem]]:
    """
    Advanced context retrieval supporting:
    - Dense vector search (SentenceTransformers + ChromaDB)
    - Lexical search (BM25 Okapi)
    - Hybrid search via Reciprocal Rank Fusion (RRF)
    - Cross-Encoder re-ranking (joint attention query-document scoring)
    - Query expansion & document filtering
    """
    if collection is None or collection.count() == 0:
        logger.warning("Vector store collection is empty or not initialized.")
        return "", []

    try:
        active_query = expand_query(query) if query_expansion else query
        where_clause = None
        if document_filter and len(document_filter) > 0:
            cleaned_filters = [d.strip() for d in document_filter if d.strip()]
            if len(cleaned_filters) == 1:
                where_clause = {"document": cleaned_filters[0]}
            elif len(cleaned_filters) > 1:
                where_clause = {"document": {"$in": cleaned_filters}}

        total_in_coll = collection.count()
        candidate_k = min(total_in_coll, max(top_k * 3, 10))

        # -------------------------------------------------------------
        # Step A: Dense Vector Retrieval
        # -------------------------------------------------------------
        dense_results_dict: Dict[str, Dict[str, Any]] = {}
        dense_ranks: Dict[str, int] = {}
        if retrieval_mode in ["dense", "hybrid"]:
            query_embedding = embedding_model.encode([active_query]).tolist()[0]
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": candidate_k,
                "include": ["documents", "metadatas", "distances"]
            }
            if where_clause:
                query_kwargs["where"] = where_clause

            d_res = collection.query(**query_kwargs)
            d_docs = d_res.get("documents", [[]])[0]
            d_metas = d_res.get("metadatas", [[]])[0]
            d_dists = d_res.get("distances", [[]])[0]
            d_ids = d_res.get("ids", [[]])[0]

            for rank_idx, (c_id, doc_text, meta, dist) in enumerate(zip(d_ids, d_docs, d_metas, d_dists), start=1):
                dense_ranks[c_id] = rank_idx
                dense_results_dict[c_id] = {
                    "id": c_id,
                    "text": doc_text,
                    "meta": meta or {},
                    "distance": float(dist) if dist is not None else None,
                    "dense_rank": rank_idx
                }

        # -------------------------------------------------------------
        # Step B: BM25 Lexical Retrieval
        # -------------------------------------------------------------
        bm25_results_dict: Dict[str, Dict[str, Any]] = {}
        bm25_ranks: Dict[str, int] = {}
        if retrieval_mode in ["bm25", "hybrid"]:
            corpus_kwargs = {"include": ["documents", "metadatas"]}
            if where_clause:
                corpus_kwargs["where"] = where_clause
            all_chunks = collection.get(**corpus_kwargs)
            corpus_docs = all_chunks.get("documents", [])
            corpus_metas = all_chunks.get("metadatas", [])
            corpus_ids = all_chunks.get("ids", [])

            if corpus_docs:
                bm25_index = BM25OkapiIndex(corpus_docs)
                bm25_scores = bm25_index.get_scores(active_query)
                scored_indices = sorted(range(len(corpus_docs)), key=lambda i: bm25_scores[i], reverse=True)

                for rank_idx, idx in enumerate(scored_indices[:candidate_k], start=1):
                    c_id = corpus_ids[idx]
                    bm25_ranks[c_id] = rank_idx
                    bm25_results_dict[c_id] = {
                        "id": c_id,
                        "text": corpus_docs[idx],
                        "meta": corpus_metas[idx] or {},
                        "bm25_score": bm25_scores[idx],
                        "bm25_rank": rank_idx
                    }

        # -------------------------------------------------------------
        # Step C: Ranking & Reciprocal Rank Fusion (RRF)
        # -------------------------------------------------------------
        candidates: List[Dict[str, Any]] = []

        if retrieval_mode == "dense":
            candidates = sorted(dense_results_dict.values(), key=lambda x: x["dense_rank"])
            for c in candidates:
                c["combined_score"] = 1.0 / (c["distance"] + 0.0001) if c["distance"] is not None else 1.0
                c["method"] = "dense"

        elif retrieval_mode == "bm25":
            candidates = sorted(bm25_results_dict.values(), key=lambda x: x["bm25_rank"])
            for c in candidates:
                c["combined_score"] = c.get("bm25_score", 0.0)
                c["distance"] = None
                c["method"] = "bm25"

        else:  # "hybrid"
            all_ids = set(dense_results_dict.keys()) | set(bm25_results_dict.keys())
            rrf_k = 60
            for c_id in all_ids:
                d_item = dense_results_dict.get(c_id)
                b_item = bm25_results_dict.get(c_id)

                meta = (d_item or b_item)["meta"]
                text = (d_item or b_item)["text"]
                d_rank = dense_ranks.get(c_id)
                b_rank = bm25_ranks.get(c_id)
                distance = d_item["distance"] if d_item else None

                rrf_score = 0.0
                if d_rank is not None:
                    rrf_score += 1.0 / (rrf_k + d_rank)
                if b_rank is not None:
                    rrf_score += 1.0 / (rrf_k + b_rank)

                candidates.append({
                    "id": c_id,
                    "text": text,
                    "meta": meta,
                    "distance": distance,
                    "dense_rank": d_rank,
                    "bm25_rank": b_rank,
                    "combined_score": rrf_score,
                    "method": "hybrid_rrf"
                })

            candidates.sort(key=lambda x: x["combined_score"], reverse=True)

        # -------------------------------------------------------------
        # Step D: Cross-Encoder Re-Ranking
        # -------------------------------------------------------------
        reranker = reranker_model
        if enable_reranker and reranker is None:
            reranker = load_reranker_model()

        reranker_applied = False
        if enable_reranker and reranker is not None and candidates:
            try:
                top_to_rerank = candidates[:min(len(candidates), max(top_k * 2, 8))]
                pairs = [(query, c["text"]) for c in top_to_rerank]
                scores = reranker.predict(pairs)
                for c, s in zip(top_to_rerank, scores):
                    c["rerank_score"] = float(s)
                    c["method"] = "cross_encoder"

                top_to_rerank.sort(key=lambda x: x["rerank_score"], reverse=True)
                candidates = top_to_rerank + candidates[len(top_to_rerank):]
                reranker_applied = True
                logger.info(f"Cross-Encoder re-ranked top {len(top_to_rerank)} candidates.")
            except Exception as e:
                logger.warning(f"Cross-Encoder reranking error: {e}. Keeping base ranking.")

        # -------------------------------------------------------------
        # Step E: Filter and Truncate to Top-K
        # -------------------------------------------------------------
        final_candidates = []
        for c in candidates:
            # Distance filter if specified
            if similarity_threshold is not None and c.get("distance") is not None:
                if c["distance"] > similarity_threshold:
                    continue
            final_candidates.append(c)
            if len(final_candidates) >= top_k:
                break

        # -------------------------------------------------------------
        # Step F: Format Context Blocks & Build SourceItems
        # -------------------------------------------------------------
        context_blocks = []
        sources: List[SourceItem] = []
        seen_sources = set()

        for idx, item in enumerate(final_candidates):
            meta = item.get("meta", {})
            doc_name = meta.get("document", "Unknown Document")
            page_num = int(meta.get("page", 1))
            doc_text = item["text"]
            score = round(item["distance"], 4) if item.get("distance") is not None else None
            confidence = calculate_confidence(score)

            # Build context block for prompt
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
                        confidence_percent=confidence,
                        retrieval_method=item.get("method", "dense"),
                        dense_rank=item.get("dense_rank"),
                        bm25_rank=item.get("bm25_rank"),
                        rerank_score=round(item["rerank_score"], 4) if item.get("rerank_score") is not None else None
                    )
                )

        formatted_context = "\n---\n".join(context_blocks)
        logger.info(
            f"Retrieved {len(context_blocks)} chunks across {len(sources)} source pages "
            f"(mode={retrieval_mode}, reranked={reranker_applied})."
        )
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

            ext = os.path.splitext(name)[1].lower().lstrip(".") or "unknown"
            document_list.append(
                DocumentInfo(
                    document_name=name,
                    chunk_count=stats["chunks"],
                    pages=pages_sorted,
                    page_count=len(pages_sorted),
                    char_count=stats["char_count"],
                    file_size_bytes=file_size,
                    file_type=ext
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
