"""Pydantic models package."""

from src.models.card import (
    CardGenerationRequest,
    CardGenerationResponse,
    GenerateImagesRequest,
    GenerateImagesResponse,
    ImageStyle,
    ImageVariant,
    RegenerateRequest,
    SendCardRequest,
    SendCardResponse,
    TextStyle,
    TextVariant,
)
from src.models.employee import Employee
from src.models.photocard import (
    PhotocardGenerateRequest,
    PhotocardGenerateResponse,
    PhotocardImageVariant,
    PhotocardSendRequest,
    PhotocardSendResponse,
)
from src.models.print_archive import PrintArchiveAsset, PrintArchiveListResponse
from src.models.response import APIResponse, RegenerateResponse
from src.models.tap_p40 import (
    TapP40LeaderboardEntry,
    TapP40LeaderboardResponse,
    TapP40ScoreRequest,
    TapP40ScoreResponse,
)

__all__ = [
    "TextStyle",
    "ImageStyle",
    "CardGenerationRequest",
    "CardGenerationResponse",
    "GenerateImagesRequest",
    "GenerateImagesResponse",
    "TextVariant",
    "ImageVariant",
    "RegenerateRequest",
    "SendCardRequest",
    "SendCardResponse",
    "Employee",
    "APIResponse",
    "RegenerateResponse",
    "PhotocardGenerateRequest",
    "PhotocardGenerateResponse",
    "PhotocardImageVariant",
    "PhotocardSendRequest",
    "PhotocardSendResponse",
    "PrintArchiveAsset",
    "PrintArchiveListResponse",
    "TapP40LeaderboardEntry",
    "TapP40LeaderboardResponse",
    "TapP40ScoreRequest",
    "TapP40ScoreResponse",
]
