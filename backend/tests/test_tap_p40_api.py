"""Endpoint tests for the Tap the P4.0 API."""

from fastapi.testclient import TestClient

from src.api import dependencies
from src.config import settings
from src.main import app


def test_tap_p40_api_saves_score_and_returns_leaderboard(tmp_path) -> None:
    original_path = settings.tap_p40_leaderboard_path
    object.__setattr__(settings, "tap_p40_leaderboard_path", str(tmp_path / "tap-p40.json"))
    dependencies._tap_p40_leaderboard_store = None

    try:
        client = TestClient(app)

        save_response = client.post(
            "/api/v1/tap-p40/scores",
            json={
                "player_name": "Катя",
                "score": 12,
                "correct_taps": 12,
                "wrong_taps": 1,
                "duration_ms": 25000,
            },
        )
        assert save_response.status_code == 200
        assert save_response.json()["data"]["rank"] == 1
        assert save_response.json()["data"]["personal_best"] is True

        leaderboard_response = client.get("/api/v1/tap-p40/leaderboard?period=all&limit=20")
        assert leaderboard_response.status_code == 200
        assert leaderboard_response.json()["data"]["entries"][0]["player_name"] == "Катя"
        assert leaderboard_response.json()["data"]["entries"][0]["score"] == 12
    finally:
        object.__setattr__(settings, "tap_p40_leaderboard_path", original_path)
        dependencies._tap_p40_leaderboard_store = None


def test_tap_p40_api_validates_payload() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/tap-p40/scores",
        json={
            "player_name": "",
            "score": -1,
            "correct_taps": 0,
            "wrong_taps": 0,
            "duration_ms": 1000,
        },
    )

    assert response.status_code == 422
