"""
Session router.
Exposes endpoints for retrieving chat sessions and their messages.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.database.postgres import get_db
from app.schemas.chat_schema import ChatMessageResponse, ChatSessionResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("", response_model=list[ChatSessionResponse])
async def get_sessions(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionResponse]:
    """Retrieve all chat sessions for the authenticated user."""
    try:
        chat_service = ChatService(db=db)
        sessions = await chat_service.get_user_sessions(user_id=user_id)
        return [ChatSessionResponse(**s) for s in sessions]
    except Exception as e:
        logger.error("Failed to fetch sessions for user %s: %s", user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions",
        ) from e


@router.get("/messages/{session_id}", response_model=list[ChatMessageResponse])
async def get_messages(
    session_id: str,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatMessageResponse]:
    """Retrieve all messages for a specific chat session."""
    try:
        chat_service = ChatService(db=db)
        messages = await chat_service.get_session_messages(session_id=session_id)
        return [
            ChatMessageResponse(
                id=msg.id,
                user_message=msg.user_message,
                assistant_response=msg.assistant_response,
                timestamp=msg.timestamp,
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error("Failed to fetch messages for session %s: %s",
                     session_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages",
        ) from e
