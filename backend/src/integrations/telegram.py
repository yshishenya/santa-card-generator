"""Telegram Bot API integration for sending greeting cards.

This module implements the TelegramClient class for sending generated greeting cards
to a Telegram chat/topic using the python-telegram-bot library.

The client handles:
- Sending photos with formatted captions
- Proper error handling and retry logic
- Message formatting according to specifications
- Caption truncation to fit Telegram limits

Usage:
    client = TelegramClient(
        bot_token="123456:ABC-DEF...",
        chat_id=-1001234567890,
        topic_id=123
    )

    message_id = await client.send_card(
        image_bytes=card_image,
        recipient="Иванов Иван",
        reason="За отличную работу",
        message="Спасибо за твой вклад!",
        sender="Петров Петр"
    )
"""

import logging
from io import BytesIO
from typing import Optional

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import (
    NetworkError,
    RetryAfter,
    TelegramError as TelegramAPIError,
    TimedOut,
)
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

# Telegram caption length limit
MAX_CAPTION_LENGTH = 1024


def escape_html(text: str) -> str:
    """Escape special characters for Telegram HTML mode.

    Args:
        text: Text to escape

    Returns:
        Text with escaped HTML special characters
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT_SECONDS = 2
RETRY_MAX_WAIT_SECONDS = 10


class TelegramClient:
    """Client for sending greeting cards to Telegram.

    This client handles all interactions with the Telegram Bot API,
    including message formatting, error handling, and retry logic.

    Attributes:
        bot_token: Telegram bot token from @BotFather
        chat_id: ID of the target chat (group/supergroup)
        topic_id: ID of the target topic/thread within the chat
    """

    def __init__(self, bot_token: str, chat_id: int, topic_id: int):
        """Initialize Telegram client with bot credentials and target chat.

        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: ID of the target chat (negative for groups/supergroups)
            topic_id: ID of the target topic/thread

        Raises:
            TelegramConfigError: If required configuration is missing or invalid
        """
        if not bot_token:
            raise TelegramConfigError(missing_config="telegram_bot_token")
        if not chat_id:
            raise TelegramConfigError(missing_config="telegram_chat_id")
        if topic_id is None:
            raise TelegramConfigError(missing_config="telegram_topic_id")

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.topic_id = topic_id

        # Initialize bot instance
        self._bot = Bot(token=self.bot_token)

        logger.info(
            "TelegramClient initialized",
            extra={
                "chat_id": self.chat_id,
                "topic_id": self.topic_id,
            },
        )

    async def send_card(
        self,
        image_bytes: bytes,
        recipient: str,
        reason: Optional[str],
        message: str,
        sender: Optional[str],
        correlation_id: Optional[str] = None,
        original_message: Optional[str] = None,
        recipient_telegram: Optional[str] = None,
    ) -> int:
        """Send greeting card to Telegram chat.

        Sends a photo with formatted caption to the configured Telegram chat/topic.
        Implements retry logic for transient errors.

        Args:
            image_bytes: Image data as bytes (JPEG/PNG)
            recipient: Name of the card recipient
            reason: Optional reason for gratitude
            message: The gratitude message text (or AI text if original_message provided)
            sender: Optional sender name (None for anonymous)
            correlation_id: Optional request tracking ID for logging
            original_message: Optional original user text to include alongside AI text
            recipient_telegram: Optional Telegram username (@user) or user ID for mention

        Returns:
            Telegram message ID of the sent message

        Raises:
            TelegramSendError: If sending fails after all retries
            TelegramNetworkError: If network connection fails
            TelegramRateLimitError: If rate limit is exceeded
            TelegramConfigError: If configuration is invalid (chat/topic not found)

        Example:
            >>> client = TelegramClient(token, chat_id, topic_id)
            >>> message_id = await client.send_card(
            ...     image_bytes=card_data,
            ...     recipient="Иванов Иван",
            ...     reason="За отличную работу",
            ...     message="Спасибо за твой вклад!",
            ...     sender="Петров Петр",
            ...     recipient_telegram="@ivanov"
            ... )
            >>> print(f"Sent: {message_id}")
        """
        caption = self._format_caption(
            recipient=recipient,
            reason=reason,
            message=message,
            sender=sender,
            original_message=original_message,
            recipient_telegram=recipient_telegram,
        )

        log_extra = {
            "recipient": recipient,
            "chat_id": self.chat_id,
            "topic_id": self.topic_id,
        }
        if correlation_id:
            log_extra["correlation_id"] = correlation_id

        logger.info("Sending card to Telegram", extra=log_extra)

        try:
            # Call internal retry-wrapped method
            telegram_message = await self._send_photo_with_retry(
                image_bytes=image_bytes,
                caption=caption,
            )

            message_id = telegram_message.message_id

            logger.info(
                "Card sent successfully to Telegram",
                extra={**log_extra, "message_id": message_id},
            )

            return message_id

        except RetryAfter as e:
            # Telegram rate limit exceeded
            logger.warning(
                f"Telegram rate limit exceeded: retry after {e.retry_after}s",
                extra=log_extra,
            )
            raise TelegramRateLimitError(
                retry_after=e.retry_after,
                original_error=e,
            )

        except (NetworkError, TimedOut) as e:
            # Network-level errors
            logger.error(
                f"Network error sending to Telegram: {e}",
                extra=log_extra,
                exc_info=True,
            )
            raise TelegramNetworkError(original_error=e)

        except TelegramAPIError as e:
            # Check if it's a configuration error (invalid chat/topic)
            error_message = str(e).lower()
            if any(
                keyword in error_message
                for keyword in [
                    "chat not found",
                    "chat_not_found",
                    "invalid chat",
                    "topic not found",
                    "thread not found",
                ]
            ):
                logger.error(
                    f"Telegram configuration error: {e}",
                    extra=log_extra,
                )
                raise TelegramConfigError(
                    message="Неверная конфигурация Telegram (чат или топик не найден)",
                    original_error=e,
                )

            # Generic Telegram API error
            logger.error(
                f"Telegram API error: {e}",
                extra=log_extra,
                exc_info=True,
            )
            raise TelegramSendError(original_error=e)

        except RetryError as e:
            # Tenacity raised this after retry attempts exhausted
            # Check if underlying error was a network error
            last_exception = e.last_attempt.exception()
            if isinstance(last_exception, (NetworkError, TimedOut)):
                logger.error(
                    f"Network error persisted after retries: {last_exception}",
                    extra=log_extra,
                    exc_info=True,
                )
                raise TelegramNetworkError(original_error=last_exception)

            # Non-network error after retries - raise as send error
            logger.error(
                f"Error after retries: {e}",
                extra=log_extra,
                exc_info=True,
            )
            raise TelegramSendError(
                message="Ошибка отправки после нескольких попыток",
                original_error=e,
            )

        except Exception as e:
            # Unexpected error
            logger.exception(
                f"Unexpected error sending to Telegram: {e}",
                extra=log_extra,
            )
            raise TelegramSendError(
                message="Непредвиденная ошибка при отправке в Telegram",
                original_error=e,
            )

    @retry(
        retry=retry_if_exception_type((NetworkError, TimedOut)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS),
    )
    async def _send_photo_with_retry(
        self,
        image_bytes: bytes,
        caption: str,
    ):
        """Send photo with automatic retry on network errors.

        This internal method wraps the actual Telegram API call with tenacity retry logic.
        It retries only on transient network errors (NetworkError, TimedOut).

        Args:
            image_bytes: Image data as bytes
            caption: Formatted caption text

        Returns:
            Telegram Message object

        Raises:
            NetworkError: If network connection fails (will be retried)
            TimedOut: If request times out (will be retried)
            TelegramAPIError: For other Telegram API errors (not retried)
        """
        # Convert bytes to file-like object for python-telegram-bot
        photo = BytesIO(image_bytes)
        photo.name = "card.jpg"  # Set filename for proper MIME type detection

        # Send photo to Telegram
        # topic_id=0 means send to main chat without thread
        send_kwargs = {
            "chat_id": self.chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": ParseMode.HTML,
        }
        if self.topic_id:
            send_kwargs["message_thread_id"] = self.topic_id

        result = await self._bot.send_photo(**send_kwargs)

        return result

    def _format_caption(
        self,
        recipient: str,
        reason: Optional[str],
        message: str,
        sender: Optional[str],
        original_message: Optional[str] = None,
        recipient_telegram: Optional[str] = None,
    ) -> str:
        """Format caption for Telegram message according to specification.

        Creates a structured caption using HTML formatting. If original_message is provided,
        shows both texts with labels "Слова благодарности" and "ИИ-креатив".

        Supports two mention formats:
        - @username: Direct mention (e.g., @ivanov)
        - Numeric ID: Text mention via tg://user?id= link

        Args:
            recipient: Name of the card recipient
            reason: Optional reason for gratitude
            message: The gratitude message text (AI text if original_message provided)
            sender: Optional sender name (None for anonymous)
            original_message: Optional original user text to show alongside AI text
            recipient_telegram: Optional Telegram username (@user) or user ID for mention

        Returns:
            Formatted caption string, truncated to MAX_CAPTION_LENGTH if necessary
        """
        # Build caption parts with optional telegram mention
        # Escape HTML special characters in user-provided content
        escaped_recipient = escape_html(recipient)

        # Format recipient with telegram mention
        if recipient_telegram:
            if recipient_telegram.startswith("@"):
                # @username format - use as-is (Telegram will recognize it)
                mention_text = f" ({recipient_telegram})"
            else:
                # Numeric ID - use tg://user?id= link for text mention
                mention_text = f' (<a href="tg://user?id={recipient_telegram}">написать</a>)'
        else:
            mention_text = ""

        parts = [f"<b>Кому:</b> {escaped_recipient}{mention_text}"]

        if reason:
            escaped_reason = escape_html(reason)
            parts.append(f"\n\n<b>За что:</b> {escaped_reason}")

        # Format message section based on whether we have both texts
        # Escape user-provided messages to prevent HTML parsing errors
        escaped_message = escape_html(message)
        if original_message:
            # Both original and AI text
            escaped_original = escape_html(original_message)
            parts.append(f"\n\n<b>Слова благодарности:</b>\n{escaped_original}")
            parts.append(f"\n\n<b>ИИ-креатив:</b>\n{escaped_message}")
        else:
            # Only one message (either original or AI)
            parts.append(f"\n\n{escaped_message}")

        if sender:
            escaped_sender = escape_html(sender)
            parts.append(f"\n\n<b>От кого:</b> {escaped_sender}")

        caption = "".join(parts)

        # Truncate if too long
        if len(caption) > MAX_CAPTION_LENGTH:
            # Calculate how much we can keep
            suffix = "..."
            available_length = MAX_CAPTION_LENGTH - len(suffix)

            # Try to keep the structure by truncating messages
            header = f"<b>Кому:</b> {escaped_recipient}{mention_text}"
            if reason:
                header += f"\n\n<b>За что:</b> {escaped_reason}"

            footer = ""
            if sender:
                footer = f"\n\n<b>От кого:</b> {escaped_sender}"

            # Calculate available space for messages
            fixed_parts_length = len(header) + len(footer) + 4
            messages_max_length = available_length - fixed_parts_length

            if original_message:
                # Split space between both messages
                half_length = messages_max_length // 2 - 30  # Account for labels
                if half_length > 20:
                    truncated_original = (
                        escape_html(original_message[:half_length]) + suffix
                        if len(original_message) > half_length
                        else escaped_original
                    )
                    truncated_ai = (
                        escape_html(message[:half_length]) + suffix
                        if len(message) > half_length
                        else escaped_message
                    )
                    caption = (
                        f"{header}\n\n"
                        f"<b>Слова благодарности:</b>\n{truncated_original}\n\n"
                        f"<b>ИИ-креатив:</b>\n{truncated_ai}"
                        f"{footer}"
                    )
                else:
                    caption = caption[:available_length] + suffix
            else:
                if messages_max_length > 10:
                    truncated_message = escape_html(message[:messages_max_length]) + suffix
                    caption = f"{header}\n\n{truncated_message}{footer}"
                else:
                    caption = caption[:available_length] + suffix

            logger.warning(
                f"Caption truncated from {len(''.join(parts))} to {len(caption)} characters",
                extra={"recipient": recipient},
            )

        return caption

    async def close(self) -> None:
        """Close the Telegram client and cleanup resources.

        Should be called during application shutdown to properly
        close the bot connection.
        """
        if self._bot:
            await self._bot.shutdown()
            logger.info("TelegramClient closed")
