import pytest
from app.services.retrieval import BM25OkapiIndex, expand_query, retrieve_context
from unittest.mock import MagicMock


def test_bm25_scoring():
    corpus = [
        "Python is an interpreted high-level general-purpose programming language.",
        "Hash tables provide average O(1) constant time lookup complexity.",
        "MergeSort is an O(n log n) comparison-based sorting algorithm."
    ]
    bm25 = BM25OkapiIndex(corpus)
    scores_python = bm25.get_scores("python programming")
    assert scores_python[0] > scores_python[1]
    assert scores_python[0] > scores_python[2]

    scores_hash = bm25.get_scores("hash table lookup")
    assert scores_hash[1] > scores_hash[0]
    assert scores_hash[1] > scores_hash[2]


def test_query_expansion():
    q = "What is RAG?"
    expanded = expand_query(q)
    assert "retrieval augmented generation" in expanded

    q_oop = "Explain OOP principles"
    expanded_oop = expand_query(q_oop)
    assert "encapsulation" in expanded_oop


def test_retrieve_context_hybrid_fallback_empty():
    mock_coll = MagicMock()
    mock_coll.count.return_value = 0
    mock_emb = MagicMock()

    context, sources = retrieve_context(
        query="What is a binary tree?",
        collection=mock_coll,
        embedding_model=mock_emb,
        top_k=3,
        retrieval_mode="hybrid"
    )
    assert context == ""
    assert sources == []
