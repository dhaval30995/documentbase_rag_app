"""
Chat service.
Manages chat sessions and message persistence using repositories.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ChatMessage, ChatSession
from app.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)


class ChatService:
    """
    Business logic for chat session and message management.
    Delegates persistence to ChatRepository.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = ChatRepository(db)

    async def create_session(self, user_id: str, title: str = "New Chat") -> ChatSession:
        """Create a new chat session for a user."""
        return await self._repo.create_session(
            user_id=UUID(user_id),
            title=title,
        )

    async def save_message(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
    ) -> ChatMessage:
        """Persist a user-assistant message pair to a session."""
        return await self._repo.create_message(
            session_id=UUID(session_id),
            user_message=user_message,
            assistant_response=assistant_response,
        )

    async def get_user_sessions(self, user_id: str) -> list[dict]:
        """Retrieve all chat sessions for a user with message counts."""
        return await self._repo.get_sessions_by_user(user_id=UUID(user_id))

    async def get_session_messages(self, session_id: str) -> list[ChatMessage]:
        """Retrieve all messages for a given session."""
        return await self._repo.get_messages_by_session(session_id=UUID(session_id))
