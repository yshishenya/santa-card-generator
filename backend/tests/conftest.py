"""Shared pytest fixtures for backend tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import settings
from src.models.card import ImageStyle
from src.models.photocard import (
    PhotocardGenerateRequest,
    PhotocardGenerateResponse,
    PhotocardImageVariant,
    PhotocardSendResponse,
)


@pytest.fixture(scope="session", autouse=True)
def configure_settings_for_tests():
    """Set test-friendly settings overrides for the duration of the session."""
    original_values = {
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "telegram_delivery_env": settings.telegram_delivery_env,
        "telegram_staging_chat_id": settings.telegram_staging_chat_id,
        "telegram_staging_topic_id": settings.telegram_staging_topic_id,
        "telegram_prod_chat_id": settings.telegram_prod_chat_id,
        "telegram_prod_topic_id": settings.telegram_prod_topic_id,
        "telegram_chat_id": settings.telegram_chat_id,
        "telegram_topic_id": settings.telegram_topic_id,
        "print_archive_storage_path": settings.print_archive_storage_path,
        "print_archive_password": settings.print_archive_password,
        "tap_p40_leaderboard_path": settings.tap_p40_leaderboard_path,
    }

    object.__setattr__(settings, "rate_limit_per_minute", 10000)
    object.__setattr__(settings, "telegram_delivery_env", "staging")
    object.__setattr__(settings, "telegram_staging_chat_id", -1001234567890)
    object.__setattr__(settings, "telegram_staging_topic_id", 123)
    object.__setattr__(settings, "telegram_prod_chat_id", -1009876543210)
    object.__setattr__(settings, "telegram_prod_topic_id", 456)
    object.__setattr__(settings, "telegram_chat_id", -1009876543210)
    object.__setattr__(settings, "telegram_topic_id", 456)
    object.__setattr__(settings, "print_archive_storage_path", "/tmp/cards-test-print-archive")
    object.__setattr__(settings, "print_archive_password", "Pr0ffes4.0Pr0ffes4.0")
    object.__setattr__(settings, "tap_p40_leaderboard_path", "/tmp/cards-test-tap-p40.json")

    yield

    for key, value in original_values.items():
        object.__setattr__(settings, key, value)


@pytest.fixture
def sample_photocard_request() -> PhotocardGenerateRequest:
    """Create a sample photocard generation request."""
    return PhotocardGenerateRequest(
        full_name="Jane Frost",
        alter_ego="Cyberpunk snow captain",
    )


@pytest.fixture
def sample_image_variants() -> list[PhotocardImageVariant]:
    """Create three generated image variants."""
    return [
        PhotocardImageVariant(
            url="generated://image-001",
            style=ImageStyle.CYBERPUNK,
        ),
        PhotocardImageVariant(
            url="generated://image-002",
            style=ImageStyle.HYPERREALISM,
        ),
        PhotocardImageVariant(
            url="generated://image-003",
            style=ImageStyle.FANTASY,
        ),
    ]


@pytest.fixture
def sample_image_data(sample_image_variants: list[PhotocardImageVariant]) -> dict[str, bytes]:
    """Create fake PNG bytes for the sample variants."""
    return {
        variant.url: f"png-{index}".encode("utf-8")
        for index, variant in enumerate(sample_image_variants, start=1)
    }


@pytest.fixture
def sample_generate_response(
    sample_image_variants: list[PhotocardImageVariant],
) -> PhotocardGenerateResponse:
    """Create a sample generate response."""
    return PhotocardGenerateResponse(
        session_id="test-session-123",
        image_variants=sample_image_variants,
    )


@pytest.fixture
def sample_send_response() -> PhotocardSendResponse:
    """Create a sample send response."""
    return PhotocardSendResponse(
        success=True,
        message="Photocard sent successfully",
        telegram_message_id=12345,
        delivery_env="staging",
    )


@pytest.fixture
def mock_gemini_client() -> AsyncMock:
    """Create a mock Gemini client for service tests."""
    client = AsyncMock()
    client.generate_image_direct = AsyncMock(
        return_value=(b"\x89PNGtest-image", "prompt"),
    )
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_telegram_client() -> AsyncMock:
    """Create a mock Telegram client for service tests."""
    client = AsyncMock()
    client.delivery_env = "staging"
    client.send_photocard = AsyncMock(return_value=12345)
    client.send_card = AsyncMock(return_value=12345)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_print_archive_store() -> MagicMock:
    """Create a mock print archive store for service tests."""
    store = MagicMock()
    store.save_asset = MagicMock()
    store.list_assets = MagicMock(return_value=[])
    store.get_asset = MagicMock(return_value=None)
    store.get_asset_file_path = MagicMock(return_value=None)
    store.build_zip_bytes = MagicMock(return_value=b"PK\x03\x04")
    return store


@pytest.fixture
def mock_telegram_message() -> MagicMock:
    """Create a mock Telegram API message."""
    message = MagicMock()
    message.message_id = 12345
    return message


@pytest.fixture
def sample_employee_data() -> list[dict]:
    """Create employee data used by employee repository tests."""
    return [
        {
            "id": "1",
            "name": "John Doe",
            "department": "Engineering",
            "telegram": "@john_doe",
        },
        {
            "id": "2",
            "name": "Jane Smith",
            "department": "Marketing",
            "telegram": "@jane_smith",
        },
    ]
