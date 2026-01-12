"""
Embedding service for Marcus v0.3.
Optional offline semantic search using sentence-transformers.
Gracefully degrades if dependencies are missing.
"""

from typing import List, Optional
import json

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


class EmbeddingService:
    """
    Generates embeddings using local models (sentence-transformers).

    Graceful degradation:
    - If sentence-transformers not installed: is_available() = False
    - If model fails to load: is_available() = False
    - System falls back to FTS5 search
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.

        Default model: all-MiniLM-L6-v2
        - Small (80MB)
        - Fast
        - Good quality for semantic search
        - Runs offline
        """
        self.model_name = model_name
        self.model = None
        self._available = False

        try:
            self._initialize_model()
        except Exception as e:
            print(f"[EmbeddingService] Failed to initialize: {e}")
            print("[EmbeddingService] Embeddings disabled, using FTS5 only")

    def _initialize_model(self):
        """Try to load the embedding model."""
        if not NUMPY_AVAILABLE:
            print("[EmbeddingService] numpy not installed")
            print("[EmbeddingService] Install with: pip install numpy")
            self._available = False
            return

        try:
            from sentence_transformers import SentenceTransformer

            print(f"[EmbeddingService] Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self._available = True
            print("[EmbeddingService] Model loaded successfully")

        except ImportError:
            print("[EmbeddingService] sentence-transformers not installed")
            print("[EmbeddingService] Install with: pip install sentence-transformers")
            self._available = False

        except Exception as e:
            print(f"[EmbeddingService] Error loading model: {e}")
            self._available = False

    def is_available(self) -> bool:
        """Check if embeddings are available."""
        return self._available and self.model is not None

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a text string.

        Returns:
            List of floats (embedding vector)

        Raises:
            RuntimeError if embeddings not available
        """
        if not self.is_available():
            raise RuntimeError("Embeddings not available")

        # Truncate if too long (model has max length)
        if len(text) > 5000:
            text = text[:5000]

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient).

        Returns:
            List of embedding vectors
        """
        if not self.is_available():
            raise RuntimeError("Embeddings not available")

        # Truncate long texts
        truncated_texts = [t[:5000] if len(t) > 5000 else t for t in texts]

        embeddings = self.model.encode(truncated_texts, convert_to_numpy=True)
        return embeddings.tolist()

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Returns:
            Similarity score (0.0 to 1.0, higher = more similar)
        """
        if not NUMPY_AVAILABLE:
            raise RuntimeError("Numpy not available for similarity calculation")

        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Normalize
        v1_norm = v1 / np.linalg.norm(v1)
        v2_norm = v2 / np.linalg.norm(v2)

        # Cosine similarity
        similarity = np.dot(v1_norm, v2_norm)

        # Clamp to [0, 1]
        similarity = max(0.0, min(1.0, similarity))

        return float(similarity)

    def get_model_info(self) -> dict:
        """Return information about the current model."""
        return {
            'available': self.is_available(),
            'model_name': self.model_name,
            'embedding_dim': self.model.get_sentence_embedding_dimension() if self.model else None,
            'max_seq_length': self.model.max_seq_length if self.model else None
        }


# Global instance (optional)
_embedding_service_instance = None


def get_embedding_service() -> Optional[EmbeddingService]:
    """
    Get global embedding service instance.
    Returns None if not available.
    """
    global _embedding_service_instance

    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()

    if not _embedding_service_instance.is_available():
        return None

    return _embedding_service_instance
