"""Unit tests for the photocard SessionManager."""

from datetime import datetime, timedelta, timezone
import uuid

from src.core.session_manager import GenerationSession, SessionManager


class TestSessionManager:
    """Photocard session storage behavior."""

    def test_create_session_returns_uuid(
        self,
        sample_image_variants,
        sample_image_data,
    ) -> None:
        manager = SessionManager(session_ttl_minutes=30)

        session_id = manager.create_session(
            full_name="Jane Frost",
            alter_ego="Cyber captain",
            image_variants=sample_image_variants,
            image_data=sample_image_data,
            generated_styles=[variant.style for variant in sample_image_variants],
        )

        assert str(uuid.UUID(session_id)) == session_id

    def test_create_session_stores_photocard_payload(
        self,
        sample_image_variants,
        sample_image_data,
    ) -> None:
        manager = SessionManager(session_ttl_minutes=30)
        session_id = manager.create_session(
            full_name="Jane Frost",
            alter_ego="Cyber captain",
            image_variants=sample_image_variants,
            image_data=sample_image_data,
            generated_styles=[variant.style for variant in sample_image_variants],
        )

        session = manager.get_session(session_id)

        assert isinstance(session, GenerationSession)
        assert session is not None
        assert session.full_name == "Jane Frost"
        assert session.alter_ego == "Cyber captain"
        assert session.image_variants == sample_image_variants
        assert session.image_data == sample_image_data
        assert session.generated_styles == [variant.style for variant in sample_image_variants]

    def test_get_session_returns_none_for_expired_session(
        self,
        sample_image_variants,
        sample_image_data,
    ) -> None:
        manager = SessionManager(session_ttl_minutes=1)
        session_id = manager.create_session(
            full_name="Jane Frost",
            alter_ego="Cyber captain",
            image_variants=sample_image_variants,
            image_data=sample_image_data,
            generated_styles=[variant.style for variant in sample_image_variants],
        )

        manager._sessions[session_id].created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

        assert manager.get_session(session_id) is None
        assert session_id not in manager._sessions

    def test_get_image_data_returns_bytes(
        self,
        sample_image_variants,
        sample_image_data,
    ) -> None:
        manager = SessionManager(session_ttl_minutes=30)
        session_id = manager.create_session(
            full_name="Jane Frost",
            alter_ego="Cyber captain",
            image_variants=sample_image_variants,
            image_data=sample_image_data,
            generated_styles=[variant.style for variant in sample_image_variants],
        )

        first_variant = sample_image_variants[0]

        assert manager.get_image_data(session_id, first_variant.url) == sample_image_data[first_variant.url]

    def test_cleanup_expired_removes_only_expired_sessions(
        self,
        sample_image_variants,
        sample_image_data,
    ) -> None:
        manager = SessionManager(session_ttl_minutes=30)
        active_session_id = manager.create_session(
            full_name="Jane Frost",
            alter_ego="Cyber captain",
            image_variants=sample_image_variants,
            image_data=sample_image_data,
            generated_styles=[variant.style for variant in sample_image_variants],
        )
        expired_session_id = manager.create_session(
            full_name="John Snow",
            alter_ego="Fantasy ranger",
            image_variants=sample_image_variants,
            image_data=sample_image_data,
            generated_styles=[variant.style for variant in sample_image_variants],
        )
        manager._sessions[expired_session_id].created_at = (
            datetime.now(timezone.utc) - timedelta(minutes=31)
        )

        removed_count = manager.cleanup_expired()

        assert removed_count == 1
        assert active_session_id in manager._sessions
        assert expired_session_id not in manager._sessions
