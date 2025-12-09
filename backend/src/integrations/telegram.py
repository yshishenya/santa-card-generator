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
            ...     sender="Петров Петр"
            ... )
            >>> print(f"Sent: {message_id}")
        """
        caption = self._format_caption(
            recipient=recipient,
            reason=reason,
            message=message,
            sender=sender,
            original_message=original_message,
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
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
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
            "parse_mode": ParseMode.MARKDOWN,
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
    ) -> str:
        # Build caption parts
        """Format caption for Telegram message according to specification.
        
        This function creates a structured caption for a Telegram message,
        incorporating various elements such as the recipient's name, a reason for
        gratitude, and the message text. If an original_message is provided, it
        displays both the original and AI-generated texts with appropriate labels. The
        caption is truncated to MAX_CAPTION_LENGTH if necessary, ensuring that the
        essential information is preserved.
        
        Args:
            recipient (str): Name of the card recipient.
            reason (Optional[str]): Optional reason for gratitude.
            message (str): The gratitude message text (AI text if original_message provided).
            sender (Optional[str]): Optional sender name (None for anonymous).
            original_message (Optional[str]): Optional original user text to show alongside AI text.
        
        Returns:
            str: Formatted caption string, truncated to MAX_CAPTION_LENGTH if necessary.
        """
        parts = [f"**Кому:** {recipient}"]

        if reason:
            parts.append(f"\n\n**За что:** {reason}")

        # Format message section based on whether we have both texts
        if original_message:
            # Both original and AI text
            parts.append(f"\n\n**Слова благодарности:**\n{original_message}")
            parts.append(f"\n\n**ИИ-креатив:**\n{message}")
        else:
            # Only one message (either original or AI)
            parts.append(f"\n\n{message}")

        if sender:
            parts.append(f"\n\n**От кого:** {sender}")

        caption = "".join(parts)

        # Truncate if too long
        if len(caption) > MAX_CAPTION_LENGTH:
            # Calculate how much we can keep
            suffix = "..."
            available_length = MAX_CAPTION_LENGTH - len(suffix)

            # Try to keep the structure by truncating messages
            header = f"**Кому:** {recipient}"
            if reason:
                header += f"\n\n**За что:** {reason}"

            footer = ""
            if sender:
                footer = f"\n\n**От кого:** {sender}"

            # Calculate available space for messages
            fixed_parts_length = len(header) + len(footer) + 4
            messages_max_length = available_length - fixed_parts_length

            if original_message:
                # Split space between both messages
                half_length = messages_max_length // 2 - 30  # Account for labels
                if half_length > 20:
                    truncated_original = (
                        original_message[:half_length] + suffix
                        if len(original_message) > half_length
                        else original_message
                    )
                    truncated_ai = (
                        message[:half_length] + suffix
                        if len(message) > half_length
                        else message
                    )
                    caption = (
                        f"{header}\n\n"
                        f"**Слова благодарности:**\n{truncated_original}\n\n"
                        f"**ИИ-креатив:**\n{truncated_ai}"
                        f"{footer}"
                    )
                else:
                    caption = caption[:available_length] + suffix
            else:
                if messages_max_length > 10:
                    truncated_message = message[:messages_max_length] + suffix
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
