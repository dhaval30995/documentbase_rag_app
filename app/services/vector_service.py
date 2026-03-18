"""
Vector store service.
Manages ChromaDB collections, stores document embeddings, and
performs similarity search with user-level filtering.
"""

import logging
from typing import Any

import chromadb

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Wraps ChromaDB operations: collection management, document
    storage, and similarity search with user-scoped filtering.
    """

    _instance: "VectorStoreService | None" = None
    _client: Any | None = None
    _collection: Any | None = None

    COLLECTION_NAME = "rag_documents"

    def __new__(cls) -> "VectorStoreService":
        """Singleton pattern — one ChromaDB client per process."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if VectorStoreService._client is None:
            settings = get_settings()
            logger.info("Initializing ChromaDB at: %s", settings.CHROMA_DB_PATH)
            try:
                # For ChromaDB >= 0.4.0
                VectorStoreService._client = chromadb.PersistentClient(
                    path=settings.CHROMA_DB_PATH
                )
            except AttributeError:
                # For older ChromaDB versions
                from chromadb.config import Settings as ChromaSettings
                VectorStoreService._client = chromadb.Client(ChromaSettings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=settings.CHROMA_DB_PATH
                ))
            VectorStoreService._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB collection '%s' ready", self.COLLECTION_NAME)

    def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Add document chunks with their embeddings and metadata to ChromaDB.

        Args:
            documents: List of text chunks.
            embeddings: List of embedding vectors.
            metadatas: List of metadata dicts (must include user_id, document_name, chunk_id).
            ids: List of unique IDs for each chunk.
        """
        if not documents:
            logger.warning("add_documents called with empty document list")
            return

        self._collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info("Added %d document chunks to vector store", len(documents))

    def search(
        self,
        query_embedding: list[float],
        user_id: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Perform similarity search filtered by user_id.

        Args:
            query_embedding: The embedding vector for the query.
            user_id: The user ID to filter results.
            top_k: Number of top results to return.

        Returns:
            A list of dicts with keys: document, metadata, distance.
        """
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": user_id},
        )

        if not results or not results.get("documents"):
            logger.info("No results found for user: %s", user_id)
            return []

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)

        search_results = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            search_results.append({
                "document": doc,
                "metadata": meta,
                "distance": dist,
            })

        logger.info("Found %d results for user: %s", len(search_results), user_id)
        return search_results

    def get_document_count(self, user_id: str) -> int:
        """Return the total number of chunks stored for a given user."""
        try:
            results = self._collection.get(
                where={"user_id": user_id},
            )
            return len(results.get("ids", []))
        except Exception:
            return 0

    def get_user_documents(self, user_id: str) -> list[str]:
        """Return a list of unique document names uploaded by the user."""
        try:
            # Only request metadatas to minimize data transfer
            results = self._collection.get(
                where={"user_id": user_id},
                include=["metadatas"]
            )
            metadatas = results.get("metadatas", [])
            doc_names = set()
            for meta in metadatas:
                if meta and "document_name" in meta:
                    doc_names.add(meta["document_name"])
            return sorted(list(doc_names))
        except Exception as e:
            logger.error("Error getting user documents: %s", str(e))
            return []
