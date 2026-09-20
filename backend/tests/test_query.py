import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.query import SourceItem


@pytest.fixture
def mock_app_state():
    """Sets up mock app state for testing endpoints without loading full models."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 10
    mock_model = MagicMock()

    app.state.chroma_collection = mock_collection
    app.state.embedding_model = mock_model
    yield app
    app.state.chroma_collection = None
    app.state.embedding_model = None


def test_health_check_endpoint(mock_app_state):
    """Test GET /health returns valid diagnostic JSON structure."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "vector_db_loaded" in data
        assert "ollama_available" in data


def test_query_invalid_empty_input(mock_app_state):
    """Test POST /query with empty string returns HTTP 422 Validation Error."""
    with TestClient(app) as client:
        payload = {"question": "   "}
        response = client.post("/query", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


def test_query_missing_field(mock_app_state):
    """Test POST /query with missing 'question' field returns HTTP 422."""
    with TestClient(app) as client:
        payload = {}
        response = client.post("/query", json=payload)
        assert response.status_code == 422


@patch("app.api.routes.query.generate_grounded_answer")
@patch("app.api.routes.query.retrieve_context")
def test_query_valid_request(mock_retrieve, mock_generate, mock_app_state):
    """Test POST /query with valid prompt returns grounded answer and cited sources."""
    mock_retrieve.return_value = (
        "Hash tables provide average O(1) time complexity.",
        [SourceItem(document="cs_data_structures.pdf", page=2, snippet="Hash tables map keys to values", score=0.12)]
    )

    mock_generate.return_value = (
        "Hash tables map keys to values with O(1) average lookup time [cs_data_structures.pdf, Page 2].",
        True
    )

    with TestClient(app) as client:
        payload = {"question": "What is the complexity of a hash table?"}
        response = client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) == 1
        assert data["sources"][0]["document"] == "cs_data_structures.pdf"
        assert data["sources"][0]["page"] == 2
        assert "O(1)" in data["answer"]


@patch("app.api.routes.query.retrieve_context")
def test_query_no_context_found(mock_retrieve, mock_app_state):
    """Test POST /query when no document context matches user query."""
    mock_retrieve.return_value = ("", [])

    with TestClient(app) as client:
        payload = {"question": "What is the capital of France?"}
        response = client.post("/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "could not find relevant information" in data["answer"].lower()
        assert len(data["sources"]) == 0

