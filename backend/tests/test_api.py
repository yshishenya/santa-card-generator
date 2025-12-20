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

    NEW architecture: 5 variants, one per AI style.

    Returns:
        List of 5 TextVariant objects.
    """
    return [
        TextVariant(text="О, великий John Doe! Твои труды озаряют наш путь!", style=TextStyle.ODE),
        TextVariant(text="Winter snow falls\nJohn Doe brings light\nSuccess blooms", style=TextStyle.HAIKU),
        TextVariant(text="BREAKING: John Doe achieves outstanding results!", style=TextStyle.NEWSPAPER),
        TextVariant(text="Report from 2025: John Doe's legacy continues...", style=TextStyle.FUTURE),
        TextVariant(text="So, John Doe walks into the office... productivity +200%!", style=TextStyle.STANDUP),
    ]


@pytest.fixture
def sample_image_variants() -> List[ImageVariant]:
    """Create sample image variants for testing.

    Uses 4 representative styles from the 15 available.

    Returns:
        List of 4 ImageVariant objects.
    """
    return [
        ImageVariant(
            url="generated://image-001",
            style=ImageStyle.HYPERREALISM,
            prompt="Photorealistic winter scene"
        ),
        ImageVariant(
            url="generated://image-002",
            style=ImageStyle.PIXEL_ART,
            prompt="Retro pixel art holiday greeting"
        ),
        ImageVariant(
            url="generated://image-003",
            style=ImageStyle.KNITTED,
            prompt="Cozy knitted texture scene"
        ),
        ImageVariant(
            url="generated://image-004",
            style=ImageStyle.WATERCOLOR,
            prompt="Soft watercolor winter scene"
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
        CardGenerationResponse object with all required fields.
    """
    return CardGenerationResponse(
        session_id="test-session-123",
        recipient="John Doe",
        original_text=None,
        text_variants=sample_text_variants,
        image_variants=sample_image_variants,
        remaining_text_regenerations=3,
        remaining_image_regenerations=3,
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
    """Tests for the POST /api/v1/cards/generate endpoint.

    NEW architecture: CardGenerationRequest uses recipient, sender, reason, message.
    All styles are generated automatically (5 text + 4 image variants).
    """

    def test_generate_card_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test successful card generation with all 5 text and 4 image variants."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "recipient": "John Doe",
            "sender": "HR Team",
            "reason": "Outstanding performance",
            "message": "Thank you for your hard work!",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["error"] is None
        assert data["data"]["session_id"] == "test-session-123"
        assert data["data"]["recipient"] == "John Doe"
        assert len(data["data"]["text_variants"]) == 5  # One per AI style
        assert len(data["data"]["image_variants"]) == 4  # One per image style

        # Verify text variant structure
        text_variant = data["data"]["text_variants"][0]
        assert "text" in text_variant
        assert "style" in text_variant

        # Verify image variant structure
        image_variant = data["data"]["image_variants"][0]
        assert "url" in image_variant
        assert "style" in image_variant
        assert "prompt" in image_variant

        # Verify regeneration counts
        assert "remaining_text_regenerations" in data["data"]
        assert "remaining_image_regenerations" in data["data"]

    def test_generate_card_missing_recipient(self, client: TestClient) -> None:
        """Test card generation fails with missing recipient."""
        request_data = {
            "sender": "HR Team",
            "reason": "Great work",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data

    def test_generate_card_minimal_request(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test card generation with only required field (recipient)."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "recipient": "John Doe",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

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
            "recipient": "Unknown Employee",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 404
        data = response.json()
        assert "Employee not found" in data["detail"]

    def test_generate_card_with_all_optional_fields(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_generation_response: CardGenerationResponse,
    ) -> None:
        """Test card generation with all optional fields populated."""
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "recipient": "John Doe",
            "sender": "The Team",
            "reason": "За отличную работу над проектом",
            "message": "С Новым Годом! Желаем успехов!",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_generate_card_empty_recipient(self, client: TestClient) -> None:
        """Test card generation fails with empty recipient."""
        request_data = {
            "recipient": "",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_generate_card_whitespace_only_recipient(
        self, client: TestClient
    ) -> None:
        """Test card generation fails with whitespace-only recipient."""
        request_data = {
            "recipient": "   ",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


# ---------------------------------------------------------------------------
# Cards Regeneration Endpoint Tests
# ---------------------------------------------------------------------------


class TestCardsRegenerationEndpoint:
    """Tests for the POST /api/v1/cards/regenerate endpoint.

    NEW architecture: Regenerates ALL variants of a type (text or image).
    No element_index - all 5 texts or all 4 images are regenerated at once.
    """

    def test_regenerate_text_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_text_variants: List[TextVariant],
    ) -> None:
        """Test successful text regeneration (regenerates all 5 text variants)."""
        # Create RegenerateResponse with all 5 text variants
        regen_response = RegenerateResponse(
            text_variants=sample_text_variants,
            remaining_regenerations=2,
        )

        mock_card_service.regenerate_text = AsyncMock(return_value=regen_response)

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["remaining_regenerations"] == 2
        assert "text_variants" in data["data"]
        assert len(data["data"]["text_variants"]) == 5

    def test_regenerate_image_success(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_image_variants: List[ImageVariant],
    ) -> None:
        """Test successful image regeneration (regenerates all 4 image variants)."""
        # Create RegenerateResponse with all 4 image variants
        regen_response = RegenerateResponse(
            image_variants=sample_image_variants,
            remaining_regenerations=1,
        )

        mock_card_service.regenerate_image = AsyncMock(return_value=regen_response)

        request_data = {
            "session_id": "test-session-123",
            "element_type": "image",
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["remaining_regenerations"] == 1
        assert "image_variants" in data["data"]
        assert len(data["data"]["image_variants"]) == 4

    def test_regenerate_invalid_session(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test regeneration fails for non-existent session."""
        mock_card_service.regenerate_text = AsyncMock(
            side_effect=SessionNotFoundError("invalid-session-id")
        )

        request_data = {
            "session_id": "invalid-session-id",
            "element_type": "text",
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
        mock_card_service.regenerate_text = AsyncMock(
            side_effect=RegenerationLimitExceededError("text", 3)
        )

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
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
        mock_card_service.regenerate_text = AsyncMock(
            side_effect=SessionExpiredError("expired-session-id")
        )

        request_data = {
            "session_id": "expired-session-id",
            "element_type": "text",
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
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_regenerate_missing_session_id(self, client: TestClient) -> None:
        """Test regeneration fails with missing session_id."""
        request_data = {
            "element_type": "text",
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

    def test_send_card_rejects_negative_text_index(self, client: TestClient) -> None:
        """Test sending card fails with negative text index (validation)."""
        request_data = {
            "session_id": "test-session-123",
            "employee_name": "John Doe",
            "selected_text_index": -1,  # Negative index (invalid)
            "selected_image_index": 0,
        }

        response = client.post("/api/v1/cards/send", json=request_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_send_card_rejects_negative_image_index(self, client: TestClient) -> None:
        """Test sending card fails with negative image index (validation)."""
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

        # API uses service.get_image_data() not service._session_manager
        mock_card_service.get_image_data.return_value = image_data

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
        mock_card_service.get_image_data.return_value = None
        mock_card_service.get_session.return_value = None

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

        mock_card_service.get_image_data.return_value = None
        mock_card_service.get_session.return_value = mock_session

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
        # Note: The API doesn't check session expiration for image retrieval.
        # It only checks if the image data exists and if session exists.
        # If image_data is None and session is None, return 404.
        mock_card_service.get_image_data.return_value = None
        mock_card_service.get_session.return_value = None

        response = client.get("/api/v1/cards/images/expired-session/image-001")

        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]

    def test_get_image_content_length_header(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test that Content-Length header is set correctly."""
        image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 256

        mock_card_service.get_image_data.return_value = image_data

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
            "recipient": "John Doe",
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
        assert "recipient" in response_data
        assert "text_variants" in response_data
        assert "image_variants" in response_data
        assert "remaining_text_regenerations" in response_data
        assert "remaining_image_regenerations" in response_data

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
        sample_text_variants: List[TextVariant],
    ) -> None:
        """Validate regeneration response schema."""
        regen_response = RegenerateResponse(
            text_variants=sample_text_variants,
            remaining_regenerations=2,
        )
        mock_card_service.regenerate_text = AsyncMock(return_value=regen_response)

        request_data = {
            "session_id": "test-session-123",
            "element_type": "text",
        }

        response = client.post("/api/v1/cards/regenerate", json=request_data)
        data = response.json()

        # Validate APIResponse wrapper
        assert "success" in data
        assert "data" in data

        # Validate RegenerateResponse data
        response_data = data["data"]
        assert "text_variants" in response_data or "image_variants" in response_data
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
            "recipient": "Unknown Person",
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
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "recipient": "Иванов Иван Иванович",
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
        mock_card_service.generate_card = AsyncMock(
            return_value=sample_generation_response
        )

        request_data = {
            "recipient": "John O'Connor-Smith",
            "reason": "За отличную работу!",
        }

        response = client.post("/api/v1/cards/generate", json=request_data)

        assert response.status_code == 200

    def test_regenerate_multiple_times(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
        sample_text_variants: List[TextVariant],
    ) -> None:
        """Test multiple regeneration requests."""
        # Each regeneration decreases the counter
        for remaining in [2, 1, 0]:
            regen_response = RegenerateResponse(
                text_variants=sample_text_variants,
                remaining_regenerations=remaining,
            )
            mock_card_service.regenerate_text = AsyncMock(return_value=regen_response)

            request_data = {
                "session_id": "test-session-123",
                "element_type": "text",
            }

            response = client.post("/api/v1/cards/regenerate", json=request_data)

            assert response.status_code == 200
            assert response.json()["data"]["remaining_regenerations"] == remaining

    def test_send_card_with_all_valid_indices(
        self,
        client: TestClient,
        mock_card_service: MagicMock,
    ) -> None:
        """Test sending card with all valid index combinations (5 text x 4 image)."""
        send_response = SendCardResponse(
            success=True,
            message="Card sent successfully",
            telegram_message_id=12345,
        )
        mock_card_service.send_card = AsyncMock(return_value=send_response)

        # Test some representative combinations (all 5x4=20 would be too many)
        test_combinations = [(0, 0), (2, 1), (4, 3)]  # First, middle, last

        for text_idx, image_idx in test_combinations:
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
            "recipient": "John Doe",
            "sender": "HR Team",
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
