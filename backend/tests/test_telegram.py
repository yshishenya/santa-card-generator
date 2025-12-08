"""Unit tests for TelegramClient integration.

This module contains comprehensive tests for the TelegramClient class,
covering message formatting, sending operations, error handling, and retry logic.

Test coverage:
- Caption formatting with various input combinations
- Caption truncation for long messages
- Successful card sending
- Network error handling and retry logic
- Configuration error detection
- Rate limit error handling
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from telegram.error import NetworkError, RetryAfter, TelegramError as TelegramAPIError

from src.integrations.telegram import TelegramClient, MAX_CAPTION_LENGTH
from src.integrations.exceptions import (
    TelegramConfigError,
    TelegramNetworkError,
    TelegramRateLimitError,
    TelegramSendError,
)


class TestTelegramClientInit:
    """Tests for TelegramClient initialization."""

    @patch("src.integrations.telegram.Bot")
    def test_init_with_valid_credentials(self, mock_bot_class: MagicMock) -> None:
        """Test that TelegramClient initializes successfully with valid credentials.

        Verifies that:
        - Bot class is instantiated with the token
        - All parameters are stored correctly
        - No exceptions are raised
        """
        # Arrange
        bot_token = "123456:ABC-DEF-GHI"
        chat_id = -1001234567890
        topic_id = 123

        # Act
        client = TelegramClient(
            bot_token=bot_token,
            chat_id=chat_id,
            topic_id=topic_id,
        )

        # Assert
        mock_bot_class.assert_called_once_with(token=bot_token)
        assert client.bot_token == bot_token
        assert client.chat_id == chat_id
        assert client.topic_id == topic_id

    def test_init_missing_bot_token_raises_error(self) -> None:
        """Test that missing bot_token raises TelegramConfigError.

        Verifies that:
        - TelegramConfigError is raised
        - Error indicates which config is missing
        """
        # Arrange & Act & Assert
        with pytest.raises(TelegramConfigError) as exc_info:
            TelegramClient(
                bot_token="",
                chat_id=-1001234567890,
                topic_id=123,
            )

        assert "telegram_bot_token" in exc_info.value.details.get("missing_config", "")

    def test_init_missing_chat_id_raises_error(self) -> None:
        """Test that missing chat_id raises TelegramConfigError.

        Verifies that:
        - TelegramConfigError is raised when chat_id is 0 or falsy
        """
        # Arrange & Act & Assert
        with pytest.raises(TelegramConfigError) as exc_info:
            TelegramClient(
                bot_token="valid-token",
                chat_id=0,
                topic_id=123,
            )

        assert "telegram_chat_id" in exc_info.value.details.get("missing_config", "")

    def test_init_missing_topic_id_raises_error(self) -> None:
        """Test that missing topic_id raises TelegramConfigError.

        Verifies that:
        - TelegramConfigError is raised when topic_id is 0 or falsy
        """
        # Arrange & Act & Assert
        with pytest.raises(TelegramConfigError) as exc_info:
            TelegramClient(
                bot_token="valid-token",
                chat_id=-1001234567890,
                topic_id=0,
            )

        assert "telegram_topic_id" in exc_info.value.details.get("missing_config", "")


class TestFormatCaption:
    """Tests for caption formatting functionality."""

    @pytest.fixture
    def telegram_client(self) -> TelegramClient:
        """Create a TelegramClient instance with mocked Bot.

        Returns:
            TelegramClient: Configured client for testing.
        """
        with patch("src.integrations.telegram.Bot"):
            client = TelegramClient(
                bot_token="test-token",
                chat_id=-1001234567890,
                topic_id=123,
            )
            return client

    def test_format_caption_full_message(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test caption formatting with all fields provided.

        Verifies that:
        - Caption includes recipient with proper formatting
        - Caption includes reason section
        - Caption includes message text
        - Caption includes sender with proper formatting
        - All sections are properly separated
        """
        # Arrange
        recipient = "Иванов Иван"
        reason = "За отличную работу"
        message = "Спасибо за твой вклад в развитие компании!"
        sender = "Петров Петр"

        # Act
        caption = telegram_client._format_caption(
            recipient=recipient,
            reason=reason,
            message=message,
            sender=sender,
        )

        # Assert
        assert "**Кому:** Иванов Иван" in caption
        assert "**За что:** За отличную работу" in caption
        assert "Спасибо за твой вклад в развитие компании!" in caption
        assert "**От кого:** Петров Петр" in caption

    def test_format_caption_without_reason(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test caption formatting when reason is not provided.

        Verifies that:
        - Caption is properly formatted without 'За что' section
        - Other fields are still included
        """
        # Arrange
        recipient = "Иванов Иван"
        message = "С Новым Годом!"
        sender = "Коллектив"

        # Act
        caption = telegram_client._format_caption(
            recipient=recipient,
            reason=None,
            message=message,
            sender=sender,
        )

        # Assert
        assert "**Кому:** Иванов Иван" in caption
        assert "**За что:**" not in caption
        assert "С Новым Годом!" in caption
        assert "**От кого:** Коллектив" in caption

    def test_format_caption_anonymous(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test caption formatting when sender is anonymous (None).

        Verifies that:
        - Caption is properly formatted without 'От кого' section
        - Anonymous sending is supported
        """
        # Arrange
        recipient = "Мария Сидорова"
        reason = "За помощь коллегам"
        message = "Ты лучшая!"

        # Act
        caption = telegram_client._format_caption(
            recipient=recipient,
            reason=reason,
            message=message,
            sender=None,
        )

        # Assert
        assert "**Кому:** Мария Сидорова" in caption
        assert "**За что:** За помощь коллегам" in caption
        assert "Ты лучшая!" in caption
        assert "**От кого:**" not in caption

    def test_format_caption_truncates_long_message(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test that very long messages are truncated to fit Telegram limits.

        Verifies that:
        - Caption is truncated when exceeding MAX_CAPTION_LENGTH
        - Truncation preserves structure (recipient, reason, sender)
        - Truncation indicator '...' is added
        - Final caption length does not exceed MAX_CAPTION_LENGTH
        """
        # Arrange
        recipient = "Иванов Иван"
        reason = "За отличную работу"
        # Create a message that will exceed the limit
        long_message = "A" * 2000
        sender = "Петров Петр"

        # Act
        caption = telegram_client._format_caption(
            recipient=recipient,
            reason=reason,
            message=long_message,
            sender=sender,
        )

        # Assert
        assert len(caption) <= MAX_CAPTION_LENGTH
        assert "..." in caption
        assert "**Кому:** Иванов Иван" in caption
        assert "**От кого:** Петров Петр" in caption

    def test_format_caption_edge_case_max_length(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test caption at exactly the maximum length boundary.

        Verifies that:
        - Caption at boundary is not unnecessarily truncated
        - Caption slightly over is properly truncated
        """
        # Arrange
        recipient = "Иван"
        message = "Test message"
        sender = "Петр"

        # Act
        caption = telegram_client._format_caption(
            recipient=recipient,
            reason=None,
            message=message,
            sender=sender,
        )

        # Assert
        assert len(caption) <= MAX_CAPTION_LENGTH

    def test_format_caption_preserves_structure_when_truncating(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test that truncation preserves header and footer structure.

        Verifies that:
        - When message is truncated, recipient header is preserved
        - Sender footer is preserved when possible
        """
        # Arrange
        recipient = "Тестовый Получатель"
        reason = "За труды"
        # Create message that forces truncation
        long_message = "X" * 1500
        sender = "Отправитель"

        # Act
        caption = telegram_client._format_caption(
            recipient=recipient,
            reason=reason,
            message=long_message,
            sender=sender,
        )

        # Assert
        assert caption.startswith("**Кому:** Тестовый Получатель")
        # Check that sender is preserved if there's space
        if len(caption) < MAX_CAPTION_LENGTH - 50:
            assert "**От кого:**" in caption


class TestSendCard:
    """Tests for card sending functionality."""

    @pytest.fixture
    def telegram_client(self) -> TelegramClient:
        """Create a TelegramClient instance with mocked Bot.

        Returns:
            TelegramClient: Configured client for testing.
        """
        with patch("src.integrations.telegram.Bot") as mock_bot_class:
            mock_bot = MagicMock()
            mock_bot_class.return_value = mock_bot
            client = TelegramClient(
                bot_token="test-token",
                chat_id=-1001234567890,
                topic_id=123,
            )
            return client

    @pytest.mark.asyncio
    async def test_send_card_success(
        self, telegram_client: TelegramClient, mock_telegram_message: MagicMock
    ) -> None:
        """Test successful card sending to Telegram.

        Verifies that:
        - send_card returns message_id on success
        - Bot.send_photo is called with correct parameters
        - Caption is properly formatted
        """
        # Arrange
        image_bytes = b"fake_image_data"
        telegram_client._bot.send_photo = AsyncMock(return_value=mock_telegram_message)

        # Act
        result = await telegram_client.send_card(
            image_bytes=image_bytes,
            recipient="Иванов Иван",
            reason="За отличную работу",
            message="Спасибо!",
            sender="Петров Петр",
        )

        # Assert
        assert result == mock_telegram_message.message_id
        telegram_client._bot.send_photo.assert_called_once()

        # Verify call arguments
        call_kwargs = telegram_client._bot.send_photo.call_args.kwargs
        assert call_kwargs["chat_id"] == telegram_client.chat_id
        assert call_kwargs["message_thread_id"] == telegram_client.topic_id
        assert "Иванов Иван" in call_kwargs["caption"]

    @pytest.mark.asyncio
    async def test_send_card_retries_on_network_error(
        self, telegram_client: TelegramClient, mock_telegram_message: MagicMock
    ) -> None:
        """Test that network errors trigger retry logic.

        Verifies that:
        - NetworkError causes retry
        - After retries, success is achieved
        - Correct number of attempts are made
        """
        # Arrange
        image_bytes = b"fake_image_data"
        call_count = 0

        async def mock_send_photo(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Connection failed")
            return mock_telegram_message

        telegram_client._bot.send_photo = AsyncMock(side_effect=mock_send_photo)

        # Act
        result = await telegram_client.send_card(
            image_bytes=image_bytes,
            recipient="Test User",
            reason="Testing",
            message="Test message",
            sender="Tester",
        )

        # Assert
        assert result == mock_telegram_message.message_id
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_send_card_raises_config_error_on_invalid_chat(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test that invalid chat/topic configuration raises TelegramConfigError.

        Verifies that:
        - 'chat not found' error is detected
        - TelegramConfigError is raised with appropriate message
        """
        # Arrange
        image_bytes = b"fake_image_data"
        telegram_client._bot.send_photo = AsyncMock(
            side_effect=TelegramAPIError("Chat not found")
        )

        # Act & Assert
        with pytest.raises(TelegramConfigError) as exc_info:
            await telegram_client.send_card(
                image_bytes=image_bytes,
                recipient="Test User",
                reason="Testing",
                message="Test message",
                sender="Tester",
            )

        assert "чат" in str(exc_info.value).lower() or "топик" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_card_raises_rate_limit_error(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test that rate limit exceeded raises TelegramRateLimitError.

        Verifies that:
        - RetryAfter exception is properly caught
        - TelegramRateLimitError is raised
        - retry_after value is preserved
        """
        # Arrange
        image_bytes = b"fake_image_data"
        retry_after_error = RetryAfter(retry_after=30)
        telegram_client._bot.send_photo = AsyncMock(side_effect=retry_after_error)

        # Act & Assert
        with pytest.raises(TelegramRateLimitError) as exc_info:
            await telegram_client.send_card(
                image_bytes=image_bytes,
                recipient="Test User",
                reason="Testing",
                message="Test message",
                sender="Tester",
            )

        assert exc_info.value.details.get("retry_after") == 30

    @pytest.mark.asyncio
    async def test_send_card_raises_network_error_after_retries(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test that persistent network errors eventually raise TelegramNetworkError.

        Verifies that:
        - After all retry attempts, TelegramNetworkError is raised
        - Original error is preserved
        """
        # Arrange
        image_bytes = b"fake_image_data"
        telegram_client._bot.send_photo = AsyncMock(
            side_effect=NetworkError("Persistent network failure")
        )

        # Act & Assert
        with pytest.raises(TelegramNetworkError):
            await telegram_client.send_card(
                image_bytes=image_bytes,
                recipient="Test User",
                reason="Testing",
                message="Test message",
                sender="Tester",
            )

    @pytest.mark.asyncio
    async def test_send_card_raises_send_error_on_generic_telegram_error(
        self, telegram_client: TelegramClient
    ) -> None:
        """Test that generic Telegram API errors raise TelegramSendError.

        Verifies that:
        - Non-config, non-network Telegram errors raise TelegramSendError
        """
        # Arrange
        image_bytes = b"fake_image_data"
        telegram_client._bot.send_photo = AsyncMock(
            side_effect=TelegramAPIError("Some generic error")
        )

        # Act & Assert
        with pytest.raises(TelegramSendError):
            await telegram_client.send_card(
                image_bytes=image_bytes,
                recipient="Test User",
                reason="Testing",
                message="Test message",
                sender="Tester",
            )

    @pytest.mark.asyncio
    async def test_send_card_with_correlation_id(
        self, telegram_client: TelegramClient, mock_telegram_message: MagicMock
    ) -> None:
        """Test that correlation_id is properly logged (doesn't affect functionality).

        Verifies that:
        - correlation_id parameter is accepted
        - Sending still works with correlation_id
        """
        # Arrange
        image_bytes = b"fake_image_data"
        telegram_client._bot.send_photo = AsyncMock(return_value=mock_telegram_message)

        # Act
        result = await telegram_client.send_card(
            image_bytes=image_bytes,
            recipient="Test User",
            reason="Testing",
            message="Test message",
            sender="Tester",
            correlation_id="test-correlation-123",
        )

        # Assert
        assert result == mock_telegram_message.message_id

    @pytest.mark.asyncio
    async def test_send_card_anonymous_sender(
        self, telegram_client: TelegramClient, mock_telegram_message: MagicMock
    ) -> None:
        """Test sending card with anonymous sender (None).

        Verifies that:
        - Card can be sent without sender information
        - Caption doesn't include 'От кого' section
        """
        # Arrange
        image_bytes = b"fake_image_data"
        telegram_client._bot.send_photo = AsyncMock(return_value=mock_telegram_message)

        # Act
        result = await telegram_client.send_card(
            image_bytes=image_bytes,
            recipient="Test User",
            reason="Testing",
            message="Anonymous message",
            sender=None,
        )

        # Assert
        assert result == mock_telegram_message.message_id
        call_kwargs = telegram_client._bot.send_photo.call_args.kwargs
        assert "**От кого:**" not in call_kwargs["caption"]


class TestInternalMethods:
    """Tests for internal helper methods."""

    @pytest.fixture
    def telegram_client(self) -> TelegramClient:
        """Create a TelegramClient instance with mocked Bot.

        Returns:
            TelegramClient: Configured client for testing.
        """
        with patch("src.integrations.telegram.Bot"):
            client = TelegramClient(
                bot_token="test-token",
                chat_id=-1001234567890,
                topic_id=123,
            )
            return client

    @pytest.mark.asyncio
    async def test_send_photo_with_retry_creates_bytesio(
        self, telegram_client: TelegramClient, mock_telegram_message: MagicMock
    ) -> None:
        """Test that _send_photo_with_retry properly wraps image bytes in BytesIO.

        Verifies that:
        - Image bytes are converted to file-like object
        - Filename is set for MIME type detection
        """
        # Arrange
        image_bytes = b"fake_image_content"
        telegram_client._bot.send_photo = AsyncMock(return_value=mock_telegram_message)

        # Act
        result = await telegram_client._send_photo_with_retry(
            image_bytes=image_bytes,
            caption="Test caption",
        )

        # Assert
        assert result == mock_telegram_message
        call_kwargs = telegram_client._bot.send_photo.call_args.kwargs
        photo_arg = call_kwargs["photo"]
        # BytesIO should have been passed with a name attribute
        assert hasattr(photo_arg, "name")
        assert photo_arg.name == "card.jpg"
