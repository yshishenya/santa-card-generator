"""API endpoints for the Tap the P4.0 game."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_tap_p40_leaderboard_store
from src.core.tap_p40_leaderboard import TapP40LeaderboardStore
from src.models import APIResponse
from src.models.tap_p40 import (
    TapP40LeaderboardResponse,
    TapP40ScoreRequest,
    TapP40ScoreResponse,
)

router = APIRouter()


@router.get("/tap-p40/leaderboard", response_model=APIResponse[TapP40LeaderboardResponse])
async def get_tap_p40_leaderboard(
    store: Annotated[TapP40LeaderboardStore, Depends(get_tap_p40_leaderboard_store)],
    period: Literal["all", "day"] = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=100),
) -> APIResponse[TapP40LeaderboardResponse]:
    """Return the Tap the P4.0 leaderboard."""
    return APIResponse(
        success=True,
        data=TapP40LeaderboardResponse(
            period=period,
            limit=limit,
            entries=store.get_leaderboard(period=period, limit=limit),
        ),
        error=None,
    )


@router.post("/tap-p40/scores", response_model=APIResponse[TapP40ScoreResponse])
async def save_tap_p40_score(
    body: TapP40ScoreRequest,
    store: Annotated[TapP40LeaderboardStore, Depends(get_tap_p40_leaderboard_store)],
) -> APIResponse[TapP40ScoreResponse]:
    """Save one completed Tap the P4.0 run."""
    return APIResponse(
        success=True,
        data=store.save_score(body),
        error=None,
    )
