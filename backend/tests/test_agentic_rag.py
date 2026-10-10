try:
    import pytest
except ImportError:
    pytest = None
from app.services.agentic_rag import classify_and_decompose_intent, grade_context_relevance
from app.schemas.query import SourceItem


def test_classify_and_decompose_intent_factual():
    """Validates intent classification for direct factual question."""
    res = classify_and_decompose_intent("What is a hash table?")
    assert res["intent_type"] == "factual_lookup"
    assert not res["is_complex"]
    assert len(res["sub_queries"]) == 1


def test_classify_and_decompose_intent_comparison():
    """Validates multi-hop decomposition for comparative questions."""
    res = classify_and_decompose_intent("Compare hash table vs binary search tree")
    assert res["intent_type"] == "multi_hop_comparison"
    assert res["is_complex"]
    assert len(res["sub_queries"]) >= 2
    assert any("hash table" in sq.lower() for sq in res["sub_queries"])
    assert any("binary search tree" in sq.lower() for sq in res["sub_queries"])


def test_classify_and_decompose_intent_complexity():
    """Validates decomposition for Big-O / runtime questions."""
    res = classify_and_decompose_intent("What is the time complexity and runtime of MergeSort?")
    assert res["intent_type"] == "algorithmic_performance"
    assert res["is_complex"]
    assert len(res["sub_queries"]) >= 2


def test_grade_context_relevance_high_quality():
    """Validates CRAG grading for high-confidence sources."""
    sources = [
        SourceItem(document="test.pdf", page=1, snippet="hash tables provide O(1) lookup", confidence_percent=92.0),
        SourceItem(document="test.pdf", page=2, snippet="collision resolution via chaining", confidence_percent=88.0)
    ]
    grading = grade_context_relevance("What is hash table lookup time?", sources, threshold=65.0)
    assert grading["is_sufficient"]
    assert grading["average_confidence"] == 90.0
    assert grading["relevant_count"] == 2


def test_grade_context_relevance_empty():
    """Validates CRAG grading when no sources are retrieved."""
    grading = grade_context_relevance("Unknown query", [], threshold=65.0)
    assert not grading["is_sufficient"]
    assert grading["average_confidence"] == 0.0
    assert grading["relevant_count"] == 0
