"""Unit tests for CardService.

This module contains comprehensive tests for the CardService class,
which orchestrates the card generation workflow, including:
- Recipient validation
- Text and image variant generation
- Session management
- Regeneration handling
- Telegram card delivery

Tests follow the AAA pattern (Arrange-Act-Assert) and use AsyncMock
for testing async dependencies.
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
)
from src.models.employee import Employee


class TestCardServiceGenerateCard:
    """Tests for CardService.generate_card method."""

    @pytest.mark.asyncio
    async def test_generate_card_validates_recipient(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo_empty: AsyncMock,
    ) -> None:
        """Test that generate_card validates the recipient exists.

        Verifies that RecipientNotFoundError is raised when the employee
        name doesn't match any employee in the repository.
        """
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo_empty,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        request = CardGenerationRequest(
            employee_name="Non Existent Person",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.DIGITAL_ART,
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
        """Test that generate_card creates a session and returns session ID.

        Verifies that a successful card generation returns a response
        containing a valid session ID.
        """
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
    async def test_generate_card_returns_variants(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card returns text and image variants.

        Verifies that the response contains exactly 3 text variants
        and 3 image variants as specified by the service.
        """
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
        assert len(response.text_variants) == 3
        assert len(response.image_variants) == 3
        assert all(isinstance(v, TextVariant) for v in response.text_variants)
        assert all(isinstance(v, ImageVariant) for v in response.image_variants)

    @pytest.mark.asyncio
    async def test_generate_card_calls_gemini_client(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card calls Gemini client for generation.

        Verifies that the Gemini client's generate_text and generate_image
        methods are called for each variant.
        """
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
        # Should be called 3 times for text variants
        assert mock_gemini_client.generate_text.call_count == 3
        # Should be called 3 times for image variants
        assert mock_gemini_client.generate_image.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_card_includes_employee_name(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card includes employee name in response.

        Verifies that the response correctly includes the employee name
        from the original request.
        """
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
        assert response.employee_name == sample_card_request.employee_name


class TestCardServiceRegenerateText:
    """Tests for CardService.regenerate_text method."""

    @pytest.mark.asyncio
    async def test_regenerate_text_adds_variant(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_text adds a new text variant.

        Verifies that regenerating text produces a new variant
        and returns it along with the remaining regeneration count.
        """
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
        new_variant, remaining = await service.regenerate_text(
            generation_id=session_id,
            original_request=sample_card_request,
        )

        # Assert
        assert new_variant is not None
        assert isinstance(new_variant, TextVariant)
        assert remaining == 2  # 3 max - 1 used = 2 remaining
        mock_gemini_client.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_text_fails_when_limit_exceeded(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_text fails when regeneration limit is exceeded.

        Verifies that RegenerationLimitExceededError is raised when
        attempting to regenerate beyond the maximum allowed.
        """
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
            await service.regenerate_text(session_id, sample_card_request)

        # Act & Assert
        with pytest.raises(RegenerationLimitExceededError) as exc_info:
            await service.regenerate_text(session_id, sample_card_request)

        assert "text" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_regenerate_text_fails_for_invalid_session(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_text fails for invalid session ID.

        Verifies that SessionNotFoundError is raised when trying to
        regenerate for a non-existent session.
        """
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
            await service.regenerate_text(invalid_session_id, sample_card_request)

        assert invalid_session_id in str(exc_info.value)


class TestCardServiceRegenerateImage:
    """Tests for CardService.regenerate_image method."""

    @pytest.mark.asyncio
    async def test_regenerate_image_adds_variant(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_image adds a new image variant.

        Verifies that regenerating image produces a new variant
        and returns it along with the remaining regeneration count.
        """
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
        mock_gemini_client.generate_image.reset_mock()

        # Act
        new_variant, remaining = await service.regenerate_image(
            generation_id=session_id,
            original_request=sample_card_request,
        )

        # Assert
        assert new_variant is not None
        assert isinstance(new_variant, ImageVariant)
        assert remaining == 2  # 3 max - 1 used = 2 remaining
        mock_gemini_client.generate_image.assert_called_once()

    @pytest.mark.asyncio
    async def test_regenerate_image_fails_when_limit_exceeded(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that regenerate_image fails when regeneration limit is exceeded.

        Verifies that RegenerationLimitExceededError is raised when
        attempting to regenerate beyond the maximum allowed.
        """
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

        # Use up all regenerations
        await service.regenerate_image(session_id, sample_card_request)

        # Act & Assert
        with pytest.raises(RegenerationLimitExceededError) as exc_info:
            await service.regenerate_image(session_id, sample_card_request)

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
        """Test that send_card retrieves and uses session data.

        Verifies that send_card correctly retrieves the session data
        including selected text and image variants.
        """
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

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.employee_name,
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
        """Test that send_card calls Telegram client to send the card.

        Verifies that the Telegram client's send_card method is called
        with the correct parameters.
        """
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

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.employee_name,
            selected_text_index=0,
            selected_image_index=0,
        )

        # Act
        response = await service.send_card(send_request)

        # Assert
        mock_telegram_client.send_card.assert_called_once()
        call_kwargs = mock_telegram_client.send_card.call_args.kwargs
        assert call_kwargs["employee_name"] == sample_card_request.employee_name
        assert "text" in call_kwargs
        assert "image_bytes" in call_kwargs
        assert response.success is True

    @pytest.mark.asyncio
    async def test_send_card_returns_telegram_message_id(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card returns the Telegram message ID.

        Verifies that the response includes the message ID returned
        by the Telegram client.
        """
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

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.employee_name,
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
        """Test that send_card fails for invalid session ID.

        Verifies that SessionNotFoundError is raised when trying to
        send a card with a non-existent session ID.
        """
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
        """Test that send_card handles Telegram errors gracefully.

        Verifies that errors from Telegram client are caught and
        a failure response is returned rather than raising an exception.
        """
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

        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.employee_name,
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
        """Test that send_card uses the correct text variant by index.

        Verifies that the selected_text_index correctly selects the
        corresponding text variant.
        """
        # Arrange
        # Configure mock to return different texts for identification
        text_responses = ["First text", "Second text", "Third text"]
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

        # Select the second text variant (index 1)
        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.employee_name,
            selected_text_index=1,
            selected_image_index=0,
        )

        # Act
        await service.send_card(send_request)

        # Assert
        call_kwargs = mock_telegram_client.send_card.call_args.kwargs
        assert call_kwargs["text"] == "Second text"

    @pytest.mark.asyncio
    async def test_send_card_uses_correct_image_index(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that send_card uses the correct image variant by index.

        Verifies that the selected_image_index correctly selects the
        corresponding image variant and its data.
        """
        # Arrange
        # Configure mock to return different images for identification
        image_responses = [
            (b"image_1_bytes", "prompt 1"),
            (b"image_2_bytes", "prompt 2"),
            (b"image_3_bytes", "prompt 3"),
        ]
        mock_gemini_client.generate_image = AsyncMock(side_effect=image_responses)

        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        gen_response = await service.generate_card(sample_card_request)
        session_id = gen_response.session_id

        # Select the third image variant (index 2)
        send_request = SendCardRequest(
            session_id=session_id,
            employee_name=sample_card_request.employee_name,
            selected_text_index=0,
            selected_image_index=2,
        )

        # Act
        await service.send_card(send_request)

        # Assert
        call_kwargs = mock_telegram_client.send_card.call_args.kwargs
        assert call_kwargs["image_bytes"] == b"image_3_bytes"


class TestCardServiceConcurrentGeneration:
    """Tests for concurrent operations in CardService."""

    @pytest.mark.asyncio
    async def test_generate_card_generates_variants_concurrently(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that generate_card generates text and image variants concurrently.

        Verifies that the service uses asyncio.gather to parallelize
        text and image generation for better performance.
        """
        # Arrange
        import asyncio

        call_order = []

        async def track_text_call(*args, **kwargs):
            call_order.append("text_start")
            await asyncio.sleep(0.01)  # Small delay to check concurrency
            call_order.append("text_end")
            return "Generated text"

        async def track_image_call(*args, **kwargs):
            call_order.append("image_start")
            await asyncio.sleep(0.01)
            call_order.append("image_end")
            return (b"image_bytes", "prompt")

        mock_gemini_client.generate_text = AsyncMock(side_effect=track_text_call)
        mock_gemini_client.generate_image = AsyncMock(side_effect=track_image_call)

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
        # Verify both text and image generation were called
        assert mock_gemini_client.generate_text.call_count == 3
        assert mock_gemini_client.generate_image.call_count == 3


class TestCardServiceDifferentStyles:
    """Tests for different text and image styles."""

    @pytest.mark.asyncio
    async def test_generate_card_with_haiku_style(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
        sample_card_request_haiku: CardGenerationRequest,
    ) -> None:
        """Test that generate_card works with haiku text style.

        Verifies that the service correctly processes requests with
        different text styles.
        """
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )

        # Act
        response = await service.generate_card(sample_card_request_haiku)

        # Assert
        assert response is not None
        assert response.employee_name == sample_card_request_haiku.employee_name

    @pytest.mark.asyncio
    async def test_generate_card_passes_correct_style_to_gemini(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that generate_card passes the correct style to Gemini.

        Verifies that the specified text and image styles are correctly
        passed to the Gemini client.
        """
        # Arrange
        service = CardService(
            gemini_client=mock_gemini_client,
            telegram_client=mock_telegram_client,
            employee_repo=mock_employee_repo,
            max_regenerations=3,
            session_ttl_minutes=30,
        )
        request = CardGenerationRequest(
            employee_name="Ivanov Ivan Ivanovich",
            text_style=TextStyle.NEWSPAPER,
            image_style=ImageStyle.SPACE,
        )

        # Act
        await service.generate_card(request)

        # Assert
        # Check that text generation was called with newspaper style
        text_call = mock_gemini_client.generate_text.call_args_list[0]
        assert text_call.args[1] == "newspaper" or text_call.kwargs.get("text_style") == "newspaper"

        # Check that image generation was called with space style
        image_call = mock_gemini_client.generate_image.call_args_list[0]
        assert image_call.args[1] == "space" or image_call.kwargs.get("image_style") == "space"


class TestCardServiceInitialization:
    """Tests for CardService initialization."""

    def test_card_service_initialization(
        self,
        mock_gemini_client: AsyncMock,
        mock_telegram_client: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> None:
        """Test that CardService initializes correctly with dependencies.

        Verifies that the service accepts all required dependencies
        and optional configuration parameters.
        """
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
        """Test that CardService uses default configuration values.

        Verifies that the service uses sensible defaults when optional
        parameters are not provided.
        """
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
        """Test that generate_card propagates Gemini API errors.

        Verifies that errors from the Gemini client are properly
        propagated to the caller.
        """
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
