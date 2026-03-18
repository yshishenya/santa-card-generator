"""Models for the Tap the P4.0 game and leaderboard."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TapP40ScoreRequest(BaseModel):
    """Payload for one completed Tap the P4.0 run."""

    player_name: str = Field(..., min_length=1, max_length=80)
    score: int = Field(..., ge=0, le=9999)
    correct_taps: int = Field(..., ge=0, le=9999)
    wrong_taps: int = Field(..., ge=0, le=9999)
    duration_ms: int = Field(..., ge=5000, le=120000)
    game_version: str = Field(default="v1", min_length=1, max_length=20)


class TapP40StoredRun(BaseModel):
    """Internal append-only stored run."""

    run_id: str = Field(..., description="Unique run identifier")
    player_name: str = Field(..., description="Display name entered by the player")
    player_key: str = Field(..., description="Normalized key used for per-player grouping")
    score: int = Field(..., ge=0)
    correct_taps: int = Field(..., ge=0)
    wrong_taps: int = Field(..., ge=0)
    duration_ms: int = Field(..., ge=0)
    game_version: str = Field(..., description="Game ruleset version")
    created_at: datetime = Field(..., description="Run completion timestamp")


class TapP40LeaderboardEntry(BaseModel):
    """Public leaderboard entry."""

    rank: int = Field(..., ge=1)
    player_name: str = Field(..., description="Name shown in the leaderboard")
    score: int = Field(..., ge=0)
    correct_taps: int = Field(..., ge=0)
    wrong_taps: int = Field(..., ge=0)
    duration_ms: int = Field(..., ge=0)
    created_at: datetime = Field(..., description="When this best result was achieved")


class TapP40LeaderboardResponse(BaseModel):
    """Leaderboard response payload."""

    period: Literal["all", "day"] = Field(..., description="Requested leaderboard period")
    limit: int = Field(..., ge=1, le=100)
    entries: list[TapP40LeaderboardEntry] = Field(default_factory=list)


class TapP40ScoreResponse(BaseModel):
    """Response after saving one completed run."""

    rank: int = Field(..., ge=1)
    personal_best: bool = Field(..., description="Whether the saved run is the player's best result")
    saved_run: TapP40LeaderboardEntry = Field(..., description="Saved run reflected as a leaderboard row")
