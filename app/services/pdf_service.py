"""
PDF processing service.
Handles PDF file reading, text extraction, chunking, and
orchestrating the embedding + vector storage pipeline.
"""

import io
import logging
from typing import BinaryIO

from PyPDF2 import PdfReader

from app.core.config import get_settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorStoreService
from app.utils.helpers import generate_uuid, sanitize_filename
from app.utils.text_splitter import RecursiveTextSplitter

logger = logging.getLogger(__name__)


class PDFService:
    """
    Processes PDF files: extracts text, splits into chunks,
    generates embeddings, and stores in the vector database.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._text_splitter = RecursiveTextSplitter(
            chunk_size=self._settings.CHUNK_SIZE,
            chunk_overlap=self._settings.CHUNK_OVERLAP,
        )
        self._embedding_service = EmbeddingService()
        self._vector_store = VectorStoreService()

    def extract_text(self, file_content: BinaryIO) -> str:
        """
        Extract all text from a PDF file.

        Args:
            file_content: A file-like object containing PDF bytes.

        Returns:
            The concatenated text from all pages.
        """
        try:
            reader = PdfReader(file_content)
            text_parts: list[str] = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n\n".join(text_parts)
            logger.info("Extracted %d characters from PDF (%d pages)",
                        len(full_text), len(reader.pages))
            return full_text
        except Exception as e:
            logger.error("Failed to extract text from PDF: %s", str(e))
            raise ValueError(f"Failed to read PDF file: {str(e)}") from e

    def process_pdf(self, file_content: bytes, filename: str, user_id: str) -> int:
        """
        Full PDF processing pipeline:
        1. Extract text from PDF
        2. Split text into chunks
        3. Generate embeddings for all chunks
        4. Store embeddings with metadata in ChromaDB

        Args:
            file_content: Raw PDF file bytes.
            filename: Original filename.
            user_id: ID of the uploading user.

        Returns:
            The number of chunks created and stored.
        """
        safe_filename = sanitize_filename(filename)
        logger.info("Processing PDF: %s for user: %s", safe_filename, user_id)

        # Step 1: Extract text
        pdf_stream = io.BytesIO(file_content)
        text = self.extract_text(pdf_stream)

        if not text.strip():
            logger.warning("PDF '%s' contained no extractable text", safe_filename)
            return 0

        # Step 2: Chunk text
        chunks = self._text_splitter.split_text(text)
        if not chunks:
            logger.warning("No chunks produced from PDF '%s'", safe_filename)
            return 0

        logger.info("Created %d chunks from '%s'", len(chunks), safe_filename)

        # Step 3: Generate embeddings
        embeddings = self._embedding_service.generate_embeddings(chunks)

        # Step 4: Prepare metadata and IDs
        ids: list[str] = []
        metadatas: list[dict] = []
        for i, _chunk in enumerate(chunks):
            chunk_id = generate_uuid()
            ids.append(chunk_id)
            metadatas.append({
                "user_id": user_id,
                "document_name": safe_filename,
                "chunk_id": str(i),
            })

        # Step 5: Store in vector database
        self._vector_store.add_documents(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info("Successfully stored %d chunks for '%s'", len(chunks), safe_filename)
        return len(chunks)
