"""Persistent leaderboard storage for Tap the P4.0."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.models.tap_p40 import (
    TapP40LeaderboardEntry,
    TapP40ScoreRequest,
    TapP40ScoreResponse,
    TapP40StoredRun,
)


class TapP40LeaderboardStore:
    """Store append-only game runs and build a best-per-player leaderboard."""

    def __init__(self, storage_path: str) -> None:
        self._storage_path = Path(storage_path)
        self._lock = threading.Lock()
        self._ensure_directory()

    def save_score(self, request: TapP40ScoreRequest) -> TapP40ScoreResponse:
        """Persist a completed run and return its leaderboard standing.
        
        This function locks access to the runs data, loads the current runs,  and
        determines the best run for the player before saving a new run  with the
        provided score details. After updating the runs, it checks  the player's new
        best run and builds the leaderboard entries. If the  saved score is not found
        in the leaderboard, it raises an error.  Finally, it returns the player's rank
        and whether the new score is a  personal best.
        """
        with self._lock:
            runs = self._load_runs_locked()
            best_before = self._best_run_for_player(runs, request.player_name)

            stored_run = TapP40StoredRun(
                run_id=str(uuid.uuid4()),
                player_name=request.player_name.strip(),
                player_key=self._build_player_key(request.player_name),
                score=request.score,
                correct_taps=request.correct_taps,
                wrong_taps=request.wrong_taps,
                duration_ms=request.duration_ms,
                game_version=request.game_version,
                created_at=datetime.now(timezone.utc),
            )
            runs.append(stored_run)
            self._write_runs_locked(runs)

            best_after = self._best_run_for_player(runs, request.player_name)
            assert best_after is not None
            personal_best = best_before is None or best_after.run_id == stored_run.run_id

            leaderboard = self._build_leaderboard_entries_locked(runs, period="all", limit=1000)
            saved_entry = next(
                (entry for entry in leaderboard if entry.player_name == best_after.player_name),
                None,
            )
            if saved_entry is None:
                raise RuntimeError("Saved Tap the P4.0 score is missing from leaderboard")

            return TapP40ScoreResponse(
                rank=saved_entry.rank,
                personal_best=personal_best,
                saved_run=saved_entry,
            )

    def get_leaderboard(
        self,
        *,
        period: str = "all",
        limit: int = 20,
    ) -> list[TapP40LeaderboardEntry]:
        """Return the leaderboard with one best result per player."""
        with self._lock:
            runs = self._load_runs_locked()
            return self._build_leaderboard_entries_locked(runs, period=period, limit=limit)

    def _ensure_directory(self) -> None:
        """Ensure the storage directory exists."""
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_runs_locked(self) -> list[TapP40StoredRun]:
        if not self._storage_path.exists():
            return []

        try:
            raw_payload = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        if not isinstance(raw_payload, list):
            return []

        runs: list[TapP40StoredRun] = []
        for item in raw_payload:
            try:
                runs.append(TapP40StoredRun.model_validate(item))
            except Exception:
                continue
        return runs

    def _write_runs_locked(self, runs: list[TapP40StoredRun]) -> None:
        """Writes the given runs to a temporary file and replaces the storage path."""
        payload = [run.model_dump(mode="json") for run in runs]
        temp_path = self._storage_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_path.replace(self._storage_path)

    def _build_leaderboard_entries_locked(
        self,
        runs: list[TapP40StoredRun],
        *,
        period: str,
        limit: int,
    ) -> list[TapP40LeaderboardEntry]:
        """Builds leaderboard entries from filtered runs.
        
        Args:
            runs (list[TapP40StoredRun]): The list of stored runs.
            period (str): The time period for filtering runs.
            limit (int): The maximum number of entries to return.
        
        Returns:
            list[TapP40LeaderboardEntry]: The leaderboard entries.
        """
        filtered_runs = self._filter_runs_for_period(runs, period=period)
        best_runs = self._best_runs_per_player(filtered_runs)
        best_runs.sort(key=self._sort_key)

        entries: list[TapP40LeaderboardEntry] = []
        for index, run in enumerate(best_runs[:limit], start=1):
            entries.append(
                TapP40LeaderboardEntry(
                    rank=index,
                    player_name=run.player_name,
                    score=run.score,
                    correct_taps=run.correct_taps,
                    wrong_taps=run.wrong_taps,
                    duration_ms=run.duration_ms,
                    created_at=run.created_at,
                )
            )
        return entries

    def _filter_runs_for_period(
        self,
        runs: list[TapP40StoredRun],
        *,
        period: str,
    ) -> list[TapP40StoredRun]:
        """Filter runs based on the specified period."""
        if period == "all":
            return list(runs)

        start_of_day = datetime.now(timezone.utc).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return [run for run in runs if run.created_at >= start_of_day]

    def _best_runs_per_player(self, runs: list[TapP40StoredRun]) -> list[TapP40StoredRun]:
        """Retrieve the best run for each player from a list of runs."""
        best_by_player: dict[str, TapP40StoredRun] = {}
        for run in runs:
            existing = best_by_player.get(run.player_key)
            if existing is None or self._sort_key(run) < self._sort_key(existing):
                best_by_player[run.player_key] = run
        return list(best_by_player.values())

    def _best_run_for_player(
        self,
        runs: list[TapP40StoredRun],
        player_name: str,
    ) -> TapP40StoredRun | None:
        """Return the best run for a specified player."""
        player_key = self._build_player_key(player_name)
        player_runs = [run for run in runs if run.player_key == player_key]
        if not player_runs:
            return None
        player_runs.sort(key=self._sort_key)
        return player_runs[0]

    def _build_player_key(self, player_name: str) -> str:
        return " ".join(player_name.strip().lower().split())

    def _sort_key(self, run: TapP40StoredRun) -> tuple[int, int, int, datetime]:
        """Return a tuple used for sorting TapP40StoredRun objects."""
        return (-run.score, run.wrong_taps, run.duration_ms, run.created_at)
