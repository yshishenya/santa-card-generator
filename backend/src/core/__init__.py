"""Core business logic package.

This package contains the core business logic and services for the Santa application.
Services here orchestrate operations between repositories, integrations, and API layers.
"""

from src.core.card_service import CardService, GeminiClient, TelegramClient
from src.core.exceptions import (
    CardServiceError,
    RecipientNotFoundError,
    RegenerationLimitExceededError,
    SessionExpiredError,
    SessionNotFoundError,
    VariantNotFoundError,
)
from src.core.session_manager import GenerationSession, SessionManager

__all__ = [
    # Card Service
    "CardService",
    "GeminiClient",
    "TelegramClient",
    # Exceptions
    "CardServiceError",
    "RecipientNotFoundError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "RegenerationLimitExceededError",
    "VariantNotFoundError",
    # Session Management
    "SessionManager",
    "GenerationSession",
]
