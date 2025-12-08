"""Unit tests for SessionManager.

This module contains comprehensive tests for the SessionManager class,
which handles in-memory session storage for card generation sessions,
including variant management and regeneration limits.

Tests follow the AAA pattern (Arrange-Act-Assert) and cover:
- Session creation and retrieval
- Session expiration handling
- Text and image variant management
- Regeneration limit enforcement
- Session cleanup operations
"""

from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import patch
import uuid

import pytest

from src.core.session_manager import GenerationSession, SessionManager
from src.models.card import (
    CardGenerationRequest,
    ImageStyle,
    ImageVariant,
    TextStyle,
    TextVariant,
)


class TestSessionManagerCreateSession:
    """Tests for SessionManager.create_session method."""

    def test_create_session_returns_uuid(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that create_session returns a valid UUID string.

        Verifies that the session ID returned by create_session is a valid UUID
        format string that can be used to retrieve the session later.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Assert
        assert session_id is not None
        assert isinstance(session_id, str)
        # Verify it's a valid UUID by parsing it
        parsed_uuid = uuid.UUID(session_id)
        assert str(parsed_uuid) == session_id

    def test_create_session_stores_request_data(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that create_session stores all request data correctly.

        Verifies that the created session contains the original request,
        variants, and image data as provided.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.request == sample_card_request
        assert session.text_variants == sample_text_variants
        assert session.image_variants == sample_image_variants
        assert session.image_data == sample_image_data

    def test_create_session_initializes_regeneration_counters(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that create_session initializes regeneration counters correctly.

        Verifies that the session is created with the correct initial
        regeneration limits for both text and images.
        """
        # Arrange
        max_regenerations = 5
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.text_regenerations_left == max_regenerations
        assert session.image_regenerations_left == max_regenerations

    def test_create_session_increments_session_count(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that creating sessions increments the session count.

        Verifies that each session creation adds to the total session count.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        initial_count = manager.get_session_count()

        # Act
        manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Assert
        assert manager.get_session_count() == initial_count + 2


class TestSessionManagerGetSession:
    """Tests for SessionManager.get_session method."""

    def test_get_session_returns_session(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that get_session returns the correct session for a valid ID.

        Verifies that a session can be retrieved using its ID and contains
        the expected data.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert isinstance(session, GenerationSession)
        assert session.id == session_id
        assert session.request.employee_name == sample_card_request.employee_name

    def test_get_session_returns_none_for_invalid_id(self) -> None:
        """Test that get_session returns None for an invalid session ID.

        Verifies that requesting a session with a non-existent ID returns None
        rather than raising an exception.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        invalid_session_id = str(uuid.uuid4())

        # Act
        session = manager.get_session(invalid_session_id)

        # Assert
        assert session is None

    def test_get_session_returns_none_for_expired(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that get_session returns None for an expired session.

        Verifies that sessions that have exceeded their TTL are not returned
        and are automatically cleaned up.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=1)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Verify session exists initially
        assert manager.get_session(session_id) is not None

        # Act - Simulate time passing by patching datetime
        expired_time = datetime.utcnow() + timedelta(minutes=2)
        with patch("src.core.session_manager.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = expired_time
            session = manager.get_session(session_id)

        # Assert
        assert session is None

    def test_get_session_removes_expired_session_from_storage(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that expired sessions are removed from storage when accessed.

        Verifies that accessing an expired session triggers its removal
        from the internal storage.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=1)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        initial_count = manager.get_session_count()

        # Act - Simulate time passing
        expired_time = datetime.utcnow() + timedelta(minutes=2)
        with patch("src.core.session_manager.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = expired_time
            manager.get_session(session_id)

        # Assert - Session should be removed from storage
        # Note: We need to check without the mock to verify actual storage
        assert manager.get_session_count() == initial_count - 1


class TestSessionManagerAddTextVariant:
    """Tests for SessionManager.add_text_variant method."""

    def test_add_text_variant_decrements_counter(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that adding a text variant decrements the regeneration counter.

        Verifies that each call to add_text_variant properly decrements
        the text_regenerations_left counter and returns the updated count.
        """
        # Arrange
        max_regenerations = 3
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = TextVariant(text="New generated text", style=TextStyle.ODE)

        # Act
        remaining = manager.add_text_variant(session_id, new_variant)

        # Assert
        assert remaining == max_regenerations - 1
        session = manager.get_session(session_id)
        assert session is not None
        assert session.text_regenerations_left == max_regenerations - 1
        assert len(session.text_variants) == len(sample_text_variants) + 1

    def test_add_text_variant_appends_to_list(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that adding a text variant appends it to the variants list.

        Verifies that the new variant is added to the end of the text_variants list.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = TextVariant(text="Brand new text variant!", style=TextStyle.HAIKU)

        # Act
        manager.add_text_variant(session_id, new_variant)
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.text_variants[-1] == new_variant

    def test_add_text_variant_raises_on_invalid_session(self) -> None:
        """Test that add_text_variant raises ValueError for invalid session ID.

        Verifies that attempting to add a variant to a non-existent session
        raises an appropriate error.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        invalid_session_id = str(uuid.uuid4())
        new_variant = TextVariant(text="Test text", style=TextStyle.ODE)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            manager.add_text_variant(invalid_session_id, new_variant)

        assert "Session not found" in str(exc_info.value)

    def test_add_text_variant_raises_on_limit_exceeded(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that add_text_variant raises error when limit is exceeded.

        Verifies that attempting to add more variants than allowed by
        max_regenerations raises an appropriate error.
        """
        # Arrange
        max_regenerations = 2
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = TextVariant(text="Test text", style=TextStyle.ODE)

        # Use up all regenerations
        for _ in range(max_regenerations):
            manager.add_text_variant(session_id, new_variant)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            manager.add_text_variant(session_id, new_variant)

        assert "Regeneration limit exceeded" in str(exc_info.value)


class TestSessionManagerAddImageVariant:
    """Tests for SessionManager.add_image_variant method."""

    def test_add_image_variant_decrements_counter(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that adding an image variant decrements the regeneration counter.

        Verifies that each call to add_image_variant properly decrements
        the image_regenerations_left counter and returns the updated count.
        """
        # Arrange
        max_regenerations = 3
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = ImageVariant(
            url="generated://new-img",
            style=ImageStyle.DIGITAL_ART,
            prompt="New festive image",
        )
        new_image_bytes = b"new_image_data_bytes"

        # Act
        remaining = manager.add_image_variant(session_id, new_variant, new_image_bytes)

        # Assert
        assert remaining == max_regenerations - 1
        session = manager.get_session(session_id)
        assert session is not None
        assert session.image_regenerations_left == max_regenerations - 1

    def test_add_image_variant_stores_image_data(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that adding an image variant stores the image bytes.

        Verifies that the image data is properly stored and can be retrieved.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = ImageVariant(
            url="generated://new-img-123",
            style=ImageStyle.PIXEL_ART,
            prompt="Pixel art winter scene",
        )
        new_image_bytes = b"pixel_art_image_data"

        # Act
        manager.add_image_variant(session_id, new_variant, new_image_bytes)

        # Assert
        retrieved_data = manager.get_image_data(session_id, new_variant.url)
        assert retrieved_data == new_image_bytes

    def test_add_image_variant_appends_to_list(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that adding an image variant appends it to the variants list.

        Verifies that the new variant is added to the end of the image_variants list.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = ImageVariant(
            url="generated://appended-img",
            style=ImageStyle.SPACE,
            prompt="Space themed greeting",
        )
        initial_count = len(sample_image_variants)

        # Act
        manager.add_image_variant(session_id, new_variant, b"image_bytes")
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert len(session.image_variants) == initial_count + 1
        assert session.image_variants[-1] == new_variant

    def test_add_image_variant_raises_on_limit_exceeded(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that add_image_variant raises error when limit is exceeded.

        Verifies that attempting to add more image variants than allowed
        raises an appropriate error.
        """
        # Arrange
        max_regenerations = 1
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = ImageVariant(
            url="generated://test-img",
            style=ImageStyle.MOVIE,
            prompt="Movie poster style",
        )

        # Use up all regenerations
        manager.add_image_variant(session_id, new_variant, b"data")

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            manager.add_image_variant(session_id, new_variant, b"more_data")

        assert "Regeneration limit exceeded" in str(exc_info.value)


class TestSessionManagerCleanupExpired:
    """Tests for SessionManager.cleanup_expired method."""

    def test_cleanup_expired_removes_old_sessions(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that cleanup_expired removes sessions that have exceeded TTL.

        Verifies that expired sessions are removed and the count of removed
        sessions is returned correctly.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=1)

        # Create multiple sessions
        session_id_1 = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        session_id_2 = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        initial_count = manager.get_session_count()
        assert initial_count == 2

        # Act - Simulate time passing
        expired_time = datetime.utcnow() + timedelta(minutes=2)
        with patch("src.core.session_manager.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = expired_time
            removed_count = manager.cleanup_expired()

        # Assert
        assert removed_count == 2
        assert manager.get_session_count() == 0

    def test_cleanup_expired_preserves_valid_sessions(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that cleanup_expired preserves sessions that haven't expired.

        Verifies that only expired sessions are removed, while valid sessions
        remain intact.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=60)  # 1 hour TTL
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act - Run cleanup without time passing
        removed_count = manager.cleanup_expired()

        # Assert
        assert removed_count == 0
        assert manager.get_session_count() == 1
        assert manager.get_session(session_id) is not None

    def test_cleanup_expired_returns_zero_when_no_expired(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that cleanup_expired returns 0 when no sessions have expired.

        Verifies correct behavior when all sessions are still valid.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act
        removed_count = manager.cleanup_expired()

        # Assert
        assert removed_count == 0


class TestRegenerationLimitRespected:
    """Tests for regeneration limit enforcement."""

    def test_regeneration_limit_respected(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that regeneration limits are strictly enforced.

        Verifies that after using all regeneration attempts, further
        regeneration requests are rejected with appropriate errors.
        """
        # Arrange
        max_regenerations = 3
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act - Use all text regenerations
        for i in range(max_regenerations):
            new_variant = TextVariant(text=f"Regenerated text {i}", style=TextStyle.ODE)
            remaining = manager.add_text_variant(session_id, new_variant)
            assert remaining == max_regenerations - i - 1

        # Assert - Next regeneration should fail
        with pytest.raises(ValueError) as exc_info:
            manager.add_text_variant(
                session_id,
                TextVariant(text="Too many regenerations", style=TextStyle.ODE),
            )
        assert "Regeneration limit exceeded" in str(exc_info.value)

    def test_text_and_image_limits_are_independent(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that text and image regeneration limits are tracked independently.

        Verifies that using up text regenerations doesn't affect image
        regeneration limit and vice versa.
        """
        # Arrange
        max_regenerations = 2
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act - Use all text regenerations
        for i in range(max_regenerations):
            manager.add_text_variant(
                session_id,
                TextVariant(text=f"Text {i}", style=TextStyle.ODE),
            )

        # Assert - Image regenerations should still be available
        session = manager.get_session(session_id)
        assert session is not None
        assert session.text_regenerations_left == 0
        assert session.image_regenerations_left == max_regenerations

        # Verify we can still add image variants
        remaining = manager.add_image_variant(
            session_id,
            ImageVariant(
                url="generated://img-new",
                style=ImageStyle.DIGITAL_ART,
                prompt="test",
            ),
            b"image_bytes",
        )
        assert remaining == max_regenerations - 1


class TestGenerationSessionExpiration:
    """Tests for GenerationSession.is_expired method."""

    def test_session_is_expired_when_past_ttl(self) -> None:
        """Test that is_expired returns True when session exceeds TTL.

        Verifies the expiration logic in the GenerationSession dataclass.
        """
        # Arrange
        request = CardGenerationRequest(
            employee_name="Test Employee",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.DIGITAL_ART,
        )
        session = GenerationSession(
            id=str(uuid.uuid4()),
            request=request,
            text_variants=[],
            image_variants=[],
            created_at=datetime.utcnow() - timedelta(minutes=35),
        )

        # Act & Assert
        assert session.is_expired(ttl_minutes=30) is True

    def test_session_is_not_expired_within_ttl(self) -> None:
        """Test that is_expired returns False when session is within TTL.

        Verifies that sessions are considered valid before the TTL expires.
        """
        # Arrange
        request = CardGenerationRequest(
            employee_name="Test Employee",
            text_style=TextStyle.ODE,
            image_style=ImageStyle.DIGITAL_ART,
        )
        session = GenerationSession(
            id=str(uuid.uuid4()),
            request=request,
            text_variants=[],
            image_variants=[],
            created_at=datetime.utcnow(),
        )

        # Act & Assert
        assert session.is_expired(ttl_minutes=30) is False


class TestGetImageData:
    """Tests for SessionManager.get_image_data method."""

    def test_get_image_data_returns_correct_bytes(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that get_image_data returns the correct image bytes.

        Verifies that image data can be retrieved by session ID and image URL.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        image_url = sample_image_variants[0].url
        expected_data = sample_image_data[image_url]

        # Act
        image_data = manager.get_image_data(session_id, image_url)

        # Assert
        assert image_data == expected_data

    def test_get_image_data_returns_none_for_invalid_session(self) -> None:
        """Test that get_image_data returns None for invalid session ID.

        Verifies graceful handling of requests for non-existent sessions.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)

        # Act
        image_data = manager.get_image_data(str(uuid.uuid4()), "some-url")

        # Assert
        assert image_data is None

    def test_get_image_data_returns_none_for_invalid_image_id(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that get_image_data returns None for invalid image ID.

        Verifies graceful handling of requests for non-existent images.
        """
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act
        image_data = manager.get_image_data(session_id, "non-existent-url")

        # Assert
        assert image_data is None
