"""
RAG (Retrieval-Augmented Generation) service.
Orchestrates the full pipeline: embed query → retrieve context → prompt LLM → return answer.
"""

import logging

from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.vector_service import VectorStoreService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Full RAG pipeline orchestrator.

    Flow:
        1. Generate embedding for the user's query.
        2. Search the vector store for relevant document chunks (filtered by user).
        3. Build a prompt with retrieved context.
        4. Send prompt to the LLM.
        5. Return the generated answer and source references.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStoreService()
        self._llm_service = LLMService()

    def answer_question(self, question: str, user_id: str) -> dict:
        """
        Process a user question through the RAG pipeline.

        Args:
            question: The user's natural language question.
            user_id: The ID of the user asking the question.

        Returns:
            A dict with 'answer' (str) and 'sources' (list of source doc names).
        """
        logger.info("RAG pipeline started for user: %s", user_id)

        # Step 1: Generate query embedding
        query_embedding = self._embedding_service.generate_single_embedding(question)
        if not query_embedding:
            logger.warning("Failed to generate embedding for query")
            return {
                "answer": "I was unable to process your question. Please try again.",
                "sources": [],
            }

        # Step 2: Retrieve relevant chunks from vector store
        search_results = self._vector_store.search(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=self._settings.TOP_K_RESULTS,
        )

        if not search_results:
            logger.info("No relevant documents found for user: %s", user_id)
            return {
                "answer": "I don't have any relevant documents to answer your question. "
                          "Please upload some PDF documents first.",
                "sources": [],
            }

        # Step 3: Build context from retrieved chunks
        context_parts: list[str] = []
        source_names: set[str] = set()

        for i, result in enumerate(search_results, 1):
            context_parts.append(f"[Chunk {i}]: {result['document']}")
            doc_name = result.get("metadata", {}).get("document_name", "Unknown")
            source_names.add(doc_name)

        context = "\n\n".join(context_parts)

        # Step 4: Build the augmented prompt
        augmented_prompt = self._build_prompt(question, context)

        # Step 5: Generate answer via LLM
        answer = self._llm_service.generate_response(prompt=augmented_prompt)

        logger.info("RAG pipeline completed. Sources: %s", list(source_names))
        return {
            "answer": answer,
            "sources": list(source_names),
        }

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """Build the augmented prompt with context and question."""
        return (
            "Use the following context to answer the user's question. "
            "If the context does not contain enough information, say so clearly. "
            "Do not make up information.\n\n"
            "--- CONTEXT ---\n"
            f"{context}\n\n"
            "--- QUESTION ---\n"
            f"{question}\n\n"
            "--- ANSWER ---"
        )

    def answer_question_stream(self, question: str, user_id: str):
        """
        Stream the LLM response for a user question through the RAG pipeline.

        Args:
            question: The user's natural language question.
            user_id: The ID of the user asking the question.

        Yields:
            A tuple of (chunk_type, chunk_data).
            - ('token', "text chunk") for LLM text.
            - ('sources', ["doc1", "doc2"]) once sources are ready.
            - ('full_response', "complete text") at the end.
        """
        logger.info("RAG streaming pipeline started for user: %s", user_id)

        # Step 1: Generate query embedding
        query_embedding = self._embedding_service.generate_single_embedding(question)
        if not query_embedding:
            logger.warning("Failed to generate embedding for query")
            yield 'token', "I was unable to process your question. Please try again."
            yield 'sources', []
            yield 'full_response', "I was unable to process your question. Please try again."
            return

        # Step 2: Retrieve relevant chunks
        search_results = self._vector_store.search(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=self._settings.TOP_K_RESULTS,
        )

        if not search_results:
            logger.info("No relevant documents found for user: %s", user_id)
            no_docs_msg = "I don't have any relevant documents to answer your question. Please upload some PDF documents first."
            yield 'token', no_docs_msg
            yield 'sources', []
            yield 'full_response', no_docs_msg
            return

        # Step 3: Build context
        context_parts: list[str] = []
        source_names: set[str] = set()

        for i, result in enumerate(search_results, 1):
            context_parts.append(f"[Chunk {i}]: {result['document']}")
            doc_name = result.get("metadata", {}).get("document_name", "Unknown")
            source_names.add(doc_name)

        context = "\n\n".join(context_parts)
        
        # Yield the sources to the caller immediately
        yield 'sources', list(source_names)

        # Step 4: Build prompt
        augmented_prompt = self._build_prompt(question, context)

        # Step 5: Generate and stream answer
        full_response_parts = []
        for chunk in self._llm_service.generate_response_stream(prompt=augmented_prompt):
            full_response_parts.append(chunk)
            yield 'token', chunk

        # Finalize and yield full response for DB saving
        full_text = "".join(full_response_parts)
        logger.info("RAG streaming pipeline completed. Sources: %s", list(source_names))
        yield 'full_response', full_text
