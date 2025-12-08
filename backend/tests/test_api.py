"""Integration tests for Santa API endpoints.

This module contains comprehensive integration tests for all API endpoints,
using FastAPI TestClient with mocked CardService for controlled testing.
"""

import pytest
from typing import AsyncGenerator, List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.main import app
from src.api.dependencies import get_card_service
from src.core import CardService, SessionManager
from src.core.exceptions import (
    RecipientNotFoundError,
    RegenerationLimitExceededError,
    SessionExpiredError,
    SessionNotFoundError,
    VariantNotFoundError,
)
from src.models import (
    CardGenerationRequest,
    CardGenerationResponse,
    Employee,
    ImageStyle,
    ImageVariant,
    SendCardResponse,
    TextStyle,
    TextVariant,
)
from src.models.response import RegenerateResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_card_service() -> MagicMock:
    """Create a mock CardService for testing.

    Returns:
        MagicMock instance mimicking CardService behavior.
    """
    service = MagicMock(spec=CardService)

    # Create a mock session manager
    session_manager = MagicMock(spec=SessionManager)
    service._session_manager = session_manager

    return service


@pytest.fixture
def client(mock_card_service: MagicMock) -> TestClient:
    """Create a TestClient with mocked CardService.

    Args:
        mock_card_service: Mocked CardService instance.

    Returns:
        TestClient configured with dependency override.
    """
    def override_get_card_service() -> MagicMock:
        return mock_card_service

    app.dependency_overrides[get_card_service] = override_get_card_service

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def sample_text_variants() -> List[TextVariant]:
    """Create sample text variants for testing.

    Returns:
        List of 3 TextVariant objects.
    """
    return [
        TextVariant(text="Happy New Year! May success follow you.", style=TextStyle.ODE),
        TextVariant(text="Wishing you joy and prosperity in 2024!", style=TextStyle.ODE),
        TextVariant(text="Best wishes for a wonderful year ahead!", style=TextStyle.ODE),
    ]


@pytest.fixture
def sample_image_variants() -> List[ImageVariant]:
    """Create sample image variants for testing.

    Returns:
        List of 3 ImageVariant objects.
    """
    return [
        ImageVariant(
            url="generated://image-001",
            style=ImageStyle.DIGITAL_ART,
            prompt="A festive digital art greeting"
        ),
        ImageVariant(
            url="generated://image-002",
            style=ImageStyle.DIGITAL_ART,
            prompt="Digital painting celebration"
        ),
        ImageVariant(
            url="generated://image-003",
            style=ImageStyle.DIGITAL_ART,
            prompt="Colorful digital artwork"
        ),
    ]


@pytest.fixture
def sample_generation_response(
    sample_text_variants: List[TextVariant],
    sample_image_variants: List[ImageVariant],
) -> CardGenerationResponse:
    """Create a sample card generation response.

    Args:
        sample_text_variants: List of text variants.
        sample_image_variants: List of image variants.

    Returns:
        CardGenerationResponse object.
    """
    return CardGenerationResponse(
        session_id="test-session-123",
        employee_name="John Doe",
        text_variants=sample_text_variants,
        image_variants=sample_image_variants,
    )


@pytest.fixture
def sample_employees() -> List[Employee]:
    """Create sample employee list for testing.

    Returns:
        List of Employee objects.
    """
    return [
        Employee(id="1", name="John Doe", department="Engineering"),
        Employee(id="2", name="Jane Smith", department="Marketing"),
        Employee(id="3", name="Bob Wilson", department="HR"),
    ]


