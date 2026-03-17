"""Unit tests for the MVP photocard service."""

from unittest.mock import AsyncMock

import pytest

from src.core.card_service import CardService
from src.core.exceptions import SessionNotFoundError, VariantNotFoundError
from src.models.card import ImageStyle
from src.models.photocard import PhotocardSendRequest


class TestCardService:
    """Photocard generation and send behavior."""

    @pytest.mark.asyncio
    async def test_generate_photocard_returns_exactly_three_images(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        sample_photocard_request,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )

        response = await service.generate_photocard(sample_photocard_request)

        assert len(response.image_variants) == 3
        assert response.session_id
        assert mock_gemini_client.generate_image_direct.await_count == 3

    def test_classify_styles_uses_keyword_matches(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )

        styles = service._build_style_candidates("cyber neon superhero")

        assert styles[:3] == [
            ImageStyle.BENTO_GRID,
            ImageStyle.MINIMALIST_CORPORATE_LINE_ART,
            ImageStyle.QUIRKY_HAND_DRAWN_FLAT,
        ]

    def test_classify_styles_falls_back_to_defaults_when_no_match(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )

        styles = service._build_style_candidates("plain office persona")

        assert styles[:3] == [
            ImageStyle.BENTO_GRID,
            ImageStyle.MINIMALIST_CORPORATE_LINE_ART,
            ImageStyle.QUIRKY_HAND_DRAWN_FLAT,
        ]

    @pytest.mark.asyncio
    async def test_generate_photocard_stores_session_and_bytes(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        sample_photocard_request,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )

        response = await service.generate_photocard(sample_photocard_request)
        session = service.get_session(response.session_id)

        assert session is not None
        assert session.full_name == sample_photocard_request.full_name
        assert session.alter_ego == sample_photocard_request.alter_ego
        assert len(session.image_variants) == 3
        assert len(session.image_data) == 3

    @pytest.mark.asyncio
    async def test_send_photocard_uses_selected_image_and_caption_inputs(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        sample_photocard_request,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )
        generate_response = await service.generate_photocard(sample_photocard_request)

        response = await service.send_photocard(
            PhotocardSendRequest(
                session_id=generate_response.session_id,
                selected_image_index=1,
            )
        )

        assert response.success is True
        assert response.delivery_env == "staging"
        mock_telegram_client.send_photocard.assert_awaited_once()
        call_kwargs = mock_telegram_client.send_photocard.await_args.kwargs
        assert call_kwargs["full_name"] == sample_photocard_request.full_name
        assert call_kwargs["alter_ego"] == sample_photocard_request.alter_ego

    @pytest.mark.asyncio
    async def test_send_photocard_raises_for_missing_session(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )

        with pytest.raises(SessionNotFoundError):
            await service.send_photocard(
                PhotocardSendRequest(
                    session_id="missing-session",
                    selected_image_index=0,
                )
            )

    @pytest.mark.asyncio
    async def test_send_photocard_raises_for_invalid_image_index(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        sample_photocard_request,
    ) -> None:
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            session_ttl_minutes=30,
        )
        generate_response = await service.generate_photocard(sample_photocard_request)

        with pytest.raises(VariantNotFoundError):
            await service.send_photocard(
                PhotocardSendRequest(
                    session_id=generate_response.session_id,
                    selected_image_index=9,
                )
            )
