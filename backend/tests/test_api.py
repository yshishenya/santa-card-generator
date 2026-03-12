"""Endpoint contract tests for the MVP photocard API."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from src.api.photocards import generate_photocard, send_photocard
from src.core import CardService
from src.core.exceptions import CardServiceError, SessionNotFoundError, VariantNotFoundError
from src.main import health_check
from src.models.photocard import PhotocardGenerateRequest, PhotocardSendRequest


@pytest.fixture
def mock_card_service() -> MagicMock:
    """Create a mocked photocard service."""
    return MagicMock(spec=CardService)


class TestHealthEndpoints:
    """Health checks that should remain available."""

    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self) -> None:
        response = await health_check()

        assert response["status"] == "healthy"


class TestPhotocardGenerateEndpoint:
    """Generation endpoint coverage."""

    @pytest.mark.asyncio
    async def test_generate_success(
        self,
        mock_card_service: MagicMock,
        sample_generate_response,
    ) -> None:
        mock_card_service.generate_photocard = AsyncMock(return_value=sample_generate_response)

        response = await generate_photocard(
            body=PhotocardGenerateRequest(
                full_name="Jane Frost",
                alter_ego="Cyberpunk snow captain",
            ),
            service=mock_card_service,
        )

        assert response.success is True
        assert response.data is not None
        assert response.data.session_id == sample_generate_response.session_id
        assert len(response.data.image_variants) == 3

    @pytest.mark.asyncio
    async def test_generate_maps_service_error_to_500(
        self,
        mock_card_service: MagicMock,
    ) -> None:
        mock_card_service.generate_photocard = AsyncMock(
            side_effect=CardServiceError("generation failed")
        )

        with pytest.raises(HTTPException) as exc_info:
            await generate_photocard(
                body=PhotocardGenerateRequest(
                    full_name="Jane Frost",
                    alter_ego="Cyberpunk snow captain",
                ),
                service=mock_card_service,
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "generation failed"


class TestPhotocardSendEndpoint:
    """Send endpoint coverage."""

    @pytest.mark.asyncio
    async def test_send_success(
        self,
        mock_card_service: MagicMock,
        sample_send_response,
    ) -> None:
        mock_card_service.send_photocard = AsyncMock(return_value=sample_send_response)

        response = await send_photocard(
            body=PhotocardSendRequest(
                session_id="test-session-123",
                selected_image_index=1,
            ),
            service=mock_card_service,
        )

        assert response.success is True
        assert response.data is not None
        assert response.data.telegram_message_id == 12345
        assert response.data.delivery_env == "staging"

    @pytest.mark.asyncio
    async def test_send_missing_session_returns_404(
        self,
        mock_card_service: MagicMock,
    ) -> None:
        mock_card_service.send_photocard = AsyncMock(
            side_effect=SessionNotFoundError("missing-session")
        )

        with pytest.raises(HTTPException) as exc_info:
            await send_photocard(
                body=PhotocardSendRequest(
                    session_id="missing-session",
                    selected_image_index=0,
                ),
                service=mock_card_service,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Session not found: missing-session"

    @pytest.mark.asyncio
    async def test_send_invalid_image_index_returns_404(
        self,
        mock_card_service: MagicMock,
    ) -> None:
        mock_card_service.send_photocard = AsyncMock(
            side_effect=VariantNotFoundError("image", 7)
        )

        with pytest.raises(HTTPException) as exc_info:
            await send_photocard(
                body=PhotocardSendRequest(
                    session_id="test-session-123",
                    selected_image_index=7,
                ),
                service=mock_card_service,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Image variant not found at index: 7"
