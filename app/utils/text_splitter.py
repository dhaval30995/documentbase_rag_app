"""
Utility module for recursive text splitting.
Splits large text documents into smaller overlapping chunks for embedding.
"""

import logging

logger = logging.getLogger(__name__)


class RecursiveTextSplitter:
    """
    Splits text recursively using a hierarchy of separators.
    Produces overlapping chunks suitable for RAG pipelines.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        """
        Split text into chunks using recursive separators.

        Args:
            text: The input text to split.

        Returns:
            A list of text chunks.
        """
        if not text or not text.strip():
            return []

        chunks = self._recursive_split(text, self._separators)
        # Merge small chunks and apply overlap
        merged = self._merge_chunks(chunks)
        logger.debug("Split text into %d chunks (size=%d, overlap=%d)",
                      len(merged), self._chunk_size, self._chunk_overlap)
        return merged

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """Recursively split text using the separator hierarchy."""
        if len(text) <= self._chunk_size:
            return [text.strip()] if text.strip() else []

        # Try each separator in order
        for i, separator in enumerate(separators):
            if separator == "":
                # Last resort: split by character count
                return self._split_by_characters(text)

            if separator in text:
                parts = text.split(separator)
                result: list[str] = []
                current = ""

                for part in parts:
                    candidate = f"{current}{separator}{part}" if current else part
                    if len(candidate) <= self._chunk_size:
                        current = candidate
                    else:
                        if current:
                            result.append(current.strip())
                        # If a single part exceeds chunk_size, split it further
                        if len(part) > self._chunk_size:
                            sub_chunks = self._recursive_split(
                                part, separators[i + 1:]
                            )
                            result.extend(sub_chunks)
                            current = ""
                        else:
                            current = part

                if current and current.strip():
                    result.append(current.strip())

                return [chunk for chunk in result if chunk]

        return self._split_by_characters(text)

    def _split_by_characters(self, text: str) -> list[str]:
        """Split text into fixed-size character chunks."""
        chunks: list[str] = []
        for i in range(0, len(text), self._chunk_size):
            chunk = text[i: i + self._chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _merge_chunks(self, chunks: list[str]) -> list[str]:
        """Merge chunks and apply overlap between consecutive chunks."""
        if not chunks:
            return []

        merged: list[str] = []
        for i, chunk in enumerate(chunks):
            if i > 0 and self._chunk_overlap > 0:
                # Prepend overlap from the tail of the previous chunk
                prev = chunks[i - 1]
                overlap_text = prev[-self._chunk_overlap:]
                chunk_with_overlap = overlap_text + chunk
                # Trim if it exceeds chunk_size
                if len(chunk_with_overlap) > self._chunk_size + self._chunk_overlap:
                    chunk_with_overlap = chunk_with_overlap[: self._chunk_size + self._chunk_overlap]
                merged.append(chunk_with_overlap.strip())
            else:
                merged.append(chunk)

        return [c for c in merged if c]
