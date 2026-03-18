"""
Repository for chat-related database operations.
Handles ChatSession and ChatMessage persistence.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


class ChatRepository:
    """Handles all database operations related to chat sessions and messages."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Session Operations ─────────────────────────────────────────────

    async def create_session(
        self, user_id: UUID, title: str = "New Chat"
    ) -> ChatSession:
        """Create a new chat session for a user."""
        session = ChatSession(user_id=user_id, title=title)
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        logger.info("Created chat session: %s for user: %s", session.id, user_id)
        return session

    async def get_session_by_id(self, session_id: UUID) -> Optional[ChatSession]:
        """Retrieve a chat session by its UUID."""
        stmt = select(ChatSession).where(ChatSession.id == session_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sessions_by_user(self, user_id: UUID) -> list[dict]:
        """Retrieve all chat sessions for a user with message counts."""
        stmt = (
            select(
                ChatSession.id,
                ChatSession.title,
                ChatSession.created_at,
                func.count(ChatMessage.id).label("message_count"),
            )
            .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
            .where(ChatSession.user_id == user_id)
            .group_by(ChatSession.id, ChatSession.title, ChatSession.created_at)
            .order_by(ChatSession.created_at.desc())
        )
        result = await self._db.execute(stmt)
        rows = result.all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "created_at": row.created_at,
                "message_count": row.message_count,
            }
            for row in rows
        ]

    # ── Message Operations ─────────────────────────────────────────────

    async def create_message(
        self,
        session_id: UUID,
        user_message: str,
        assistant_response: str,
    ) -> ChatMessage:
        """Create a new chat message within a session."""
        message = ChatMessage(
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response,
        )
        self._db.add(message)
        await self._db.flush()
        await self._db.refresh(message)
        logger.info("Saved message in session: %s", session_id)
        return message

    async def get_messages_by_session(self, session_id: UUID) -> list[ChatMessage]:
        """Retrieve all messages for a given session, ordered by timestamp."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
