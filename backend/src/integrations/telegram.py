"""Telegram Bot API integration for photocard delivery."""

import logging
from io import BytesIO
from typing import Literal, Optional

try:
    from telegram import Bot
    from telegram.constants import ParseMode
    from telegram.error import (
        NetworkError,
        RetryAfter,
        TelegramError as TelegramAPIError,
        TimedOut,
    )
except ImportError:  # pragma: no cover - exercised in local test environments
    Bot = None

    class ParseMode:
        HTML = "HTML"

    class TelegramAPIError(Exception):
        """Fallback Telegram API error when python-telegram-bot is unavailable."""

    class NetworkError(TelegramAPIError):
        """Fallback network error when python-telegram-bot is unavailable."""

    class TimedOut(NetworkError):
        """Fallback timeout error when python-telegram-bot is unavailable."""

    class RetryAfter(TelegramAPIError):
        """Fallback retry-after error when python-telegram-bot is unavailable."""

        def __init__(self, retry_after: int) -> None:
            self.retry_after = retry_after
            super().__init__(f"Retry after {retry_after}")
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .exceptions import (
    TelegramConfigError,
    TelegramNetworkError,
    TelegramRateLimitError,
    TelegramSendError,
)

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 2
RETRY_MAX_WAIT_SECONDS = 10


def escape_html(text: str) -> str:
    """Escape text for Telegram HTML captions."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def is_target_config_error_message(error: Exception | str) -> bool:
    """Detect Telegram target misconfiguration errors from exception text."""
    error_message = str(error).lower()
    return any(
        marker in error_message
        for marker in (
            "chat not found",
            "topic not found",
            "thread not found",
            "message thread not found",
            "forbidden",
            "bot was kicked",
            "not enough rights",
        )
    )


class TelegramClient:
    """Client for sending generated photocards to Telegram."""

    def __init__(
        self,
        bot_token: str,
        chat_id: int,
        topic_id: int,
        delivery_env: Literal["staging", "prod"] = "staging",
    ) -> None:
        if not bot_token:
            raise TelegramConfigError(missing_config="telegram_bot_token")
        if not chat_id:
            raise TelegramConfigError(missing_config="telegram_chat_id")
        if topic_id is None:
            raise TelegramConfigError(missing_config="telegram_topic_id")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.topic_id = topic_id
        self.delivery_env = delivery_env
        self._bot = Bot(token=self.bot_token) if Bot is not None else None

    async def send_card(
        self,
        image_bytes: bytes,
        full_name: str,
        alter_ego: str,
        correlation_id: Optional[str] = None,
    ) -> int:
        """Send a photocard with the Alter Ego caption format."""
        caption = self._format_caption(full_name=full_name)
        log_extra = {
            "full_name": full_name,
            "delivery_env": self.delivery_env,
            "chat_id": self.chat_id,
            "topic_id": self.topic_id,
        }
        if correlation_id:
            log_extra["correlation_id"] = correlation_id

        if self._bot is None:
            raise TelegramConfigError(
                message="python-telegram-bot is not installed; Telegram delivery is unavailable"
            )

        try:
            telegram_message = await self._send_photo_with_retry(
                image_bytes=image_bytes,
                caption=caption,
            )
            logger.info("Photocard sent successfully", extra=log_extra)
            return telegram_message.message_id
        except RetryAfter as exc:
            raise TelegramRateLimitError(
                retry_after=exc.retry_after,
                original_error=exc,
            ) from exc
        except (NetworkError, TimedOut) as exc:
            raise TelegramNetworkError(original_error=exc) from exc
        except TelegramAPIError as exc:
            if is_target_config_error_message(exc):
                raise TelegramConfigError(original_error=exc) from exc
            raise TelegramSendError(original_error=exc) from exc
        except RetryError as exc:
            last_exception = exc.last_attempt.exception()
            if last_exception and is_target_config_error_message(last_exception):
                raise TelegramConfigError(original_error=last_exception) from exc
            if isinstance(last_exception, (NetworkError, TimedOut)):
                raise TelegramNetworkError(original_error=last_exception) from exc
            raise TelegramSendError(original_error=exc) from exc
        except Exception as exc:
            logger.exception("Unexpected Telegram send error", extra=log_extra)
            if is_target_config_error_message(exc):
                raise TelegramConfigError(original_error=exc) from exc
            raise TelegramSendError(original_error=exc) from exc

    async def send_photocard(
        self,
        image_bytes: bytes,
        full_name: str,
        alter_ego: str,
        correlation_id: Optional[str] = None,
    ) -> int:
        """Backward-compatible alias for the MVP photocard send path."""
        return await self.send_card(
            image_bytes=image_bytes,
            full_name=full_name,
            alter_ego=alter_ego,
            correlation_id=correlation_id,
        )

    @retry(
        retry=retry_if_exception_type((NetworkError, TimedOut)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=RETRY_MIN_WAIT_SECONDS,
            max=RETRY_MAX_WAIT_SECONDS,
        ),
    )
    async def _send_photo_with_retry(self, image_bytes: bytes, caption: str):
        """Retry transient network failures while sending a photo."""
        photo = BytesIO(image_bytes)
        photo.name = "photocard.png"

        send_kwargs = {
            "chat_id": self.chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": ParseMode.HTML,
        }
        if self.topic_id:
            send_kwargs["message_thread_id"] = self.topic_id

        return await self._bot.send_photo(**send_kwargs)

    def _format_caption(self, full_name: str) -> str:
        """Build the Telegram caption as image plus name only."""
        return f"<b>Имя:</b> {escape_html(full_name)}"

    async def close(self) -> None:
        """Shutdown the Telegram bot client."""
        if self._bot:
            await self._bot.shutdown()
