"""
Authentication service.
Handles user registration, login, password verification, and JWT issuance.
"""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SecurityService
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import TokenResponse, UserLogin, UserRegister

logger = logging.getLogger(__name__)


class AuthService:
    """Orchestrates authentication workflows: registration and login."""

    def __init__(self, db: AsyncSession, security: SecurityService) -> None:
        self._user_repo = UserRepository(db)
        self._security = security

    async def register(self, data: UserRegister) -> TokenResponse:
        """
        Register a new user.

        Validates uniqueness of username and email, hashes the password,
        persists the user, and returns a JWT token.
        """
        # Check username uniqueness
        existing = await self._user_repo.get_user_by_username(data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Check email uniqueness
        existing_email = await self._user_repo.get_user_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Hash password and create user
        hashed_pw = self._security.hash_password(data.password)
        user = await self._user_repo.create_user(
            username=data.username,
            email=data.email,
            hashed_password=hashed_pw,
        )

        # Generate JWT
        token = self._security.create_access_token(data={"sub": str(user.id)})
        logger.info("User registered: %s", user.username)

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            username=user.username,
        )

    async def login(self, data: UserLogin) -> TokenResponse:
        """
        Authenticate a user with username and password.

        Returns a JWT token on successful authentication.
        """
        user = await self._user_repo.get_user_by_username(data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        if not self._security.verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        token = self._security.create_access_token(data={"sub": str(user.id)})
        logger.info("User logged in: %s", user.username)

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            username=user.username,
        )
