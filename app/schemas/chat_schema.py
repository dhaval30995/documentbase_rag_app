"""
Pydantic schemas for chat requests and responses.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for a chat message request."""

    question: str = Field(..., min_length=1, description="User question")
    session_id: Optional[str] = Field(None, description="Existing session ID (optional)")


class ChatResponse(BaseModel):
    """Schema for a chat message response."""

    answer: str
    session_id: str
    sources: list[str] = Field(default_factory=list)


class ChatMessageResponse(BaseModel):
    """Schema for a single chat message in history."""

    id: UUID
    user_message: str
    assistant_response: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    """Schema for a chat session summary."""

    id: UUID
    title: str
    created_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True