# ---------------------------------------------------------------------------
# Health Check Tests
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for the /health endpoint."""

    def test_health_check_returns_ok(self, client: TestClient) -> None:
        """Test that health check returns status healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "santa-api"
        assert data["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Employees Endpoint Tests
# ---------------------------------------------------------------------------


class TestEmployeesEndpoint:
    """Tests for the /api/v1/employees endpoint."""

    def test_get_employees_returns_list(
        self,
        client: TestClient,
        sample_employees: List[Employee],
    ) -> None:
        """Test that GET /employees returns a list of employees."""
        with patch(
            "src.api.employees.employee_repo.get_all",
            new_callable=AsyncMock,
            return_value=sample_employees,
        ):
            response = client.get("/api/v1/employees")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

        # Verify employee structure
        assert data[0]["id"] == "1"
        assert data[0]["name"] == "John Doe"
        assert data[0]["department"] == "Engineering"

    def test_get_employees_empty_list(self, client: TestClient) -> None:
        """Test that GET /employees returns empty list when no employees."""
        with patch(
            "src.api.employees.employee_repo.get_all",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = client.get("/api/v1/employees")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 0


# ---------------------------------------------------------------------------
# Cards Generation Endpoint Tests
# ---------------------------------------------------------------------------


class TestCardsGenerationEndpoint:
    """Tests for the POST /api/v1/cards/generate endpoint."""

    def test_generate_card_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test successful card generation."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "employee_name": "John Doe",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["error"] is None
        assert data["data"]["session_id"] == "test-session-123"
        assert data["data"]["employee_name"] == "John Doe"
        assert len(data["data"]["text_variants"]) == 3
        assert len(data["data"]["image_variants"]) == 3

        # Verify text variant structure
        text_variant = data["data"]["text_variants"][0]
        assert "text" in text_variant
        assert "style" in text_variant

        # Verify image variant structure
        image_variant = data["data"]["image_variants"][0]
        assert "url" in image_variant
        assert "style" in image_variant
        assert "prompt" in image_variant

    def test_generate_card_missing_recipient(self, client: TestClient) -> None:
        """Test card generation fails with missing employee_name."""
        request_data = {
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_generate_card_missing_image_style(self, client: TestClient) -> None:
        """Test card generation fails with missing image_style."""
        request_data = {
            "employee_name": "John Doe",
            "text_style": "ode",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_generate_card_invalid_recipient(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test card generation returns 404 for unknown employee."""
        mock_card_service.generate_card = AsyncMock(
            side_effect=RecipientNotFoundError("Unknown Employee")
        )

        request_data = {
            "employee_name": "Unknown Employee",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "Employee not found" in data["detail"]

    def test_generate_card_with_text_enhancement(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test card generation with different text styles."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        # Test with different text styles
        text_styles = ["ode", "future", "haiku", "newspaper", "standup"]

        for style in text_styles:
            request_data = {
                "employee_name": "John Doe",
                "text_style": style,
                "image_style": "digital_art",
            }

            response = client.post("/api/v1/cards/generate", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_generate_card_invalid_text_style(self, client: TestClient) -> None:
        """Test card generation fails with invalid text_style."""
        request_data = {
            "employee_name": "John Doe",
            "text_style": "invalid_style",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_generate_card_invalid_image_style(self, client: TestClient) -> None:
        """Test card generation fails with invalid image_style."""
        request_data = {
            "employee_name": "John Doe",
            "text_style": "ode",
            "image_style": "invalid_style",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_generate_card_empty_employee_name(self, client: TestClient) -> None:
        """Test card generation fails with empty employee_name."""
        request_data = {
            "employee_name": "",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_generate_card_whitespace_only_employee_name(
        self, client: TestClient
    ) -> None:
        """Test card generation fails with whitespace-only employee_name."""
        request_data = {
            "employee_name": "   ",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# Cards Regeneration Endpoint Tests
# ---------------------------------------------------------------------------


class TestCardsRegenerationEndpoint:
    """Tests for the POST /api/v1/cards/regenerate endpoint."""

    def test_regenerate_text_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test successful text regeneration."""
        new_variant = TextVariant(
            text="A brand new greeting for you!",
            style=TextStyle.ODE,
        )

        # Setup mock session
        mock_session = MagicMock()
        mock_session.is_expired.return_value = False
        mock_session.original_request = CardGenerationRequest(
            employee_name="John Doe",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.DIGITAL_ART,
        )
        mock_card_service._session_manager.get_session.return_value = mock_session

        mock_card_service.regenerate_text = AsyncMock(return_value=(new_variant, 2))

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["remaining_regenerations"] == 2
        assert data["data"]["variant"]["text"] == "A brand new greeting for you!"
        assert data["data"]["variant"]["style"] == "ode"

    def test_regenerate_image_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test successful image regeneration."""
        new_variant = ImageVariant(
            url="generated://image-new",
            style=ImageStyle.PIXEL_ART,
            prompt="A fresh pixel art greeting",
        )

        # Setup mock session
        mock_session = MagicMock()
        mock_session.is_expired.return_value = False
        mock_session.original_request = CardGenerationRequest(
            employee_name="John Doe",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.PIXEL_ART,
        )
        mock_card_service._session_manager.get_session.return_value = mock_session

        mock_card_service.regenerate_image = AsyncMock(return_value=(new_variant, 1))

        request_data = {
            "session_id": "test-session-123",
            "element_type": "image",
            "element_index": 1,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["remaining_regenerations"] == 1
        assert data["data"]["variant"]["url"] == "generated://image-new"
        assert data["data"]["variant"]["style"] == "pixel_art"

    def test_regenerate_invalid_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test regeneration fails for non-existent session."""
        mock_card_service._session_manager.get_session.return_value = None

        request_data = {
            "session_id": "invalid-session-id",
            "element_type": "text",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]

    def test_regenerate_limit_exceeded(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test regeneration returns 429 when limit is exceeded."""
        # Setup mock session
        mock_session = MagicMock()
        mock_session.is_expired.return_value = False
        mock_session.original_request = CardGenerationRequest(
            employee_name="John Doe",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.DIGITAL_ART,
        )
        mock_card_service._session_manager.get_session.return_value = mock_session

        mock_card_service.regenerate_text = AsyncMock(
            side_effect=RegenerationLimitExceededError("text", 3)
        )

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 429
        data = response.json()
        assert "Regeneration limit exceeded" in data["detail"]

    def test_regenerate_expired_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test regeneration fails for expired session."""
        # Setup mock session that is expired
        mock_session = MagicMock()
        mock_session.is_expired.return_value = True
        mock_card_service._session_manager.get_session.return_value = mock_session

        request_data = {
            "session_id": "expired-session-id",
            "element_type": "text",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "Session expired" in data["detail"]

    def test_regenerate_invalid_element_type(self, client: TestClient) -> None:
        """Test regeneration fails with invalid element_type."""
        request_data = {
            "session_id": "test-session-123",
            "element_type": "invalid",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_regenerate_invalid_element_index(self, client: TestClient) -> None:
        """Test regeneration fails with invalid element_index."""
        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
            "element_index": 5,  # Out of range (0-2)
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_regenerate_missing_session_id(self, client: TestClient) -> None:
        """Test regeneration fails with missing session_id."""
        request_data = {
            "element_type": "text",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# Cards Send Endpoint Tests
# ---------------------------------------------------------------------------


class TestCardsSendEndpoint:
    """Tests for the POST /api/v1/cards/send endpoint."""

    def test_send_card_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test successful card sending to Telegram."""
        send_response = SendCardResponse(
            success=True,
            message="Card sent successfully",
            telegram_message_id=12345,
        )

        mock_card_service.send_card = AsyncMock(return_value=send_response)

        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": 1,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["success"] is True
        assert data["data"]["telegram_message_id"] == 12345
        assert data["data"]["message"] == "Card sent successfully"

    def test_send_card_invalid_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test sending card fails for non-existent session."""
        mock_card_service.send_card = AsyncMock(
            side_effect=SessionNotFoundError("invalid-session-id")
        )

        request_data = {
            "session_id": "invalid-session-id",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]

    def test_send_card_invalid_variant(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test sending card fails with invalid variant index."""
        mock_card_service.send_card = AsyncMock(
            side_effect=VariantNotFoundError("text", 5)
        )

        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "variant not found" in data["detail"]

    def test_send_card_expired_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test sending card fails for expired session."""
        mock_card_service.send_card = AsyncMock(
            side_effect=SessionExpiredError("expired-session-id")
        )

        request_data = {
            "session_id": "expired-session-id",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "Session expired" in data["detail"]

    def test_send_card_missing_employee_name(self, client: TestClient) -> None:
        """Test sending card fails with missing employee_name."""
        request_data = {
            "session_id": "test-session-123",
            "selected_text_index": 0,
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_send_card_invalid_text_index(self, client: TestClient) -> None:
        """Test sending card fails with invalid text index."""
        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": 5,  # Out of range
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_send_card_invalid_image_index(self, client: TestClient) -> None:
        """Test sending card fails with invalid image index."""
        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": -1,  # Negative index
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_send_card_telegram_failure(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test proper handling of Telegram API failure."""
        send_response = SendCardResponse(
            success=False,
            message="Telegram API error: Connection timeout",
            telegram_message_id=None,
        )

        mock_card_service.send_card = AsyncMock(return_value=send_response)

        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 500
        data = response.json()
        assert "Telegram API error" in data["detail"]


# ---------------------------------------------------------------------------
# Images Endpoint Tests
# ---------------------------------------------------------------------------


class TestImagesEndpoint:
    """Tests for the GET /api/v1/cards/images/{session_id}/{image_id} endpoint."""

    def test_get_image_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test successful image retrieval."""
        # Create mock image data (small PNG-like bytes)
        image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        mock_card_service._session_manager.get_image_data.return_value = image_data

        response = client.get("/api/v1/cards/images/test-session-123/image-001")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["cache-control"] == "public, max-age=3600"
        assert response.content == image_data

    def test_get_image_invalid_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test image retrieval fails for non-existent session."""
        mock_card_service._session_manager.get_image_data.return_value = None
        mock_card_service._session_manager.get_session.return_value = None

        response = client.get("/api/v1/cards/images/invalid-session/image-001")

        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]

    def test_get_image_invalid_image_id(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test image retrieval fails for non-existent image."""
        # Session exists but image not found
        mock_session = MagicMock()
        mock_session.is_expired.return_value = False

        mock_card_service._session_manager.get_image_data.return_value = None
        mock_card_service._session_manager.get_session.return_value = mock_session

        response = client.get("/api/v1/cards/images/test-session-123/invalid-image")

        assert response.status_code == 404
        data = response.json()
        assert "Image not found" in data["detail"]

    def test_get_image_expired_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test image retrieval fails for expired session."""
        # Session exists but is expired
        mock_session = MagicMock()
        mock_session.is_expired.return_value = True

        mock_card_service._session_manager.get_image_data.return_value = None
        mock_card_service._session_manager.get_session.return_value = mock_session

        response = client.get("/api/v1/cards/images/expired-session/image-001")

        assert response.status_code == 400
        data = response.json()
        assert "Session expired" in data["detail"]

    def test_get_image_content_length_header(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test that Content-Length header is set correctly."""
        image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 256

        mock_card_service._session_manager.get_image_data.return_value = image_data

        response = client.get("/api/v1/cards/images/test-session-123/image-001")

        assert response.status_code == 200
        assert response.headers["content-length"] == str(len(image_data))


# ---------------------------------------------------------------------------
# Response Schema Validation Tests
# ---------------------------------------------------------------------------


class TestResponseSchemaValidation:
    """Tests for validating API response schemas."""

    def test_health_response_schema(self, client: TestClient) -> None:
        """Validate health check response schema."""
        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "service", "version"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_generation_response_schema(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Validate card generation response schema."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "employee_name": "John Doe",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)
        data = response.json()

        # Validate APIResponse wrapper
        assert "success" in data
        assert "data" in data
        assert "error" in data

        # Validate CardGenerationResponse data
        response_data = data["data"]
        assert "session_id" in response_data
        assert "employee_name" in response_data
        assert "text_variants" in response_data
        assert "image_variants" in response_data

        # Validate variant structure
        for variant in response_data["text_variants"]:
            assert "text" in variant
            assert "style" in variant

        for variant in response_data["image_variants"]:
            assert "url" in variant
            assert "style" in variant
            assert "prompt" in variant

    def test_regenerate_response_schema(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Validate regeneration response schema."""
        new_variant = TextVariant(
            text="A brand new greeting!",
            style=TextStyle.ODE,
        )

        mock_session = MagicMock()
        mock_session.is_expired.return_value = False
        mock_session.original_request = CardGenerationRequest(
            employee_name="John Doe",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.DIGITAL_ART,
        )
        mock_card_service._session_manager.get_session.return_value = mock_session
        mock_card_service.regenerate_text = AsyncMock(return_value=(new_variant, 2))

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
            "element_index": 0,
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)
        data = response.json()

        # Validate APIResponse wrapper
        assert "success" in data
        assert "data" in data

        # Validate RegenerateResponse data
        response_data = data["data"]
        assert "variant" in response_data
        assert "remaining_regenerations" in response_data
        assert isinstance(response_data["remaining_regenerations"], int)

    def test_send_response_schema(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Validate send card response schema."""
        send_response = SendCardResponse(
            success=True,
            message="Card sent successfully",
            telegram_message_id=12345,
        )

        mock_card_service.send_card = AsyncMock(return_value=send_response)

        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": 0,
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)
        data = response.json()

        # Validate APIResponse wrapper
        assert "success" in data
        assert "data" in data

        # Validate SendCardResponse data
        response_data = data["data"]
        assert "success" in response_data
        assert "message" in response_data
        assert "telegram_message_id" in response_data

    def test_error_response_schema(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Validate error response schema."""
        mock_card_service.generate_card = AsyncMock(
            side_effect=RecipientNotFoundError("Unknown Person")
        )

        request_data = {
            "employee_name": "Unknown Person",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)
        data = response.json()

        assert response.status_code == 404
        assert "detail" in data


# ---------------------------------------------------------------------------
# Edge Cases and Boundary Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_generate_card_with_unicode_name(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test card generation with Unicode employee name."""
        sample_generation_response.employee_name = "John Doe"
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "employee_name": "John Doe",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200

    def test_generate_card_with_special_characters(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test card generation with special characters in name."""
        sample_generation_response.employee_name = "John O'Connor-Smith"
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "employee_name": "John O'Connor-Smith",
            "text_style": "haiku",
            "image_style": "movie",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200

    def test_regenerate_at_boundary_index(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test regeneration at boundary index (2)."""
        new_variant = TextVariant(text="Boundary test!", style=TextStyle.STANDUP)

        mock_session = MagicMock()
        mock_session.is_expired.return_value = False
        mock_session.original_request = CardGenerationRequest(
            employee_name="Test User",
            text_style=TextStyle.STANDUP,
            image_style=ImageStyle.SPACE,
        )
        mock_card_service._session_manager.get_session.return_value = mock_session
        mock_card_service.regenerate_text = AsyncMock(return_value=(new_variant, 0))

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
            "element_index": 2,  # Maximum valid index
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 200

    def test_send_card_with_all_valid_indices(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test sending card with all valid index combinations."""
        send_response = SendCardResponse(
            success=True,
            message="Card sent successfully",
            telegram_message_id=12345,
        )
        mock_card_service.send_card = AsyncMock(return_value=send_response)

        for text_idx in range(3):
            for image_idx in range(3):
                request_data = {
                    "session_id": "test-session-123",
                    "employee_name": "Test User",
                    "selected_text_index": text_idx,
                    "selected_image_index": image_idx,
                }

                response = client.post("/api/v1/cards/send", json=request_data)
                assert response.status_code == 200


# ---------------------------------------------------------------------------
# Concurrent Request Tests
# ---------------------------------------------------------------------------


class TestConcurrentRequests:
    """Tests for handling concurrent requests."""

    def test_multiple_generation_requests(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test handling multiple generation requests sequentially."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "employee_name": "John Doe",
            "text_style": "ode",
            "image_style": "digital_art",
        }

        # Send multiple requests
        responses = []
        for _ in range(5):
            response = client.post("/api/v1/cards/generate", json=request_data)
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["success"] is True
