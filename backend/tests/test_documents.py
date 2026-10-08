import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.query import DocumentInfo


@pytest.fixture
def mock_app_state():
    """Sets up mock app state for testing endpoints without loading full models."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 5
    mock_model = MagicMock()

    app.state.chroma_collection = mock_collection
    app.state.embedding_model = mock_model
    yield app
    app.state.chroma_collection = None
    app.state.embedding_model = None


@patch("app.api.routes.documents.get_indexed_documents_stats")
def test_list_documents(mock_get_stats, mock_app_state):
    """Test GET /documents returns list of indexed documents."""
    mock_get_stats.return_value = [
        DocumentInfo(
            document_name="algorithms.pdf",
            chunk_count=12,
            pages=[1, 2, 3],
            page_count=3,
            char_count=5400,
            file_size_bytes=45000
        )
    ]

    with TestClient(app) as client:
        response = client.get("/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["total_documents"] == 1
        assert data["total_chunks"] == 12
        assert len(data["documents"]) == 1
        assert data["documents"][0]["document_name"] == "algorithms.pdf"


@patch("app.api.routes.documents.index_uploaded_file")
def test_upload_document_success(mock_index, mock_app_state):
    """Test POST /documents/upload processes and indexes text file."""
    mock_index.return_value = {
        "document_name": "notes.txt",
        "pages": 1,
        "chunks_indexed": 4,
        "char_count": 2100
    }

    file_content = b"This is a test document covering binary trees and recursion."
    files = {"file": ("notes.txt", io.BytesIO(file_content), "text/plain")}

    with TestClient(app) as client:
        response = client.post("/documents/upload", files=files)
        assert response.status_code == 200
        data = response.json()
        assert "notes.txt" in data["message"]
        assert data["chunks_indexed"] == 4
        assert data["document_name"] == "notes.txt"


def test_upload_unsupported_file_format(mock_app_state):
    """Test POST /documents/upload rejects invalid file extensions."""
    files = {"file": ("script.exe", io.BytesIO(b"executable content"), "application/octet-stream")}

    with TestClient(app) as client:
        response = client.post("/documents/upload", files=files)
        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file format" in data["detail"]


@patch("app.api.routes.documents.delete_document_from_collection")
def test_delete_document_success(mock_del, mock_app_state):
    """Test DELETE /documents/{name} deletes target document."""
    mock_del.return_value = 8

    with TestClient(app) as client:
        response = client.delete("/documents/algorithms.pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["chunks_deleted"] == 8
        assert data["document_name"] == "algorithms.pdf"


@patch("app.api.routes.documents.delete_document_from_collection")
def test_delete_document_not_found(mock_del, mock_app_state):
    """Test DELETE /documents/{name} returns 404 if document does not exist."""
    mock_del.return_value = 0

    with TestClient(app) as client:
        response = client.delete("/documents/nonexistent.pdf")
        assert response.status_code == 404


@patch("app.api.routes.documents.check_ollama_availability")
@patch("app.api.routes.documents.get_indexed_documents_stats")
def test_analytics_summary(mock_stats, mock_ollama, mock_app_state):
    """Test GET /documents/analytics/summary returns system health metrics."""
    mock_stats.return_value = []
    mock_ollama.return_value = True

    with TestClient(app) as client:
        response = client.get("/documents/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "embedding_model" in data
        assert "ollama_status" in data
