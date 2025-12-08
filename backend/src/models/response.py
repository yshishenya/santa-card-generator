"""Generic API response models."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from src.models.card import ImageVariant, TextVariant

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper.

    This wrapper provides a consistent response format across all API endpoints,
    including success status, data payload, and optional error messages.
    """

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[T] = Field(None, description="Response data if successful")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")


class RegenerateResponse(BaseModel):
    """Response for regeneration endpoint.

    Contains the newly regenerated variant (either text or image) and the
    number of regenerations remaining for that element type.
    """

    variant: TextVariant | ImageVariant = Field(
        ..., description="The newly regenerated variant"
    )
    remaining_regenerations: int = Field(
        ..., description="Number of regenerations remaining", ge=0
    )
