"""
Authentication router.
Exposes POST /register and POST /login endpoints.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SecurityService, get_security_service
from app.database.postgres import get_db
from app.schemas.user_schema import TokenResponse, UserLogin, UserRegister
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
    security: SecurityService = Depends(get_security_service),
) -> TokenResponse:
    """Register a new user and return a JWT token."""
    logger.info("Registration attempt for username: %s", data.username)
    auth_service = AuthService(db=db, security=security)
    return await auth_service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
    security: SecurityService = Depends(get_security_service),
) -> TokenResponse:
    """Authenticate a user and return a JWT token."""
    logger.info("Login attempt for username: %s", data.username)
    auth_service = AuthService(db=db, security=security)
    return await auth_service.login(data)
