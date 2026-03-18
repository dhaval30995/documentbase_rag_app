"""
Pydantic schemas for document upload requests and responses.
"""

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    filename: str
    message: str
    chunks_created: int = Field(..., description="Number of text chunks created")
    status: str = "success"


class DocumentListResponse(BaseModel):
    """Schema for returning a list of uploaded documents."""

    documents: list[str] = Field(default_factory=list, description="List of unique document filenames")
