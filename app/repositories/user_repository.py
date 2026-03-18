"""
Repository for user-related database operations.
Implements the repository pattern for clean separation of data access.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Handles all database operations related to User entities."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_user(self, username: str, email: str, hashed_password: str) -> User:
        """Create a new user and persist to database."""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        logger.info("Created user: %s (id=%s)", username, user.id)
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by their username."""
        stmt = select(User).where(User.username == username)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Retrieve a user by their UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
