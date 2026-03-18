"""Unit tests for Tap the P4.0 leaderboard storage."""

import json
from datetime import datetime, timedelta, timezone

from src.core.tap_p40_leaderboard import TapP40LeaderboardStore
from src.models.tap_p40 import TapP40ScoreRequest


def test_tap_p40_store_handles_missing_and_invalid_file(tmp_path) -> None:
    leaderboard_path = tmp_path / "tap-p40.json"
    store = TapP40LeaderboardStore(str(leaderboard_path))

    assert store.get_leaderboard() == []

    leaderboard_path.write_text("{invalid", encoding="utf-8")

    assert store.get_leaderboard() == []


def test_tap_p40_store_uses_best_result_per_player_and_sorts(tmp_path) -> None:
    store = TapP40LeaderboardStore(str(tmp_path / "tap-p40.json"))

    result_first = store.save_score(
        TapP40ScoreRequest(
            player_name="Катя",
            score=15,
            correct_taps=15,
            wrong_taps=3,
            duration_ms=22000,
        )
    )
    assert result_first.rank == 1
    assert result_first.personal_best is True

    result_second = store.save_score(
        TapP40ScoreRequest(
            player_name="катя",
            score=18,
            correct_taps=18,
            wrong_taps=2,
            duration_ms=21000,
        )
    )
    assert result_second.rank == 1
    assert result_second.personal_best is True

    store.save_score(
        TapP40ScoreRequest(
            player_name="Илья",
            score=18,
            correct_taps=18,
            wrong_taps=4,
            duration_ms=19000,
        )
    )
    store.save_score(
        TapP40ScoreRequest(
            player_name="Маша",
            score=12,
            correct_taps=12,
            wrong_taps=1,
            duration_ms=17000,
        )
    )

    entries = store.get_leaderboard(limit=10, period="all")

    assert [entry.player_name for entry in entries] == ["катя", "Илья", "Маша"]
    assert entries[0].score == 18
    assert entries[0].wrong_taps == 2
    assert entries[1].wrong_taps == 4


def test_tap_p40_store_filters_daily_period_and_limit(tmp_path) -> None:
    leaderboard_path = tmp_path / "tap-p40.json"
    store = TapP40LeaderboardStore(str(leaderboard_path))

    store.save_score(
        TapP40ScoreRequest(
            player_name="Сегодня",
            score=8,
            correct_taps=8,
            wrong_taps=1,
            duration_ms=25000,
        )
    )

    payload = json.loads(leaderboard_path.read_text(encoding="utf-8"))
    payload[0]["created_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    leaderboard_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    store.save_score(
        TapP40ScoreRequest(
            player_name="Сейчас",
            score=10,
            correct_taps=10,
            wrong_taps=2,
            duration_ms=24000,
        )
    )

    day_entries = store.get_leaderboard(period="day", limit=5)
    all_entries = store.get_leaderboard(period="all", limit=1)

    assert [entry.player_name for entry in day_entries] == ["Сейчас"]
    assert len(all_entries) == 1
    assert all_entries[0].player_name == "Сейчас"
