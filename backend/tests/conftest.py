import sys
import os
from unittest.mock import MagicMock, patch

# Ensure backend directory is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Mock heavy modules before anything else loads them
mock_embed_model = MagicMock()
mock_embed_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384])

mock_collection = MagicMock()
mock_collection.count.return_value = 10
mock_collection.get.return_value = {"metadatas": [{"document": "test.pdf", "page": 1, "char_length": 500}]}

patcher1 = patch("app.main.load_embedding_model", return_value=mock_embed_model)
patcher2 = patch("app.main.get_chroma_collection", return_value=mock_collection)
patcher1.start()
patcher2.start()
