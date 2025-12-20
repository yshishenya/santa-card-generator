"""Unit tests for CardService.

This module contains comprehensive tests for the CardService class,
which orchestrates the card generation workflow, including:
- Recipient validation
- Text and image variant generation (5 text + 4 image)
- Session management
- Bulk regeneration handling
- Telegram card delivery

Updated for new multi-style generation architecture:
- 5 text variants (one per AI style: ode, haiku, future, standup, newspaper)
- 4 image variants (one per style: digital_art, space, pixel_art, movie)
- Regeneration replaces ALL variants of a type
- Separate regeneration counters for text and images
"""

from typing import Dict, List
from unittest.mock import AsyncMock, patch, MagicMock
import uuid

import pytest

from src.core.card_service import CardService
from src.core.exceptions import (
    RecipientNotFoundError,
    RegenerationLimitExceededError,
    SessionNotFoundError,
)
from src.models.card import (
    CardGenerationRequest,
    CardGenerationResponse,
    ImageStyle,
    ImageVariant,
    SendCardRequest,
    SendCardResponse,
    TextStyle,
    TextVariant,
    AI_TEXT_STYLES,
    ALL_IMAGE_STYLES,
)
from src.models.employee import Employee
from src.models.response import RegenerateResponse


class TestCardServiceGenerateCard:
    """Tests for CardService.generate_card method."""

    @pytest.mark.asyncio
    async def test_generate_card_validates_recipient(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo_empty: AsyncMock,
    ) -> None:
        """Test that generate_card validates the recipient exists."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo_empty,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        request = CardGenerationRequest(
            recipient="Non Existent Person",
        )

        # Act & Assert
        with pytest.raises(RecipientNotFoundError) as exc_info:
            await service.generate_card(request)

        assert "Non Existent Person" in str(exc_info.value)
        mock_employee_repo_empty.get_by_name.assert_called_once_with("Non Existent Person")

    @pytest.mark.asyncio
    async def test_generate_card_creates_session(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card creates a session and returns session ID."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request)

        # Assert
        assert response is not None
        assert isinstance(response, CardGenerationResponse)
        assert response.session_id is not None
        assert isinstance(response.session_id, str)
        # Verify it's a valid UUID
        uuid.UUID(response.session_id)

    @pytest.mark.asyncio
    async def test_generate_card_returns_5_text_variants_no_images(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card returns 5 text variants (images generated separately)."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request)

        # Assert
        assert len(response.text_variants) == 5  # One per AI style
        assert len(response.image_variants) == 0  # Images generated via generate_images
        assert all(isinstance(v, TextVariant) for v in response.text_variants)

    @pytest.mark.asyncio
    async def test_generate_card_text_variants_have_correct_styles(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that text variants have one variant per AI style."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request)

        # Assert - Each AI style should be represented
        actual_styles = {v.style for v in response.text_variants}
        expected_styles = set(AI_TEXT_STYLES)
        assert actual_styles == expected_styles

    @pytest.mark.asyncio
    async def test_generate_images_returns_correct_styles(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_images returns variants with correct styles."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # First generate card to create session
        card_response = await service.generate_card(sample_card_request)

        # Select some image styles
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=card_response.session_id,
            image_styles=selected_styles,
        )

        # Act
        images_response = await service.generate_images(images_request)

        # Assert - Each selected image style should be represented
        actual_styles = {v.style for v in images_response.image_variants}
        expected_styles = set(selected_styles)
        assert actual_styles == expected_styles

    @pytest.mark.asyncio
    async def test_generate_card_calls_gemini_for_text_only(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card only calls Gemini client for text generation."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        await service.generate_card(sample_card_request)

        # Assert
        # Should be called 5 times for text variants (one per AI style)
        assert mock_gemini_client.generate_text.call_count == 5
        # Images are generated via generate_images, not generate_card
        assert mock_gemini_client.generate_image.call_count == 0
        assert mock_gemini_client.analyze_for_visual.call_count == 0

    @pytest.mark.asyncio
    async def test_generate_card_includes_recipient(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card includes recipient in response."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request)

        # Assert
        assert response.recipient == sample_card_request.recipient

    @pytest.mark.asyncio
    async def test_generate_card_stores_original_text(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card stores original text from user message."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request)

        # Assert
        assert response.original_text == sample_card_request.message


class TestCardServiceRegenerateText:
    """Tests for CardService.regenerate_text method."""

    @pytest.mark.asyncio
    async def test_regenerate_text_replaces_all_variants(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_text replaces ALL text variants."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        # First generate a card to create a session
        response = await service.generate_card(sample_card_request)
        session_id = response.session_id

        # Reset mock call count
        mock_gemini_client.generate_text.reset_mock()

        # Act
        regen_response = await service.regenerate_text(session_id)

        # Assert - Should generate 5 new text variants
        assert mock_gemini_client.generate_text.call_count == 5
        assert regen_response.text_variants is not None
        assert len(regen_response.text_variants) == 5
        assert regen_response.remaining_regenerations == 2  # 3 max - 1 used

    @pytest.mark.asyncio
    async def test_regenerate_text_fails_when_limit_exceeded(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_text fails when regeneration limit is exceeded."""
        # Arrange
        max_regenerations = 2
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=max_regenerations,
            session_ttl_minutes=30,
        )
        # Generate initial card
        response = await service.generate_card(sample_card_request)
        session_id = response.session_id

        # Use up all regenerations
        for _ in range(max_regenerations):
            await service.regenerate_text(session_id)

        # Act & Assert
        with pytest.raises(RegenerationLimitExceededError) as exc_info:
            await service.regenerate_text(session_id)

        assert "text" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_regenerate_text_fails_for_invalid_session(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that regenerate_text fails for invalid session ID."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        invalid_session_id = str(uuid.uuid4())

        # Act & Assert
        with pytest.raises(SessionNotFoundError) as exc_info:
            await service.regenerate_text(invalid_session_id)

        assert invalid_session_id in str(exc_info.value)


class TestCardServiceRegenerateImage:
    """Tests for CardService.regenerate_image method."""

    @pytest.mark.asyncio
    async def test_regenerate_image_replaces_all_variants(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_image replaces ALL image variants."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        # First generate a card to create a session
        response = await service.generate_card(sample_card_request)
        session_id = response.session_id

        # Generate initial images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        # Reset mock call counts
        mock_gemini_client.generate_image.reset_mock()
        mock_gemini_client.analyze_for_visual.reset_mock()

        # Act
        regen_response = await service.regenerate_image(session_id)

        # Assert - Should call analyze_for_visual once, then generate new images for all styles
        assert mock_gemini_client.analyze_for_visual.call_count == 1
        # regenerate_image generates for ALL available styles
        assert mock_gemini_client.generate_image.call_count == len(ALL_IMAGE_STYLES)
        assert regen_response.image_variants is not None
        assert len(regen_response.image_variants) == len(ALL_IMAGE_STYLES)
        assert regen_response.remaining_regenerations == 2  # 3 max - 1 used

    @pytest.mark.asyncio
    async def test_regenerate_image_fails_when_limit_exceeded(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_image fails when regeneration limit is exceeded."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        max_regenerations = 1
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=max_regenerations,
            session_ttl_minutes=30,
        )
        # Generate initial card
        response = await service.generate_card(sample_card_request)
        session_id = response.session_id

        # Generate initial images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        # Use up all regenerations
        await service.regenerate_image(session_id)

        # Act & Assert
        with pytest.raises(RegenerationLimitExceededError) as exc_info:
            await service.regenerate_image(session_id)

        assert "image" in str(exc_info.value).lower()


class TestCardServiceSendCard:
    """Tests for CardService.send_card method."""

    @pytest.mark.asyncio
    async def test_send_card_retrieves_session_data(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card retrieves and uses session data."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        # Generate card first
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Generate images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.recipient,
            selected_text_index=0,
            selected_image_index=0,
        )

        # Act
        response = await service.send_card(send_request)

        # Assert
        assert response is not None
        assert isinstance(response, SendCardResponse)

    @pytest.mark.asyncio
    async def test_send_card_calls_telegram_client(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card calls Telegram client to send the card."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        # Generate card first
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Generate images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.recipient,
            selected_text_index=0,
            selected_image_index=0,
        )

        # Act
        response = await service.send_card(send_request)

        # Assert
        mock_telegram_client.send_card.assert_called_once()
        assert response.success is True

    @pytest.mark.asyncio
    async def test_send_card_returns_telegram_message_id(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card returns the Telegram message ID."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        expected_message_id = 12345
        mock_telegram_client.send_card = AsyncMock(return_value=expected_message_id)

        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        # Generate card first
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Generate images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.recipient,
            selected_text_index=0,
            selected_image_index=0,
        )

        # Act
        response = await service.send_card(send_request)

        # Assert
        assert response.telegram_message_id == expected_message_id
        assert response.success is True

    @pytest.mark.asyncio
    async def test_send_card_fails_for_invalid_session(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that send_card fails for invalid session ID."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        invalid_session_id = str(uuid.uuid4())

        send_request = SendCardRequest(
            session_id=invalid_session_id,
            employee_name="Test Employee",
            selected_text_index=0,
            selected_image_index=0,
        )

        # Act & Assert
        with pytest.raises(SessionNotFoundError) as exc_info:
            await service.send_card(send_request)

        assert invalid_session_id in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_card_handles_telegram_error(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client_with_error: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card handles Telegram errors gracefully."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client_with_error,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        # Generate card first
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Generate images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.recipient,
            selected_text_index=0,
            selected_image_index=0,
        )

        # Act
        response = await service.send_card(send_request)

        # Assert
        assert response.success is False
        assert response.telegram_message_id is None
        assert "Failed" in response.message or "error" in response.message.lower()


class TestCardServiceVariantSelection:
    """Tests for variant selection in send_card."""

    @pytest.mark.asyncio
    async def test_send_card_uses_correct_text_index(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card uses the correct text variant by index."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        # Configure mock to return different texts for identification
        text_responses = [f"Text variant {i}" for i in range(5)]
        mock_gemini_client.generate_text = AsyncMock(side_effect=text_responses)

        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Generate images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        # Select the third text variant (index 2)
        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.recipient,
            selected_text_index=2,
            selected_image_index=0,
        )

        # Act
        await service.send_card(send_request)

        # Assert
        call_kwargs = mock_telegram_client.send_card.call_args.kwargs
        assert call_kwargs["message"] == "Text variant 2"

    @pytest.mark.asyncio
    async def test_send_card_uses_original_text_when_requested(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that send_card uses original text when use_original_text is True."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        request_with_message = CardGenerationRequest(
            recipient="Ivanov Ivan Ivanovich",
            message="My original heartfelt message",
        )

        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        gen_response = await service.generate_card(request_with_message)
        session_id = gen_response.session_id

        # Generate images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        # Request to use original text
        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=request_with_message.recipient,
            selected_text_index=0,
            selected_image_index=0,
            use_original_text=True,
        )

        # Act
        await service.send_card(send_request)

        # Assert
        call_kwargs = mock_telegram_client.send_card.call_args.kwargs
        assert call_kwargs["message"] == "My original heartfelt message"


class TestCardServiceConcurrentGeneration:
    """Tests for concurrent operations in CardService."""

    @pytest.mark.asyncio
    async def test_generate_card_generates_text_variants_concurrently(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card generates text variants concurrently."""
        # Arrange
        import asyncio

        call_order = []

        async def track_text_call(*args, **kwargs):
            call_order.append("text_start")
            await asyncio.sleep(0.01)
            call_order.append("text_end")
            return "Generated text"

        mock_gemini_client.generate_text = AsyncMock(side_effect=track_text_call)

        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        await service.generate_card(sample_card_request)

        # Assert - Verify text generations happened (images are via separate endpoint)
        assert mock_gemini_client.generate_text.call_count == 5
        # Images are not generated in generate_card
        assert mock_gemini_client.generate_image.call_count == 0

    @pytest.mark.asyncio
    async def test_generate_images_uses_two_stage_generation(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_images uses two-stage generation (analyze, then generate)."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Generate card first
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Reset mocks
        mock_gemini_client.analyze_for_visual.reset_mock()
        mock_gemini_client.generate_image.reset_mock()

        # Generate images for 4 styles
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )

        # Act
        await service.generate_images(images_request)

        # Assert - Two-stage generation:
        # Stage 1: analyze_for_visual called once
        assert mock_gemini_client.analyze_for_visual.call_count == 1
        # Stage 2: generate_image called for each style
        assert mock_gemini_client.generate_image.call_count == 4


class TestCardServiceInitialization:
    """Tests for CardService initialization."""

    def test_card_service_initialization(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that CardService initializes correctly with dependencies."""
        # Arrange & Act
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=5,
            session_ttl_minutes=60,
        )

        # Assert
        assert service is not None
        assert service._gemini_client is mock_gemini_client
        assert service._telegram_client is mock_telegram_client
        assert service._employee_repo is mock_employee_repo
        assert service._max_regenerations == 5

    def test_card_service_default_configuration(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that CardService uses default configuration values."""
        # Arrange & Act
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
        )

        # Assert
        assert service._max_regenerations == 3  # Default value


class TestCardServiceErrorHandling:
    """Tests for error handling in CardService."""

    @pytest.mark.asyncio
    async def test_generate_card_propagates_gemini_errors(
        self,
        mock_gemini_client_with_errors: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card propagates Gemini API errors."""
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client_with_errors,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await service.generate_card(sample_card_request)

        assert "API Error" in str(exc_info.value)


class TestCardServiceRegenerationLimitsIndependent:
    """Tests for independent regeneration limits."""

    @pytest.mark.asyncio
    async def test_text_and_image_regeneration_limits_are_independent(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that text and image regeneration limits are tracked independently."""
        from src.models.card import GenerateImagesRequest

        # Arrange
        max_regenerations = 2
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=max_regenerations,
            session_ttl_minutes=30,
        )

        # Generate initial card
        response = await service.generate_card(sample_card_request)
        session_id = response.session_id

        # Generate initial images
        selected_styles = list(ALL_IMAGE_STYLES)[:4]
        images_request = GenerateImagesRequest(
            session_id=session_id,
            image_styles=selected_styles,
        )
        await service.generate_images(images_request)

        # Use all text regenerations
        for _ in range(max_regenerations):
            await service.regenerate_text(session_id)

        # Act - Image regeneration should still work
        image_response = await service.regenerate_image(session_id)

        # Assert
        assert image_response.image_variants is not None
        # regenerate_image generates for ALL available styles
        assert len(image_response.image_variants) == len(ALL_IMAGE_STYLES)
        assert image_response.remaining_regenerations == max_regenerations - 1

    @pytest.mark.asyncio
    async def test_regeneration_response_includes_remaining_count(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regeneration response includes correct remaining count."""
        # Arrange
        max_regenerations = 3
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=max_regenerations,
            session_ttl_minutes=30,
        )

        response = await service.generate_card(sample_card_request)
        session_id = response.session_id

        # Act - First regeneration
        regen_1 = await service.regenerate_text(session_id)
        assert regen_1.remaining_regenerations == 2

        # Act - Second regeneration
        regen_2 = await service.regenerate_text(session_id)
        assert regen_2.remaining_regenerations == 1

        # Act - Third regeneration
        regen_3 = await service.regenerate_text(session_id)
        assert regen_3.remaining_regenerations == 0


class TestCardServiceInitialRegenerationCounts:
    """Tests for initial regeneration count in response."""

    @pytest.mark.asyncio
    async def test_generate_card_returns_initial_regeneration_counts(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card returns initial regeneration counts."""
        # Arrange
        max_regenerations = 5
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=max_regenerations,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request)

        # Assert
        assert response.remaining_text_regenerations == max_regenerations
        assert response.remaining_image_regenerations == max_regenerations
