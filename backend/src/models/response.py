"""Generic API response models."""

from typing import Generic, List, Optional, TypeVar

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

    Contains the newly regenerated variants (all 5 texts or all 4 images)
    and the number of regenerations remaining for that element type.
    """

    text_variants: Optional[List[TextVariant]] = Field(
        None, description="New text variants if text was regenerated"
    )
    image_variants: Optional[List[ImageVariant]] = Field(
        None, description="New image variants if images were regenerated"
    )
    remaining_regenerations: int = Field(
        ..., description="Number of regenerations remaining", ge=0
    )
