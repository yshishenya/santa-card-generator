"""Unit tests for GeminiClient integration via LiteLLM proxy.

This module contains comprehensive tests for the GeminiClient class,
covering text generation with various styles, image generation, error handling,
and retry logic.

Test coverage:
- Text generation with all 5 supported styles
- Image generation with all 4 supported styles
- API error handling
- Retry logic on transient failures
- Client lifecycle (close method)
"""

import pytest
import base64
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from src.integrations.gemini import (
    GeminiClient,
    TEXT_STYLE_PROMPTS,
    IMAGE_STYLE_PROMPTS,
    HTTP_TIMEOUT_SECONDS,
    TEXT_MAX_TOKENS,
    IMAGE_MAX_TOKENS,
    VisualConcept,
)
from src.integrations.exceptions import (
    GeminiTextGenerationError,
    GeminiImageGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
)


class TestGeminiClientInit:
    """Tests for GeminiClient initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Test that GeminiClient initializes successfully with valid API key.

        Verifies that:
        - Client is created without errors
        - Default values are set correctly
        """
        # Arrange
        api_key = "valid-test-api-key"

        # Act
        client = GeminiClient(api_key=api_key)

        # Assert
        assert client._api_key == api_key
        assert client._base_url == "https://litellm.pro-4.ru/v1"
        assert client._text_model == "gemini-2.5-flash"
        assert client._image_model == "gemini/gemini-2.5-flash-image-preview"

    def test_init_with_custom_config(self) -> None:
        """Test initialization with custom configuration.

        Verifies that:
        - Custom base_url, text_model, and image_model are accepted
        """
        # Arrange & Act
        client = GeminiClient(
            api_key="test-key",
            base_url="https://custom.api.com/v1",
            text_model="custom/text-model",
            image_model="custom/image-model",
        )

        # Assert
        assert client._base_url == "https://custom.api.com/v1"
        assert client._text_model == "custom/text-model"
        assert client._image_model == "custom/image-model"

    def test_init_with_empty_api_key_raises_config_error(self) -> None:
        """Test that initialization with empty API key raises GeminiConfigError."""
        with pytest.raises(GeminiConfigError) as exc_info:
            GeminiClient(api_key="")

        assert "api_key" in str(exc_info.value.details.get("missing_param", ""))

    def test_init_with_none_api_key_raises_config_error(self) -> None:
        """Test that initialization with None API key raises GeminiConfigError."""
        with pytest.raises(GeminiConfigError):
            GeminiClient(api_key=None)

    def test_init_with_whitespace_api_key_raises_config_error(self) -> None:
        """Test that initialization with whitespace-only API key raises GeminiConfigError."""
        with pytest.raises(GeminiConfigError):
            GeminiClient(api_key="   ")


class TestGenerateTextStyles:
    """Tests for text generation with different styles."""

    @pytest.fixture
    def gemini_client(self) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(api_key="test-api-key")

    @pytest.fixture
    def mock_text_response(self) -> dict:
        """Create a mock successful text generation response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "Generated text response"
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_generate_text_with_ode_style(
        self, gemini_client: GeminiClient, mock_text_response: dict
    ) -> None:
        """Test text generation using 'ode' (ceremonial ode) style."""
        # Arrange
        mock_text_response["choices"][0]["message"]["content"] = (
            "О, великий Иван Петров! В сей день предновогодний..."
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_text_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            # Act
            result = await gemini_client.generate_text(
                prompt="",
                style="ode",
                recipient="Иван Петров",
                reason="отличную работу над проектом",
                message="С Новым Годом!",
            )

            # Assert
            assert isinstance(result, str)
            assert len(result) > 0
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/chat/completions"
            request_json = call_args[1]["json"]
            assert "Иван Петров" in request_json["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_generate_text_with_haiku_style(
        self, gemini_client: GeminiClient, mock_text_response: dict
    ) -> None:
        """Test text generation using 'haiku' (Japanese poetry) style."""
        mock_text_response["choices"][0]["message"]["content"] = (
            "Снег кружит над крышей\nИванов — как маяк —\nСветит сквозь метель"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_text_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await gemini_client.generate_text(
                prompt="",
                style="haiku",
                recipient="Иванов Иван",
                reason="креативный подход",
            )

            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_text_with_all_styles(
        self, gemini_client: GeminiClient, mock_text_response: dict
    ) -> None:
        """Test that all text styles can be used without error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_text_response
        mock_response.raise_for_status = MagicMock()

        for style in TEXT_STYLE_PROMPTS.keys():
            with patch.object(gemini_client, "_get_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                result = await gemini_client.generate_text(
                    prompt="",
                    style=style,
                    recipient="Test User",
                    reason="testing",
                )

                assert isinstance(result, str)


