"""Card-related Pydantic models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class TextStyle(str, Enum):
    """Text generation styles for greeting cards."""

    ORIGINAL = "original"  # No AI enhancement, use original message
    ODE = "ode"
    FUTURE = "future"
    HAIKU = "haiku"
    NEWSPAPER = "newspaper"
    STANDUP = "standup"


# All AI text styles (excluding ORIGINAL)
AI_TEXT_STYLES = [
    TextStyle.ODE,
    TextStyle.HAIKU,
    TextStyle.FUTURE,
    TextStyle.STANDUP,
    TextStyle.NEWSPAPER,
]

# Human-readable labels for text styles
TEXT_STYLE_LABELS = {
    TextStyle.ORIGINAL: "Оригинальный текст",
    TextStyle.ODE: "Торжественная ода",
    TextStyle.HAIKU: "Хайку",
    TextStyle.FUTURE: "Отчет из будущего",
    TextStyle.STANDUP: "Дружеский стендап",
    TextStyle.NEWSPAPER: "Заметка в газете",
}


class ImageStyle(str, Enum):
    """Image generation styles for greeting cards."""

    DIGITAL_ART = "digital_art"
    PIXEL_ART = "pixel_art"
    SPACE = "space"
    MOVIE = "movie"


# All image styles
ALL_IMAGE_STYLES = [
    ImageStyle.DIGITAL_ART,
    ImageStyle.SPACE,
    ImageStyle.PIXEL_ART,
    ImageStyle.MOVIE,
]

# Human-readable labels for image styles
IMAGE_STYLE_LABELS = {
    ImageStyle.DIGITAL_ART: "Цифровая живопись",
    ImageStyle.SPACE: "Космическая фантастика",
    ImageStyle.PIXEL_ART: "Пиксель-арт",
    ImageStyle.MOVIE: "Кадр из фильма",
}


class TextVariant(BaseModel):
    """A single text variant for a greeting card."""

    text: str = Field(..., description="The greeting text content", min_length=1)
    style: TextStyle = Field(..., description="The style used to generate this text")


class ImageVariant(BaseModel):
    """A single image variant for a greeting card."""

    url: str = Field(..., description="URL to the generated image")
    style: ImageStyle = Field(..., description="The style used to generate this image")
    prompt: str = Field(..., description="The prompt used to generate this image")


class CardGenerationRequest(BaseModel):
    """Request model for card generation.

    Simplified model - all text styles and all image styles are generated automatically.
    """

    recipient: str = Field(
        ..., description="Full name of the card recipient", min_length=1
    )
    sender: Optional[str] = Field(
        None, description="Name of the sender (optional)", max_length=100
    )
    reason: Optional[str] = Field(
        None, description="Reason for gratitude (optional)", max_length=150
    )
    message: Optional[str] = Field(
        None, description="Custom message from sender (optional)", max_length=1000
    )

    @field_validator("recipient")
    @classmethod
    def validate_recipient(cls, v: str) -> str:
        """Validate recipient name is not empty after stripping whitespace.

        Args:
            v: Recipient name to validate.

        Returns:
            Validated recipient name.

        Raises:
            ValueError: If name is empty or contains only whitespace.
        """
        if not v.strip():
            raise ValueError("Recipient name cannot be empty")
        return v.strip()


class CardGenerationResponse(BaseModel):
    """Response model for card generation."""

    session_id: str = Field(..., description="Unique session ID for this generation")
    recipient: str = Field(..., description="Recipient name from request")
    original_text: Optional[str] = Field(
        None, description="Original user message (if provided)"
    )
    text_variants: List[TextVariant] = Field(
        ..., description="List of generated text variants (5 styles)", min_length=1
    )
    image_variants: List[ImageVariant] = Field(
        ..., description="List of generated image variants (4 styles)", min_length=1
    )
    remaining_text_regenerations: int = Field(
        ..., description="Number of text regenerations remaining"
    )
    remaining_image_regenerations: int = Field(
        ..., description="Number of image regenerations remaining"
    )


class RegenerateRequest(BaseModel):
    """Request model for regenerating card elements.

    Regenerates ALL variants of the specified type (all 5 texts or all 4 images).
    """

    session_id: str = Field(..., description="Session ID from initial generation")
    element_type: str = Field(
        ..., description="Type of element to regenerate: 'text' or 'image'"
    )

    @field_validator("element_type")
    @classmethod
    def validate_element_type(cls, v: str) -> str:
        """Validate element type is either 'text' or 'image'.

        Args:
            v: Element type to validate.

        Returns:
            Validated element type.

        Raises:
            ValueError: If element type is not 'text' or 'image'.
        """
        if v not in ["text", "image"]:
            raise ValueError("element_type must be either 'text' or 'image'")
        return v


class SendCardRequest(BaseModel):
    """Request model for sending a card to Telegram."""

    session_id: str = Field(..., description="Session ID from generation")
    employee_name: str = Field(..., description="Employee name for the card")
    selected_text_index: int = Field(
        ..., description="Index of selected text variant", ge=0
    )
    selected_image_index: int = Field(
        ..., description="Index of selected image variant", ge=0
    )
    use_original_text: bool = Field(
        False,
        description="When true, use original user text instead of AI variant"
    )
    include_original_text: bool = Field(
        False,
        description="When true, include original user text alongside selected AI text"
    )


class SendCardResponse(BaseModel):
    """Response model after sending a card."""

    success: bool = Field(..., description="Whether the card was sent successfully")
    message: str = Field(..., description="Status message")
    telegram_message_id: int | None = Field(
        None, description="Telegram message ID if sent successfully"
    )
