"""
General utility / helper functions used across the application.
"""

import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def get_timestamp() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to a maximum length, appending ellipsis if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "…"


def sanitize_filename(filename: str) -> str:
    """
    Remove potentially unsafe characters from a filename.
    Keeps alphanumeric, dashes, underscores, and dots.
    """
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
    return "".join(c for c in filename if c in safe_chars) or "unnamed_file"
