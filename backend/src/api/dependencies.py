"""FastAPI dependencies for API routes."""

import logging

from src.config import settings
from src.core import CardService
from src.integrations import GeminiClient, TelegramClient
from src.integrations.gemini_client_google_tuned import ReferenceAwareGeminiClient
from src.integrations.exceptions import GeminiConfigError, TelegramConfigError

logger = logging.getLogger(__name__)

_gemini_client: GeminiClient | None = None
_telegram_client: TelegramClient | None = None
_card_service: CardService | None = None


def get_gemini_client() -> GeminiClient:
    """Return the singleton Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        try:
            _gemini_client = ReferenceAwareGeminiClient(
                api_key=settings.gemini_api_key,
                base_url=settings.gemini_base_url,
                text_model=settings.gemini_text_model,
                image_model=settings.gemini_image_model,
            )
        except GeminiConfigError:
            raise
    return _gemini_client


def get_telegram_client() -> TelegramClient:
    """Return the singleton Telegram client."""
    global _telegram_client
    if _telegram_client is None:
        try:
            _telegram_client = TelegramClient(
                bot_token=settings.telegram_bot_token,
                chat_id=settings.active_telegram_chat_id,
                topic_id=settings.active_telegram_topic_id,
                delivery_env=settings.telegram_delivery_env,
            )
        except ValueError as exc:
            raise TelegramConfigError(message=str(exc)) from exc
        except TelegramConfigError:
            raise
    return _telegram_client


def get_card_service() -> CardService:
    """Return the singleton photocard service."""
    global _card_service
    if _card_service is None:
        _card_service = CardService(
            gemini_client=get_gemini_client(),
            telegram_client=get_telegram_client(),
            session_ttl_minutes=settings.session_ttl_minutes,
        )
    return _card_service


async def startup() -> None:
    """Run lightweight startup hooks."""
    logger.info("Startup initialization complete")


async def shutdown() -> None:
    """Cleanup singleton resources."""
    global _gemini_client, _telegram_client, _card_service

    if _gemini_client is not None:
        await _gemini_client.close()
        _gemini_client = None

    if _telegram_client is not None:
        await _telegram_client.close()
        _telegram_client = None

    _card_service = None
