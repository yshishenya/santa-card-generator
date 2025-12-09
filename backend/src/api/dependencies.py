"""FastAPI dependencies for API routes.

This module provides dependency injection for service instances,
ensuring singleton lifecycle management and proper cleanup.
"""

import logging

from src.config import settings
from src.core import CardService, SessionManager
from src.integrations import GeminiClient, TelegramClient
from src.integrations.exceptions import GeminiConfigError, TelegramConfigError
from src.repositories import EmployeeRepository

logger = logging.getLogger(__name__)

# Singletons - initialized on first access
_session_manager: SessionManager | None = None
_gemini_client: GeminiClient | None = None
_telegram_client: TelegramClient | None = None
_employee_repo: EmployeeRepository | None = None
_card_service: CardService | None = None


def get_session_manager() -> SessionManager:
    """Get singleton SessionManager instance.

    Returns:
        Singleton SessionManager instance configured with max regenerations.
    """
    global _session_manager
    if _session_manager is None:
        logger.info("Initializing SessionManager singleton")
        _session_manager = SessionManager(max_regenerations=settings.max_regenerations)
    return _session_manager


def get_gemini_client() -> GeminiClient:
    """Get singleton GeminiClient instance.

    Returns:
        Singleton GeminiClient instance configured with LiteLLM proxy settings.

    Raises:
        GeminiConfigError: If Gemini client configuration is invalid.
    """
    global _gemini_client
    if _gemini_client is None:
        logger.info("Initializing GeminiClient singleton (LiteLLM proxy)")
        try:
            _gemini_client = GeminiClient(
                api_key=settings.gemini_api_key,
                base_url=settings.gemini_base_url,
                text_model=settings.gemini_text_model,
                image_model=settings.gemini_image_model,
            )
        except GeminiConfigError as e:
            logger.error(
                "Failed to initialize GeminiClient: %s",
                e.message,
                extra={"details": e.details},
            )
            raise
    return _gemini_client


def get_telegram_client() -> TelegramClient:
    """Get singleton TelegramClient instance.

    Returns:
        Singleton TelegramClient instance configured with bot token and chat settings.

    Raises:
        TelegramConfigError: If Telegram client configuration is invalid.
    """
    global _telegram_client
    if _telegram_client is None:
        logger.info("Initializing TelegramClient singleton")
        try:
            _telegram_client = TelegramClient(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.telegram_chat_id,
                topic_id=settings.telegram_topic_id,
            )
        except TelegramConfigError as e:
            logger.error(
                "Failed to initialize TelegramClient: %s",
                e.message,
                extra={"details": e.details},
            )
            raise
    return _telegram_client


def get_employee_repo() -> EmployeeRepository:
    """Get singleton EmployeeRepository instance.

    Returns:
        Singleton EmployeeRepository instance configured with employees file path.
    """
    global _employee_repo
    if _employee_repo is None:
        logger.info(f"Initializing EmployeeRepository singleton with path: {settings.employees_file_path}")
        _employee_repo = EmployeeRepository(settings.employees_file_path)
    return _employee_repo


def get_card_service() -> CardService:
    """Get singleton CardService instance."""
    global _card_service
    if _card_service is None:
        logger.info("Initializing CardService singleton")
        _card_service = CardService(
            gemini_client=get_gemini_client(),
            telegram_client=get_telegram_client(),
            employee_repo=get_employee_repo(),
            max_regenerations=settings.max_regenerations,
            session_ttl_minutes=settings.session_ttl_minutes,
        )
    return _card_service


async def startup() -> None:
    """Initialize services on application startup.

    Pre-initializes all singleton services to ensure they're ready
    before the first request arrives.
    """
    logger.info("Running startup initialization")
    # Pre-initialize all singletons
    get_card_service()
    logger.info("All services initialized successfully")


async def shutdown() -> None:
    """Cleanup resources on application shutdown.

    Closes all client connections and releases resources.
    """
    global _gemini_client, _telegram_client, _card_service, _session_manager, _employee_repo

    logger.info("Running shutdown cleanup")

    # Close Gemini client if initialized
    if _gemini_client is not None:
        logger.info("Closing GeminiClient")
        await _gemini_client.close()
        _gemini_client = None

    # Close Telegram client if initialized
    if _telegram_client is not None:
        logger.info("Closing TelegramClient")
        await _telegram_client.close()
        _telegram_client = None

    # Clear other singletons
    _card_service = None
    _session_manager = None
    _employee_repo = None

    logger.info("Shutdown cleanup completed")
