"""Pytest fixtures for Santa project tests.

This module provides reusable fixtures for testing the card generation service,
including mock clients, sample data, and test utilities.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.card import (
    CardGenerationRequest,
    ImageStyle,
    ImageVariant,
    TextStyle,
    TextVariant,
)
from src.models.employee import Employee


# ============================================================================
# Original Fixtures (preserved from existing conftest.py)
# ============================================================================


@pytest.fixture
def mock_gemini_response():
    """Create a mock Gemini API response object.

    Returns:
        MagicMock: Mocked response with text attribute.
    """
    response = MagicMock()
    response.text = "Generated test text content"
    return response


@pytest.fixture
def mock_telegram_message():
    """Create a mock Telegram message object.

    Returns:
        MagicMock: Mocked message with message_id attribute.
    """
    message = MagicMock()
    message.message_id = 12345
    return message


@pytest.fixture
def sample_employee_data():
    """Create sample employee data for testing.

    Returns:
        list: List of employee dictionaries.
    """
    return [
        {"id": "1", "name": "Ivanov Ivan Ivanovich", "department": "IT"},
        {"id": "2", "name": "Petrova Maria Sergeevna", "department": "HR"},
        {"id": "3", "name": "Sidorov Petr Alexandrovich", "department": "Sales"},
    ]


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

    Example:
        >>> async def test_example(mock_gemini_client):
        ...     text = await mock_gemini_client.generate_text(
        ...         employee_name="Test",
        ...         text_style="ode",
        ...         correlation_id="123"
        ...     )
        ...     assert "Test Employee" in text
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

    Example:
        >>> async def test_example(mock_telegram_client):
        ...     message_id = await mock_telegram_client.send_card(
        ...         employee_name="Test",
        ...         text="Hello",
        ...         image_bytes=b"...",
        ...         correlation_id="123"
        ...     )
        ...     assert message_id == 12345
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

    Example:
        >>> async def test_example(mock_employee_repo):
        ...     employee = await mock_employee_repo.get_by_name("Ivanov Ivan Ivanovich")
        ...     assert employee is not None
        ...     assert employee.id == "1"
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
# Sample CardGenerationRequest Fixture
# ============================================================================


@pytest.fixture
def sample_card_request() -> CardGenerationRequest:
    """Create a sample CardGenerationRequest for testing.

    Returns:
        CardGenerationRequest: A valid card generation request.

    Example:
        >>> def test_example(sample_card_request):
        ...     assert sample_card_request.employee_name == "Ivanov Ivan Ivanovich"
        ...     assert sample_card_request.text_style == TextStyle.ODE
    """
    return CardGenerationRequest(
        employee_name="Ivanov Ivan Ivanovich",
        text_style=TextStyle.ODE,
        image_style=ImageStyle.DIGITAL_ART,
    )


@pytest.fixture
def sample_card_request_haiku() -> CardGenerationRequest:
    """Create a sample CardGenerationRequest with haiku style.

    Returns:
        CardGenerationRequest: A valid card generation request with haiku style.
    """
    return CardGenerationRequest(
        employee_name="Petrova Maria Sergeevna",
        text_style=TextStyle.HAIKU,
        image_style=ImageStyle.PIXEL_ART,
    )


@pytest.fixture
def sample_card_request_unknown_employee() -> CardGenerationRequest:
    """Create a sample CardGenerationRequest for an unknown employee.

    Returns:
        CardGenerationRequest: A card request with non-existent employee name.
    """
    return CardGenerationRequest(
        employee_name="Unknown Person",
        text_style=TextStyle.STANDUP,
        image_style=ImageStyle.SPACE,
    )


# ============================================================================
# Sample Variant Fixtures
# ============================================================================


@pytest.fixture
def sample_text_variants() -> List[TextVariant]:
    """Create sample text variants for testing.

    Returns:
        List[TextVariant]: List of 3 text variants as expected by the service.
    """
    return [
        TextVariant(
            text="O, great Ivanov Ivan Ivanovich! Your contributions shine bright!",
            style=TextStyle.ODE,
        ),
        TextVariant(
            text="In the halls of our company, your name echoes with praise...",
            style=TextStyle.ODE,
        ),
        TextVariant(
            text="Noble colleague, accept our heartfelt gratitude for all you do!",
            style=TextStyle.ODE,
        ),
    ]


@pytest.fixture
def sample_image_variants() -> List[ImageVariant]:
    """Create sample image variants for testing.

    Returns:
        List[ImageVariant]: List of 3 image variants as expected by the service.
    """
    return [
        ImageVariant(
            url="generated://img-001",
            style=ImageStyle.DIGITAL_ART,
            prompt="Festive digital art winter scene",
        ),
        ImageVariant(
            url="generated://img-002",
            style=ImageStyle.DIGITAL_ART,
            prompt="Corporate holiday celebration artwork",
        ),
        ImageVariant(
            url="generated://img-003",
            style=ImageStyle.DIGITAL_ART,
            prompt="Winter wonderland greeting card design",
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
        datetime: A datetime object representing 1 hour ago.
    """
    return datetime.utcnow() - timedelta(hours=1)


@pytest.fixture
def future_datetime() -> datetime:
    """Create a datetime in the future (1 hour from now).

    Returns:
        datetime: A datetime object representing 1 hour from now.
    """
    return datetime.utcnow() + timedelta(hours=1)
