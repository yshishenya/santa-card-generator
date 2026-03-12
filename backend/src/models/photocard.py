"""Pydantic models for the photocard MVP flow."""

from typing import List, Literal

from pydantic import BaseModel, Field, field_validator

from src.models.card import ImageStyle


class PhotocardImageVariant(BaseModel):
    """Single generated photocard image."""

    url: str = Field(..., description="URL to the generated image")
    style: ImageStyle = Field(..., description="Style used to generate the image")


class PhotocardGenerateRequest(BaseModel):
    """Generate exactly three photocard image variants."""

    full_name: str = Field(..., description="Full name shown in the caption", max_length=200)
    alter_ego: str = Field(
        ...,
        description="Alter ego used to classify styles and guide generation",
        max_length=200,
    )

    @field_validator("full_name", "alter_ego")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty")
        return normalized


class PhotocardGenerateResponse(BaseModel):
    """Generate response for the photocard flow."""

    session_id: str = Field(..., description="Unique session ID for this generation")
    image_variants: List[PhotocardImageVariant] = Field(
        ...,
        description="Exactly three generated image variants",
        min_length=3,
        max_length=3,
    )


class PhotocardSendRequest(BaseModel):
    """Send one of the generated photocard images to Telegram."""

    session_id: str = Field(..., description="Session ID returned by generate")
    selected_image_index: int = Field(
        ...,
        description="Zero-based index of the image to send",
        ge=0,
    )


class PhotocardSendResponse(BaseModel):
    """Response after sending a photocard."""

    success: bool = Field(..., description="Whether the photocard was sent successfully")
    message: str = Field(..., description="Status message")
    telegram_message_id: int | None = Field(
        None,
        description="Telegram message ID if sending succeeded",
    )
    delivery_env: Literal["staging", "prod"] = Field(
        ...,
        description="Configured delivery environment used for send",
    )
