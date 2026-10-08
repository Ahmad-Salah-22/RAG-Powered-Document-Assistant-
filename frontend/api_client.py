import os
import time
from typing import Dict, Any, Tuple, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class RAGApiClient:
    """HTTP Client for communicating with the FastAPI RAG backend."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def check_health(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Queries backend GET /health diagnostic endpoint.
        Returns (is_online, health_data_dict) including roundtrip ping_ms.
        """
        t0 = time.perf_counter()
        try:
            with httpx.Client(timeout=4.0) as client:
                response = client.get(f"{self.base_url}/health")
                latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                if response.status_code == 200:
                    data = response.json()
                    data["ping_ms"] = latency_ms
                    return True, data
                return False, {"error": f"HTTP {response.status_code}: {response.text}", "ping_ms": latency_ms}
        except httpx.ConnectError:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return False, {"error": f"Cannot connect to backend server at {self.base_url}.", "ping_ms": latency_ms}
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            return False, {"error": str(e), "ping_ms": latency_ms}

    def submit_query(
        self,
        question: str,
        top_k: Optional[int] = None,
        model: Optional[str] = None,
        document_filter: Optional[List[str]] = None,
        similarity_threshold: Optional[float] = None,
        system_prompt_mode: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Sends user question and optional configuration to POST /query endpoint.
        Returns (success, response_dict).
        """
        url = f"{self.base_url}/query"
        payload: Dict[str, Any] = {"question": question}

        if top_k is not None:
            payload["top_k"] = top_k
        if model:
            payload["model"] = model
        if document_filter:
            payload["document_filter"] = document_filter
        if similarity_threshold is not None:
            payload["similarity_threshold"] = similarity_threshold
        if system_prompt_mode:
            payload["system_prompt_mode"] = system_prompt_mode
        if chat_history:
            payload["chat_history"] = chat_history

        try:
            with httpx.Client(timeout=65.0) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    return True, response.json()
                elif response.status_code == 422:
                    return False, {"error": "Invalid request: Question cannot be empty or invalid parameters."}
                elif response.status_code == 503:
                    return False, {"error": "Service Unavailable: Vector DB or LLM service is offline."}
                else:
                    return False, {"error": f"Backend Error ({response.status_code}): {response.text}"}
        except httpx.ConnectError:
            return False, {"error": f"Failed to connect to backend server at {self.base_url}. Please ensure FastAPI is running."}
        except httpx.TimeoutException:
            return False, {"error": "Request timed out while waiting for LLM generation response."}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}

    def get_documents(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Fetches list of all indexed documents from GET /documents.
        """
        try:
            with httpx.Client(timeout=6.0) as client:
                response = client.get(f"{self.base_url}/documents")
                if response.status_code == 200:
                    return True, response.json()
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}

    def upload_document(self, file_bytes: bytes, filename: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Uploads and indexes a file into ChromaDB via POST /documents/upload.
        """
        try:
            files = {"file": (filename, file_bytes)}
            with httpx.Client(timeout=60.0) as client:
                response = client.post(f"{self.base_url}/documents/upload", files=files)
                if response.status_code == 200:
                    return True, response.json()
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}

    def delete_document(self, document_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Deletes a document from the vector store via DELETE /documents/{document_name}.
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.delete(f"{self.base_url}/documents/{document_name}")
                if response.status_code == 200:
                    return True, response.json()
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}

    def reindex_documents(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Triggers a full reindexing via POST /documents/reindex.
        """
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/documents/reindex")
                if response.status_code == 200:
                    return True, response.json()
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}

    def get_analytics(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Retrieves full analytics summary from GET /documents/analytics/summary.
        """
        try:
            with httpx.Client(timeout=6.0) as client:
                response = client.get(f"{self.base_url}/documents/analytics/summary")
                if response.status_code == 200:
                    return True, response.json()
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return False, {"error": str(e)}

    def get_sample_raw_files(self) -> List[Dict[str, Any]]:
        """
        Scans local filesystem for available sample PDF/document files in data/raw.
        Returns list of file info dicts (name, path, size_kb).
        """
        possible_dirs = [
            os.path.join(os.path.dirname(__file__), "..", "data", "raw"),
            os.path.join(os.getcwd(), "data", "raw"),
            os.path.join(os.getcwd(), "..", "data", "raw"),
            os.path.abspath("data/raw")
        ]
        valid_extensions = {".pdf", ".txt", ".md", ".markdown"}
        found_files: List[Dict[str, Any]] = []
        seen_names = set()

        for d in possible_dirs:
            if os.path.isdir(d):
                try:
                    for fname in os.listdir(d):
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in valid_extensions and fname not in seen_names:
                            fpath = os.path.join(d, fname)
                            if os.path.isfile(fpath):
                                size_bytes = os.path.getsize(fpath)
                                found_files.append({
                                    "filename": fname,
                                    "filepath": fpath,
                                    "size_kb": round(size_bytes / 1024, 1),
                                    "extension": ext.lstrip(".")
                                })
                                seen_names.add(fname)
                except Exception:
                    continue
        return found_files

    def ingest_local_sample_file(self, filepath: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Reads a local sample file and submits it to upload_document.
        """
        try:
            filename = os.path.basename(filepath)
            with open(filepath, "rb") as f:
                content = f.read()
            return self.upload_document(content, filename)
        except Exception as e:
            return False, {"error": f"Failed reading local file '{filepath}': {str(e)}"}

