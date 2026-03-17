"""Application configuration settings."""

from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All sensitive data should be stored in .env file and never committed to version control.
    """

    # Gemini API configuration (via LiteLLM proxy)
    gemini_api_key: str
    gemini_base_url: str = "https://litellm.pro-4.ru/v1"
    gemini_text_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini/gemini-3.1-flash-image-preview"

    # Telegram bot configuration
    telegram_bot_token: str
    telegram_delivery_env: Literal["staging", "prod"] = "staging"
    telegram_staging_chat_id: Optional[int] = None
    telegram_staging_topic_id: Optional[int] = None
    telegram_prod_chat_id: Optional[int] = None
    telegram_prod_topic_id: Optional[int] = None
    telegram_chat_id: Optional[int] = None
    telegram_topic_id: Optional[int] = None

    # Application settings
    debug: bool = False
    log_level: str = "INFO"
    max_regenerations: int = 3
    session_ttl_minutes: int = 30
    employees_file_path: str = "/app/data/employees.json"

    # CORS configuration
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate limiting
    rate_limit_per_minute: int = 10  # Max requests per minute per IP

    # Authentication
    app_password: str = "Pr0ffes4.0"  # Password to access the application

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        case_sensitive = False

    @property
    def active_telegram_chat_id(self) -> int:
        """Resolve the active Telegram chat based on delivery environment."""
        if self.telegram_delivery_env == "staging":
            if self.telegram_staging_chat_id is None:
                raise ValueError(
                    "TELEGRAM_STAGING_CHAT_ID must be set when TELEGRAM_DELIVERY_ENV=staging"
                )
            return self.telegram_staging_chat_id

        if self.telegram_prod_chat_id is not None:
            return self.telegram_prod_chat_id
        if self.telegram_chat_id is not None:
            return self.telegram_chat_id
        raise ValueError(
            "TELEGRAM_PROD_CHAT_ID or legacy TELEGRAM_CHAT_ID must be set when "
            "TELEGRAM_DELIVERY_ENV=prod"
        )

    @property
    def active_telegram_topic_id(self) -> int:
        """Resolve the active Telegram topic based on delivery environment."""
        if self.telegram_delivery_env == "staging":
            if self.telegram_staging_topic_id is None:
                raise ValueError(
                    "TELEGRAM_STAGING_TOPIC_ID must be set when TELEGRAM_DELIVERY_ENV=staging"
                )
            return self.telegram_staging_topic_id

        if self.telegram_prod_topic_id is not None:
            return self.telegram_prod_topic_id
        if self.telegram_topic_id is not None:
            return self.telegram_topic_id
        raise ValueError(
            "TELEGRAM_PROD_TOPIC_ID or legacy TELEGRAM_TOPIC_ID must be set when "
            "TELEGRAM_DELIVERY_ENV=prod"
        )


settings = Settings()
