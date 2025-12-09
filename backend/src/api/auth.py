"""Authentication API endpoints."""

import logging
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status

from src.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class AuthRequest(BaseModel):
    """Request model for password verification."""

    password: str = Field(..., description="Application password")


class AuthResponse(BaseModel):
    """Response model for authentication."""

    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Status message")


@router.post("/auth/verify", response_model=AuthResponse)
async def verify_password(body: AuthRequest) -> AuthResponse:
    """Verify the application password.

    Args:
        body: Authentication request with password.

    Returns:
        AuthResponse with success status.

    Raises:
        HTTPException 401: If password is incorrect.
    """
    if body.password == settings.app_password:
        logger.info("Successful authentication")
        return AuthResponse(success=True, message="Authentication successful")

    logger.warning("Failed authentication attempt")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid password",
    )
