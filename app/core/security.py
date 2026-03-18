"""
Security module for password hashing and JWT token management.
Provides SecurityService class and FastAPI dependency for auth.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_settings

# HTTP Bearer scheme for extracting tokens from Authorization header
bearer_scheme = HTTPBearer()


class SecurityService:
    """Handles password hashing and JWT token creation/verification."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a plaintext password using bcrypt."""
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a bcrypt hash."""
        return self._pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token with an expiration time."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta
            or timedelta(minutes=self._settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(
            to_encode,
            self._settings.JWT_SECRET_KEY,
            algorithm=self._settings.JWT_ALGORITHM,
        )

    def decode_access_token(self, token: str) -> dict:
        """Decode and validate a JWT access token. Raises on invalid/expired tokens."""
        try:
            payload = jwt.decode(
                token,
                self._settings.JWT_SECRET_KEY,
                algorithms=[self._settings.JWT_ALGORITHM],
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e


def get_security_service() -> SecurityService:
    """Factory function for SecurityService dependency injection."""
    return SecurityService(settings=get_settings())


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    security_service: SecurityService = Depends(get_security_service),
) -> str:
    """
    FastAPI dependency that extracts and validates the JWT token
    from the Authorization header. Returns the user_id (subject).
    """
    token = credentials.credentials
    payload = security_service.decode_access_token(token)
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
