"""
Embedding service.
Loads a SentenceTransformer model and generates vector embeddings for text.
"""

import logging
from typing import Union

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Manages the SentenceTransformer model lifecycle and
    generates embeddings for text inputs.
    """

    _instance: "EmbeddingService | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingService":
        """Singleton pattern — ensures the model is loaded only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if EmbeddingService._model is None:
            settings = get_settings()
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL_NAME)
            EmbeddingService._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            logger.info("Embedding model loaded successfully")

    def generate_embeddings(self, texts: Union[str, list[str]]) -> list[list[float]]:
        """
        Generate embeddings for one or more texts.

        Args:
            texts: A single string or list of strings to embed.

        Returns:
            A list of embedding vectors (list of floats).
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return []

        embeddings = self._model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def generate_single_embedding(self, text: str) -> list[float]:
        """Generate an embedding for a single text string."""
        embeddings = self.generate_embeddings(text)
        return embeddings[0] if embeddings else []
