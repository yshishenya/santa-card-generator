"""Models for the persistent print archive."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PrintArchiveAsset(BaseModel):
    """Public print archive item exposed to the UI."""

    asset_id: str = Field(..., description="Persistent archive item identifier")
    full_name: str = Field(..., description="Name entered in the photocard flow")
    alter_ego: str = Field(..., description="Alter ego text used for generation")
    caption: str = Field(..., description="Human-readable caption for print coordination")
    filename: str = Field(..., description="Suggested filename for downloading the PNG")
    created_at: datetime = Field(..., description="When the original image was archived")
    telegram_message_id: int | None = Field(
        None,
        description="Telegram message ID after successful delivery, if available",
    )
    delivery_env: Literal["staging", "prod"] | None = Field(
        None,
        description="Telegram delivery environment for the archived card, if sent",
    )


class StoredPrintArchiveAsset(PrintArchiveAsset):
    """Internal archive item with deduplication metadata."""

    session_id: str = Field(..., description="Photocard session ID")
    source_image_url: str = Field(..., description="Generated image URL from the session")


class PrintArchiveListResponse(BaseModel):
    """List response for the print archive UI."""

    assets: list[PrintArchiveAsset] = Field(
        default_factory=list,
        description="Archived original images available for download",
    )

