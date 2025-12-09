"""Pytest fixtures for Santa project tests.

This module provides reusable fixtures for testing the card generation service,
including mock clients, sample data, and test utilities.

Updated for new multi-style generation architecture:
- 5 text variants (one per AI style)
- 4 image variants (one per style)
- Simplified CardGenerationRequest (no style selectors)
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.card import (
    AI_TEXT_STYLES,
    ALL_IMAGE_STYLES,
    CardGenerationRequest,
    ImageStyle,
    ImageVariant,
    TextStyle,
    TextVariant,
)
from src.models.employee import Employee


# ============================================================================
# Mock GeminiClient Fixture
# ============================================================================


@pytest.fixture
def mock_gemini_client() -> AsyncMock:
    """Create a mock GeminiClient for testing.

    The mock client provides async mocks for generate_text and generate_image
    methods that return predictable test data.

    Returns:
        AsyncMock: Mocked GeminiClient with pre-configured return values.
    """
    mock = AsyncMock()

    # Configure generate_text to return predictable text
    mock.generate_text = AsyncMock(
        return_value="Generated greeting text for Test Employee. "
        "Thank you for your contributions!"
    )

    # Configure generate_image to return tuple of (bytes, prompt)
    mock.generate_image = AsyncMock(
        return_value=(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00",  # Fake PNG header
            "A festive digital art greeting card",
        )
    )

    return mock


@pytest.fixture
def mock_gemini_client_with_errors() -> AsyncMock:
    """Create a mock GeminiClient that raises errors.

    Useful for testing error handling scenarios.

    Returns:
        AsyncMock: Mocked GeminiClient configured to raise exceptions.
    """
    mock = AsyncMock()

    mock.generate_text = AsyncMock(side_effect=Exception("API Error"))
    mock.generate_image = AsyncMock(side_effect=Exception("Image generation failed"))

    return mock


# ============================================================================
# Mock TelegramClient Fixture
# ============================================================================


@pytest.fixture
def mock_telegram_client() -> AsyncMock:
    """Create a mock TelegramClient for testing.

    The mock client provides an async mock for send_card method
    that returns a predictable message ID.

    Returns:
        AsyncMock: Mocked TelegramClient with pre-configured return values.
    """
    mock = AsyncMock()

    # Configure send_card to return a predictable message ID
    mock.send_card = AsyncMock(return_value=12345)

    return mock


@pytest.fixture
def mock_telegram_client_with_error() -> AsyncMock:
    """Create a mock TelegramClient that raises errors.

    Useful for testing error handling scenarios when Telegram fails.

    Returns:
        AsyncMock: Mocked TelegramClient configured to raise exceptions.
    """
    mock = AsyncMock()

    mock.send_card = AsyncMock(side_effect=Exception("Telegram API Error"))

    return mock


# ============================================================================
# Mock EmployeeRepository Fixture
# ============================================================================


@pytest.fixture
def sample_employees() -> List[Employee]:
    """Create a list of sample employees for testing.

    Returns:
        List[Employee]: List of test employees.
    """
    return [
        Employee(id="1", name="Ivanov Ivan Ivanovich", department="IT"),
        Employee(id="2", name="Petrova Maria Sergeevna", department="HR"),
        Employee(id="3", name="Sidorov Alexey Petrovich", department="Finance"),
        Employee(id="4", name="Kozlova Anna Dmitrievna", department="Marketing"),
        Employee(id="5", name="Smirnov Dmitry Alexandrovich", department=None),
    ]


@pytest.fixture
def mock_employee_repo(sample_employees: List[Employee]) -> AsyncMock:
    """Create a mock EmployeeRepository for testing.

    The mock repository provides async mocks for get_all and get_by_name
    methods that return sample employee data.

    Args:
        sample_employees: List of sample employees to use in the mock.

    Returns:
        AsyncMock: Mocked EmployeeRepository with pre-configured return values.
    """
    mock = AsyncMock()

    # Configure get_all to return all sample employees
    mock.get_all = AsyncMock(return_value=sample_employees)

    # Configure get_by_name to search through sample employees
    async def get_by_name_impl(name: str) -> Optional[Employee]:
        name_lower = name.lower().strip()
        for employee in sample_employees:
            if employee.name.lower().strip() == name_lower:
                return employee
        return None

    mock.get_by_name = AsyncMock(side_effect=get_by_name_impl)

    return mock


@pytest.fixture
def mock_employee_repo_empty() -> AsyncMock:
    """Create a mock EmployeeRepository with no employees.

    Useful for testing scenarios where no employees exist.

    Returns:
        AsyncMock: Mocked EmployeeRepository with empty data.
    """
    mock = AsyncMock()

    mock.get_all = AsyncMock(return_value=[])
    mock.get_by_name = AsyncMock(return_value=None)

    return mock


# ============================================================================
# Sample CardGenerationRequest Fixtures (NEW architecture)
# ============================================================================


@pytest.fixture
def sample_card_request() -> CardGenerationRequest:
    """Create a sample CardGenerationRequest for testing.

    NEW architecture: no style selectors, all styles generated automatically.

    Returns:
        CardGenerationRequest: A valid card generation request.
    """
    return CardGenerationRequest(
        recipient="Ivanov Ivan Ivanovich",
        sender="HR Team",
        reason="Outstanding performance",
        message="Thank you for your hard work!",
    )


@pytest.fixture
def sample_card_request_minimal() -> CardGenerationRequest:
    """Create a minimal CardGenerationRequest with only required field.

    Returns:
        CardGenerationRequest: A minimal card request with only recipient.
    """
    return CardGenerationRequest(
        recipient="Petrova Maria Sergeevna",
    )


@pytest.fixture
def sample_card_request_unknown_employee() -> CardGenerationRequest:
    """Create a sample CardGenerationRequest for an unknown employee.

    Returns:
        CardGenerationRequest: A card request with non-existent employee name.
    """
    return CardGenerationRequest(
        recipient="Unknown Person",
    )


# ============================================================================
# Sample Variant Fixtures (NEW architecture - 5 text, 4 image)
# ============================================================================


@pytest.fixture
def sample_text_variants() -> List[TextVariant]:
    """Create sample text variants for testing.

    NEW architecture: 5 variants, one per AI style.

    Returns:
        List[TextVariant]: List of 5 text variants (one per style).
    """
    return [
        TextVariant(
            text="O, great Ivanov Ivan Ivanovich! Your contributions shine bright!",
            style=TextStyle.ODE,
        ),
        TextVariant(
            text="Winter snow falls\nIvanov brings the joy\nSuccess blooms bright",
            style=TextStyle.HAIKU,
        ),
        TextVariant(
            text="BREAKING: Employee Ivanov achieves outstanding results!",
            style=TextStyle.NEWSPAPER,
        ),
        TextVariant(
            text="Report from 2074: Ivanov's legacy still inspires generations...",
            style=TextStyle.FUTURE,
        ),
        TextVariant(
            text="So, Ivanov walks into the office... and productivity goes up 200%!",
            style=TextStyle.STANDUP,
        ),
    ]


@pytest.fixture
def sample_image_variants() -> List[ImageVariant]:
    """Create sample image variants for testing.

    NEW architecture: 4 variants, one per image style.

    Returns:
        List[ImageVariant]: List of 4 image variants (one per style).
    """
    return [
        ImageVariant(
            url="generated://img-001",
            style=ImageStyle.DIGITAL_ART,
            prompt="Festive digital art winter scene",
        ),
        ImageVariant(
            url="generated://img-002",
            style=ImageStyle.SPACE,
            prompt="Cosmic celebration among stars",
        ),
        ImageVariant(
            url="generated://img-003",
            style=ImageStyle.PIXEL_ART,
            prompt="Retro pixel art holiday greeting",
        ),
        ImageVariant(
            url="generated://img-004",
            style=ImageStyle.MOVIE,
            prompt="Cinematic movie poster greeting",
        ),
    ]


@pytest.fixture
def sample_image_data(sample_image_variants: List[ImageVariant]) -> Dict[str, bytes]:
    """Create sample image data dictionary for testing.

    Maps image variant URLs to fake image bytes.

    Args:
        sample_image_variants: List of image variants to create data for.

    Returns:
        Dict[str, bytes]: Dictionary mapping URLs to image bytes.
    """
    return {
        variant.url: f"fake_image_bytes_{i}".encode()
        for i, variant in enumerate(sample_image_variants)
    }


# ============================================================================
# Sample Employee Data Fixture
# ============================================================================


@pytest.fixture
def sample_employee() -> Employee:
    """Create a single sample employee for testing.

    Returns:
        Employee: A test employee instance.
    """
    return Employee(
        id="1",
        name="Ivanov Ivan Ivanovich",
        department="IT",
    )


@pytest.fixture
def sample_employee_no_department() -> Employee:
    """Create a sample employee without a department.

    Returns:
        Employee: A test employee instance without department.
    """
    return Employee(
        id="5",
        name="Smirnov Dmitry Alexandrovich",
        department=None,
    )


# ============================================================================
# Time-related Fixtures
# ============================================================================


@pytest.fixture
def past_datetime() -> datetime:
    """Create a datetime in the past (1 hour ago).

    Returns:
        datetime: A timezone-aware datetime object representing 1 hour ago.
    """
    return datetime.now(timezone.utc) - timedelta(hours=1)


@pytest.fixture
def future_datetime() -> datetime:
    """Create a datetime in the future (1 hour from now).

    Returns:
        datetime: A timezone-aware datetime object representing 1 hour from now.
    """
    return datetime.now(timezone.utc) + timedelta(hours=1)


# ============================================================================
# Sample Employee Data Fixture (for test_employee_repo.py)
# ============================================================================


@pytest.fixture
def sample_employee_data() -> List[Dict[str, Any]]:
    """Create sample employee data as raw dictionaries.

    Used for testing EmployeeRepository file loading.

    Returns:
        List[Dict[str, Any]]: List of employee dictionaries.
    """
    return [
        {"id": "1", "name": "Ivanov Ivan Ivanovich", "department": "IT"},
        {"id": "2", "name": "Petrova Maria Sergeevna", "department": "HR"},
        {"id": "3", "name": "Sidorov Alexey Petrovich", "department": "Finance"},
    ]


# ============================================================================
# Mock Telegram Message Fixture (for test_telegram.py)
# ============================================================================


@pytest.fixture
def mock_telegram_message() -> MagicMock:
    """Create a mock Telegram Message object.

    Returns:
        MagicMock: Mocked Telegram Message with message_id.
    """
    mock_message = MagicMock()
    mock_message.message_id = 12345
    return mock_message
