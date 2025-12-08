"""External integrations package.

This package contains clients and adapters for external services:
- Gemini AI API for text and image generation
- Telegram Bot API for sending cards

All integrations must:
- Use async/await for I/O operations
- Include proper error handling and retry mechanisms
- Have clear Pydantic models for request/response
- Log all requests for debugging
"""

from .gemini import GeminiClient
from .telegram import TelegramClient
from .exceptions import (
    GeminiError,
    GeminiTextGenerationError,
    GeminiImageGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
    TelegramError,
    TelegramSendError,
    TelegramConfigError,
    TelegramNetworkError,
    TelegramRateLimitError,
)

__all__ = [
    "GeminiClient",
    "TelegramClient",
    "GeminiError",
    "GeminiTextGenerationError",
    "GeminiImageGenerationError",
    "GeminiRateLimitError",
    "GeminiConfigError",
    "TelegramError",
    "TelegramSendError",
    "TelegramConfigError",
    "TelegramNetworkError",
    "TelegramRateLimitError",
]
