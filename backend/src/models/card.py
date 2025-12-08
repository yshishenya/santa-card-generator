"""Card-related Pydantic models."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TextStyle(str, Enum):
    """Text generation styles for greeting cards."""

    ORIGINAL = "original"  # No AI enhancement, use original message
    ODE = "ode"
    FUTURE = "future"
    HAIKU = "haiku"
    NEWSPAPER = "newspaper"
    STANDUP = "standup"


class ImageStyle(str, Enum):
    """Image generation styles for greeting cards."""

    DIGITAL_ART = "digital_art"
    PIXEL_ART = "pixel_art"
    SPACE = "space"
    MOVIE = "movie"


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
    """Request model for card generation."""

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
    enhance_text: bool = Field(False, description="Whether to enhance text using AI")
    text_style: Optional[TextStyle] = Field(
        None, description="Style for text generation (required if enhance_text is True)"
    )
    image_style: ImageStyle = Field(..., description="Style for image generation")

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

    @model_validator(mode="after")
    def validate_text_style_when_enhance(self) -> "CardGenerationRequest":
        """Validate text_style is provided when enhance_text is True.

        Returns:
            Validated request.

        Raises:
            ValueError: If enhance_text is True but text_style is None.
        """
        if self.enhance_text and self.text_style is None:
            raise ValueError("text_style is required when enhance_text is True")
        return self


class CardGenerationResponse(BaseModel):
    """Response model for card generation."""

    session_id: str = Field(..., description="Unique session ID for this generation")
    recipient: str = Field(..., description="Recipient name from request")
    text_variants: List[TextVariant] = Field(
        ..., description="List of generated text variants", min_length=1
    )
    image_variants: List[ImageVariant] = Field(
        ..., description="List of generated image variants", min_length=1
    )
    remaining_regenerations: int = Field(
        ..., description="Number of regenerations remaining for this session"
    )



class RegenerateRequest(BaseModel):
    """Request model for regenerating a specific card element."""

    session_id: str = Field(..., description="Session ID from initial generation")
    element_type: str = Field(..., description="Type of element to regenerate: 'text' or 'image'")
    element_index: int = Field(
        ..., description="Index of the element to regenerate (0-2)", ge=0, le=2
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
        ..., description="Index of selected text variant (0-2)", ge=0, le=2
    )
    selected_image_index: int = Field(
        ..., description="Index of selected image variant (0-2)", ge=0, le=2
    )


class SendCardResponse(BaseModel):
    """Response model after sending a card."""

    success: bool = Field(..., description="Whether the card was sent successfully")
    message: str = Field(..., description="Status message")
    telegram_message_id: int | None = Field(
        None, description="Telegram message ID if sent successfully"
    )
