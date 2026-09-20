import os
from typing import Dict, Any, Tuple
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
        Returns (is_online, health_data_dict).
        """
        try:
            with httpx.Client(timeout=4.0) as client:
                response = client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return True, response.json()
                return False, {"error": f"HTTP {response.status_code}: {response.text}"}
        except httpx.ConnectError:
            return False, {"error": f"Cannot connect to backend server at {self.base_url}."}
        except Exception as e:
            return False, {"error": str(e)}

    def submit_query(self, question: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Sends user question to POST /query endpoint.
        Returns (success, response_dict).
        """
        url = f"{self.base_url}/query"
        payload = {"question": question}

        try:
            with httpx.Client(timeout=65.0) as client:
                response = client.post(url, json=payload)
                if response.status_code == 200:
                    return True, response.json()
                elif response.status_code == 422:
                    return False, {"error": "Invalid request: Question cannot be empty."}
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
