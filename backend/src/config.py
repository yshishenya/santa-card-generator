"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All sensitive data should be stored in .env file and never committed to version control.
    """

    # Gemini API configuration (via LiteLLM proxy)
    gemini_api_key: str
    gemini_base_url: str = "https://litellm.pro-4.ru/v1"
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini/gemini-2.5-flash-image-preview"

    # Telegram bot configuration
    telegram_bot_token: str
    telegram_chat_id: int
    telegram_topic_id: int

    # Application settings
    debug: bool = False
    log_level: str = "INFO"
    max_regenerations: int = 3
    employees_file_path: str = "/app/data/employees.json"

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()