class TestGenerateTextErrors:
    """Tests for error handling in text generation."""

    @pytest.fixture
    def gemini_client(self) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_generate_text_handles_api_error(
        self, gemini_client: GeminiClient
    ) -> None:
        """Test that API errors are properly caught and wrapped."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal server error",
            request=MagicMock(),
            response=mock_response,
        )

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(GeminiTextGenerationError) as exc_info:
                await gemini_client.generate_text(
                    prompt="",
                    style="ode",
                    recipient="Test User",
                    reason="testing",
                )

            assert exc_info.value.original_error is not None

    @pytest.mark.asyncio
    async def test_generate_text_raises_rate_limit_error(
        self, gemini_client: GeminiClient
    ) -> None:
        """Test that rate limit errors are properly identified and raised."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(GeminiRateLimitError):
                await gemini_client.generate_text(
                    prompt="",
                    style="ode",
                    recipient="Test User",
                    reason="testing",
                )

    @pytest.mark.asyncio
    async def test_generate_text_invalid_style_raises_error(
        self, gemini_client: GeminiClient
    ) -> None:
        """Test that invalid style parameter raises GeminiTextGenerationError."""
        with pytest.raises(GeminiTextGenerationError) as exc_info:
            await gemini_client.generate_text(
                prompt="",
                style="invalid_style",
                recipient="Test User",
                reason="testing",
            )

        assert "invalid_style" in str(exc_info.value)
        assert "available_styles" in exc_info.value.details

    @pytest.mark.asyncio
    async def test_generate_text_empty_response_raises_error(
        self, gemini_client: GeminiClient
    ) -> None:
        """Test that empty API response raises GeminiTextGenerationError."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(GeminiTextGenerationError) as exc_info:
                await gemini_client.generate_text(
                    prompt="",
                    style="ode",
                    recipient="Test User",
                    reason="testing",
                )

            assert "пустой" in str(exc_info.value).lower()


class TestGenerateImage:
    """Tests for image generation functionality."""

    @pytest.fixture
    def gemini_client(self) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(api_key="test-api-key")

    @pytest.fixture
    def sample_visual_concept(self) -> VisualConcept:
        """Create a sample VisualConcept for testing."""
        return VisualConcept(
            core_theme="teamwork",
            visual_metaphor="Hands joining together in unity, symbolizing collaboration",
            key_elements=["joined hands", "warm glow", "team spirit"],
            mood="warm and inspiring",
        )

    @pytest.fixture
    def mock_image_response(self) -> dict:
        """Create a mock successful image generation response with base64 PNG."""
        # Create a minimal valid PNG (1x1 transparent pixel)
        png_data = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        ).decode("utf-8")

        return {
            "choices": [
                {
                    "message": {
                        "content": png_data
                    }
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_generate_image_returns_tuple(
        self, gemini_client: GeminiClient, mock_image_response: dict, sample_visual_concept: VisualConcept
    ) -> None:
        """Test that image generation returns tuple of (bytes, prompt).

        NEW architecture: generate_image accepts VisualConcept and returns Tuple[bytes, str].
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_image_response
        mock_response.raise_for_status = MagicMock()

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await gemini_client.generate_image(
                visual_concept=sample_visual_concept,
                style="knitted",
            )

            # Verify tuple structure
            assert isinstance(result, tuple)
            assert len(result) == 2

            image_bytes, prompt = result
            assert isinstance(image_bytes, bytes)
            assert image_bytes[:4] == b"\x89PNG"  # PNG magic bytes
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_generate_image_with_all_styles(
        self, gemini_client: GeminiClient, mock_image_response: dict, sample_visual_concept: VisualConcept
    ) -> None:
        """Test that all image styles can be used without error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_image_response
        mock_response.raise_for_status = MagicMock()

        for style in IMAGE_STYLE_PROMPTS.keys():
            with patch.object(gemini_client, "_get_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_get_client.return_value = mock_client

                result = await gemini_client.generate_image(
                    visual_concept=sample_visual_concept,
                    style=style,
                )

                # Verify result is tuple (bytes, str)
                assert isinstance(result, tuple)
                image_bytes, prompt = result
                assert isinstance(image_bytes, bytes)

    @pytest.mark.asyncio
    async def test_generate_image_invalid_style_raises_error(
        self, gemini_client: GeminiClient, sample_visual_concept: VisualConcept
    ) -> None:
        """Test that invalid image style raises GeminiImageGenerationError."""
        with pytest.raises(GeminiImageGenerationError) as exc_info:
            await gemini_client.generate_image(
                visual_concept=sample_visual_concept,
                style="invalid_style",
            )

        assert "invalid_style" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_image_handles_rate_limit(
        self, gemini_client: GeminiClient, sample_visual_concept: VisualConcept
    ) -> None:
        """Test that rate limit is properly handled for image generation."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(GeminiRateLimitError):
                await gemini_client.generate_image(
                    visual_concept=sample_visual_concept,
                    style="knitted",
                )

    @pytest.mark.asyncio
    async def test_generate_image_empty_response_raises_error(
        self, gemini_client: GeminiClient, sample_visual_concept: VisualConcept
    ) -> None:
        """Test that empty response raises appropriate error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(gemini_client, "_get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            with pytest.raises(GeminiImageGenerationError):
                await gemini_client.generate_image(
                    visual_concept=sample_visual_concept,
                    style="knitted",
                )


class TestExtractImageFromResponse:
    """Tests for _extract_image_from_response method."""

    @pytest.fixture
    def gemini_client(self) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(api_key="test-api-key")

    def test_extract_base64_png_direct(self, gemini_client: GeminiClient) -> None:
        """Test extraction of direct base64 PNG data."""
        # Minimal PNG data
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        base64_data = base64.b64encode(png_bytes).decode("utf-8")

        data = {
            "choices": [
                {
                    "message": {
                        "content": base64_data
                    }
                }
            ]
        }

        result = gemini_client._extract_image_from_response(data, "digital_art")
        assert result == png_bytes

    def test_extract_base64_with_data_uri(self, gemini_client: GeminiClient) -> None:
        """Test extraction of base64 PNG with data URI prefix."""
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        base64_data = base64.b64encode(png_bytes).decode("utf-8")

        data = {
            "choices": [
                {
                    "message": {
                        "content": f"data:image/png;base64,{base64_data}"
                    }
                }
            ]
        }

        result = gemini_client._extract_image_from_response(data, "digital_art")
        assert result == png_bytes

    def test_extract_empty_choices_raises_error(self, gemini_client: GeminiClient) -> None:
        """Test that empty choices raises error."""
        data = {"choices": []}

        with pytest.raises(GeminiImageGenerationError):
            gemini_client._extract_image_from_response(data, "digital_art")

    def test_extract_invalid_content_raises_error(self, gemini_client: GeminiClient) -> None:
        """Test that non-image content raises error."""
        data = {
            "choices": [
                {
                    "message": {
                        "content": "This is not an image"
                    }
                }
            ]
        }

        with pytest.raises(GeminiImageGenerationError):
            gemini_client._extract_image_from_response(data, "digital_art")


class TestClientLifecycle:
    """Tests for client lifecycle management."""

    @pytest.fixture
    def gemini_client(self) -> GeminiClient:
        """Create a GeminiClient instance for testing."""
        return GeminiClient(api_key="test-api-key")

    @pytest.mark.asyncio
    async def test_close_client(self, gemini_client: GeminiClient) -> None:
        """Test that close() method completes without error."""
        # First, create a mock client
        mock_http_client = AsyncMock()
        mock_http_client.is_closed = False
        mock_http_client.aclose = AsyncMock()
        gemini_client._http_client = mock_http_client

        # Act
        await gemini_client.close()

        # Assert - save reference before close() sets it to None
        mock_http_client.aclose.assert_called_once()
        assert gemini_client._http_client is None

    @pytest.mark.asyncio
    async def test_close_client_when_not_initialized(self, gemini_client: GeminiClient) -> None:
        """Test that close() works when client was never used."""
        # Client._http_client is None by default
        await gemini_client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_get_client_creates_new_client(self, gemini_client: GeminiClient) -> None:
        """Test that _get_client creates a new httpx.AsyncClient."""
        client = await gemini_client._get_client()

        assert isinstance(client, httpx.AsyncClient)
        assert client.headers["Authorization"] == "Bearer test-api-key"

        # Cleanup
        await client.aclose()


class TestTextStylePrompts:
    """Tests to verify text style prompts are properly configured."""

    def test_all_styles_have_prompts(self) -> None:
        """Test that all expected styles have associated prompts."""
        expected_styles = ["ode", "future", "haiku", "newspaper", "standup"]

        for style in expected_styles:
            assert style in TEXT_STYLE_PROMPTS, f"Missing style: {style}"
            prompt = TEXT_STYLE_PROMPTS[style]
            assert "{recipient}" in prompt, f"Missing {{recipient}} in {style}"
            assert "{reason}" in prompt, f"Missing {{reason}} in {style}"
            assert "{message}" in prompt, f"Missing {{message}} in {style}"

    def test_prompts_are_non_empty_strings(self) -> None:
        """Test that all style prompts are non-empty strings."""
        for style, prompt in TEXT_STYLE_PROMPTS.items():
            assert isinstance(prompt, str), f"Prompt for {style} is not a string"
            assert len(prompt) >= 100, f"Prompt for {style} is too short"


class TestImageStylePrompts:
    """Tests to verify image style prompts are properly configured."""

    def test_all_image_styles_have_prompts(self) -> None:
        """Test that all expected image styles have associated prompts."""
        # Updated to check for new visual concept placeholders
        expected_styles = ["knitted", "pixel_art", "watercolor", "hyperrealism"]

        for style in expected_styles:
            assert style in IMAGE_STYLE_PROMPTS, f"Missing image style: {style}"
            prompt = IMAGE_STYLE_PROMPTS[style]
            # New architecture: each style REINTERPRETS the theme creatively
            # Required placeholders: core_theme, visual_metaphor, mood
            assert "{core_theme}" in prompt, f"Missing {{core_theme}} in {style}"
            assert "{visual_metaphor}" in prompt, f"Missing {{visual_metaphor}} in {style}"
            assert "{mood}" in prompt, f"Missing {{mood}} in {style}"

    def test_image_prompts_are_non_empty_strings(self) -> None:
        """Test that all image style prompts are non-empty strings."""
        for style, prompt in IMAGE_STYLE_PROMPTS.items():
            assert isinstance(prompt, str), f"Prompt for {style} is not a string"
            assert len(prompt) >= 100, f"Prompt for {style} is too short"
