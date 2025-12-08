"""Custom exceptions for external integrations.

This module defines the exception hierarchy for all external API integrations
(Gemini, Telegram). All exceptions inherit from a base class for consistent handling.
"""

from typing import Optional, Dict, Any


class GeminiError(Exception):
    """Base exception for all Gemini API-related errors.

    Attributes:
        message: Human-readable error message
        details: Additional error context
        original_error: Original exception that caused this error
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize GeminiError.

        Args:
            message: Error description
            details: Additional context information
            original_error: Underlying exception if available
        """
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.original_error:
            return f"{self.message} (caused by: {self.original_error})"
        return self.message


class GeminiTextGenerationError(GeminiError):
    """Raised when text generation fails.

    This error occurs when the Gemini API cannot generate text content,
    either due to API errors, content filtering, or rate limits.
    """

    def __init__(
        self,
        message: str = "Ошибка генерации текста. Попробуйте еще раз",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize GeminiTextGenerationError.

        Args:
            message: Error description
            details: Additional context (style, prompt info)
            original_error: Underlying exception
        """
        super().__init__(message, details, original_error)


class GeminiImageGenerationError(GeminiError):
    """Raised when image generation fails.

    This error occurs when the Gemini API cannot generate images,
    either due to API errors, content policy violations, or rate limits.
    """

    def __init__(
        self,
        message: str = "Ошибка генерации изображения. Попробуйте еще раз",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize GeminiImageGenerationError.

        Args:
            message: Error description
            details: Additional context (style, prompt info)
            original_error: Underlying exception
        """
        super().__init__(message, details, original_error)


class GeminiRateLimitError(GeminiError):
    """Raised when Gemini API rate limit is exceeded.

    This error occurs when too many requests are made to the API
    in a short period. Client should implement exponential backoff.
    """

    def __init__(
        self,
        message: str = "Превышен лимит запросов к API. Попробуйте позже",
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize GeminiRateLimitError.

        Args:
            message: Error description
            retry_after: Seconds to wait before retrying
            original_error: Underlying exception
        """
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, details, original_error)


class GeminiConfigError(GeminiError):
    """Raised when Gemini client configuration is invalid.

    This error occurs during client initialization if required
    configuration (API key, model name) is missing or invalid.
    """

    def __init__(
        self,
        message: str = "Неверная конфигурация Gemini API",
        missing_param: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize GeminiConfigError.

        Args:
            message: Error description
            missing_param: Name of missing configuration parameter
            original_error: Underlying exception
        """
        details = {"missing_param": missing_param} if missing_param else {}
        super().__init__(message, details, original_error)


# ============================================================================
# Telegram Integration Errors
# ============================================================================


class TelegramError(Exception):
    """Base exception for all Telegram-related errors.

    This is the parent class for all Telegram Bot API integration errors.

    Attributes:
        message: Human-readable error message
        details: Additional error context
        original_error: Original exception that caused this error
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize TelegramError.

        Args:
            message: Error description
            details: Additional context information
            original_error: Underlying exception if available
        """
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.original_error:
            return f"{self.message} (caused by: {self.original_error})"
        return self.message


class TelegramSendError(TelegramError):
    """Raised when sending message to Telegram fails.

    This error occurs when the actual message sending operation fails
    due to network issues, API errors, or other transient problems.
    This error should be retried with exponential backoff.
    """

    def __init__(
        self,
        message: str = "Не удалось отправить открытку в Telegram. Попробуйте позже",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize TelegramSendError.

        Args:
            message: Error description
            details: Additional context (recipient, message_id)
            original_error: Underlying exception
        """
        super().__init__(message, details, original_error)


class TelegramConfigError(TelegramError):
    """Raised when Telegram is not configured properly.

    This error occurs when required configuration parameters
    (bot token, chat ID, topic ID) are missing or invalid.
    This is a permanent error that should not be retried.
    """

    def __init__(
        self,
        message: str = "Telegram не настроен. Обратитесь к администратору",
        missing_config: Optional[str] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize TelegramConfigError.

        Args:
            message: Error description
            missing_config: Name of the missing configuration parameter
            original_error: Underlying exception
        """
        details = {"missing_config": missing_config} if missing_config else {}
        super().__init__(message, details, original_error)


class TelegramNetworkError(TelegramError):
    """Raised when network connection to Telegram fails.

    This error occurs for network-level issues like timeouts,
    connection refused, DNS errors, etc.
    This is a transient error that should be retried with exponential backoff.
    """

    def __init__(
        self,
        message: str = "Ошибка сети при отправке в Telegram. Повторяем попытку...",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize TelegramNetworkError.

        Args:
            message: Error description
            details: Additional context
            original_error: Underlying exception
        """
        super().__init__(message, details, original_error)


class TelegramRateLimitError(TelegramError):
    """Raised when Telegram API rate limit is exceeded.

    This error occurs when Telegram API returns 429 Too Many Requests.
    This error should be retried after a longer delay (exponential backoff).
    """

    def __init__(
        self,
        message: str = "Превышен лимит запросов к Telegram",
        retry_after: Optional[int] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize TelegramRateLimitError.

        Args:
            message: Error description
            retry_after: Number of seconds to wait before retrying (from Telegram API)
            original_error: Underlying exception
        """
        if retry_after:
            message += f". Повторите попытку через {retry_after} секунд"

        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, details, original_error)
