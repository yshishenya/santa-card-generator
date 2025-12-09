"""Unit tests for SessionManager.

This module contains comprehensive tests for the SessionManager class,
which handles in-memory session storage for card generation sessions,
including variant management and regeneration limits.

Updated for new multi-style generation architecture:
- 5 text variants (one per AI style)
- 4 image variants (one per style)
- replace_text_variants() / replace_image_variants() replace ALL variants
- Separate regeneration counters for text and images
"""

from datetime import datetime, timedelta, timezone
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
        """Test that create_session returns a valid UUID string."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=sample_card_request.message,
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
        """Test that create_session stores all request data correctly."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        original_text = "Custom message from user"

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=original_text,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.original_request == sample_card_request
        assert session.original_text == original_text
        assert session.text_variants == sample_text_variants
        assert session.image_variants == sample_image_variants
        assert session.image_data == sample_image_data

    def test_create_session_stores_5_text_4_image_variants(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that session stores the correct number of variants (5 text, 4 image)."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert len(session.text_variants) == 5  # One per AI style
        assert len(session.image_variants) == 4  # One per image style

    def test_create_session_initializes_regeneration_counters(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that create_session initializes regeneration counters correctly."""
        # Arrange
        max_regenerations = 5
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)

        # Act
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
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
        """Test that creating sessions increments the session count."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        initial_count = manager.get_session_count()

        # Act
        manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        manager.create_session(
            request=sample_card_request,
            original_text=None,
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
        """Test that get_session returns the correct session for a valid ID."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
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
        assert session.original_request.recipient == sample_card_request.recipient

    def test_get_session_returns_none_for_invalid_id(self) -> None:
        """Test that get_session returns None for an invalid session ID."""
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
        """Test that get_session returns None for an expired session."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=1)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Verify session exists initially
        assert manager.get_session(session_id) is not None

        # Act - Access the session directly and modify created_at to simulate expiration
        session = manager._sessions[session_id]
        session.created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

        # Now get_session should return None
        result = manager.get_session(session_id)

        # Assert
        assert result is None

    def test_get_session_removes_expired_session_from_storage(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that expired sessions are removed from storage when accessed."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=1)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        initial_count = manager.get_session_count()

        # Simulate expiration
        session = manager._sessions[session_id]
        session.created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

        # Act - Access expired session
        manager.get_session(session_id)

        # Assert - Session should be removed from storage
        assert manager.get_session_count() == initial_count - 1


class TestSessionManagerReplaceTextVariants:
    """Tests for SessionManager.replace_text_variants method."""

    def test_replace_text_variants_decrements_counter(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replacing text variants decrements the regeneration counter."""
        # Arrange
        max_regenerations = 3
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variants = [
            TextVariant(text=f"New text {i}", style=style)
            for i, style in enumerate([
                TextStyle.ODE, TextStyle.HAIKU, TextStyle.NEWSPAPER,
                TextStyle.FUTURE, TextStyle.STANDUP
            ])
        ]

        # Act
        remaining = manager.replace_text_variants(session_id, new_variants)

        # Assert
        assert remaining == max_regenerations - 1
        session = manager.get_session(session_id)
        assert session is not None
        assert session.text_regenerations_left == max_regenerations - 1
        assert len(session.text_variants) == 5

    def test_replace_text_variants_replaces_all_variants(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replace_text_variants replaces all existing variants."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variants = [
            TextVariant(text="Brand new text 1", style=TextStyle.ODE),
            TextVariant(text="Brand new text 2", style=TextStyle.HAIKU),
            TextVariant(text="Brand new text 3", style=TextStyle.NEWSPAPER),
            TextVariant(text="Brand new text 4", style=TextStyle.FUTURE),
            TextVariant(text="Brand new text 5", style=TextStyle.STANDUP),
        ]

        # Act
        manager.replace_text_variants(session_id, new_variants)
        session = manager.get_session(session_id)

        # Assert
        assert session is not None
        assert session.text_variants == new_variants
        assert session.text_variants[0].text == "Brand new text 1"

    def test_replace_text_variants_raises_on_invalid_session(self) -> None:
        """Test that replace_text_variants raises ValueError for invalid session ID."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        invalid_session_id = str(uuid.uuid4())
        new_variants = [TextVariant(text="Test text", style=TextStyle.ODE)]

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            manager.replace_text_variants(invalid_session_id, new_variants)

        assert "Session not found" in str(exc_info.value)

    def test_replace_text_variants_raises_on_limit_exceeded(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replace_text_variants raises error when limit is exceeded."""
        # Arrange
        max_regenerations = 2
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variants = sample_text_variants

        # Use up all regenerations
        for _ in range(max_regenerations):
            manager.replace_text_variants(session_id, new_variants)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            manager.replace_text_variants(session_id, new_variants)

        assert "Regeneration limit exceeded" in str(exc_info.value)


class TestSessionManagerReplaceImageVariants:
    """Tests for SessionManager.replace_image_variants method."""

    def test_replace_image_variants_decrements_counter(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replacing image variants decrements the regeneration counter."""
        # Arrange
        max_regenerations = 3
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variants = [
            ImageVariant(url="generated://new-1", style=ImageStyle.DIGITAL_ART, prompt="New 1"),
            ImageVariant(url="generated://new-2", style=ImageStyle.SPACE, prompt="New 2"),
            ImageVariant(url="generated://new-3", style=ImageStyle.PIXEL_ART, prompt="New 3"),
            ImageVariant(url="generated://new-4", style=ImageStyle.MOVIE, prompt="New 4"),
        ]
        new_image_data = {v.url: f"new_bytes_{i}".encode() for i, v in enumerate(new_variants)}

        # Act
        remaining = manager.replace_image_variants(session_id, new_variants, new_image_data)

        # Assert
        assert remaining == max_regenerations - 1
        session = manager.get_session(session_id)
        assert session is not None
        assert session.image_regenerations_left == max_regenerations - 1

    def test_replace_image_variants_stores_new_image_data(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replacing image variants stores new image bytes."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variant = ImageVariant(
            url="generated://brand-new-img",
            style=ImageStyle.PIXEL_ART,
            prompt="Pixel art winter scene",
        )
        new_image_bytes = b"brand_new_pixel_art_data"
        new_variants = [new_variant]
        new_image_data = {new_variant.url: new_image_bytes}

        # Act
        manager.replace_image_variants(session_id, new_variants, new_image_data)

        # Assert
        retrieved_data = manager.get_image_data(session_id, new_variant.url)
        assert retrieved_data == new_image_bytes

    def test_replace_image_variants_clears_old_data(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replacing image variants clears old image data."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        old_image_url = sample_image_variants[0].url

        # Verify old data exists
        assert manager.get_image_data(session_id, old_image_url) is not None

        # Create new variants
        new_variants = [
            ImageVariant(url="generated://new-img", style=ImageStyle.SPACE, prompt="test")
        ]
        new_image_data = {"generated://new-img": b"new_data"}

        # Act
        manager.replace_image_variants(session_id, new_variants, new_image_data)

        # Assert - old data should be gone
        assert manager.get_image_data(session_id, old_image_url) is None

    def test_replace_image_variants_raises_on_limit_exceeded(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that replace_image_variants raises error when limit is exceeded."""
        # Arrange
        max_regenerations = 1
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        new_variants = sample_image_variants
        new_image_data = sample_image_data

        # Use up all regenerations
        manager.replace_image_variants(session_id, new_variants, new_image_data)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            manager.replace_image_variants(session_id, new_variants, new_image_data)

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
        """Test that cleanup_expired removes sessions that have exceeded TTL."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=1)

        # Create multiple sessions
        session_id_1 = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )
        session_id_2 = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        initial_count = manager.get_session_count()
        assert initial_count == 2

        # Simulate expiration for both sessions
        for sid in [session_id_1, session_id_2]:
            manager._sessions[sid].created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

        # Act
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
        """Test that cleanup_expired preserves sessions that haven't expired."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=60)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
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
        """Test that cleanup_expired returns 0 when no sessions have expired."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act
        removed_count = manager.cleanup_expired()

        # Assert
        assert removed_count == 0


class TestRegenerationLimitsIndependent:
    """Tests for independent regeneration limit enforcement."""

    def test_text_and_image_limits_are_independent(
        self,
        sample_card_request: CardGenerationRequest,
        sample_text_variants: List[TextVariant],
        sample_image_variants: List[ImageVariant],
        sample_image_data: Dict[str, bytes],
    ) -> None:
        """Test that text and image regeneration limits are tracked independently."""
        # Arrange
        max_regenerations = 2
        manager = SessionManager(max_regenerations=max_regenerations, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act - Use all text regenerations
        for _ in range(max_regenerations):
            manager.replace_text_variants(session_id, sample_text_variants)

        # Assert - Image regenerations should still be available
        session = manager.get_session(session_id)
        assert session is not None
        assert session.text_regenerations_left == 0
        assert session.image_regenerations_left == max_regenerations

        # Verify we can still replace image variants
        remaining = manager.replace_image_variants(
            session_id,
            sample_image_variants,
            sample_image_data,
        )
        assert remaining == max_regenerations - 1


class TestGenerationSessionExpiration:
    """Tests for GenerationSession.is_expired method."""

    def test_session_is_expired_when_past_ttl(
        self,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that is_expired returns True when session exceeds TTL."""
        # Arrange
        session = GenerationSession(
            id=str(uuid.uuid4()),
            original_request=sample_card_request,
            original_text=None,
            text_variants=[],
            image_variants=[],
            created_at=datetime.now(timezone.utc) - timedelta(minutes=35),
        )

        # Act & Assert
        assert session.is_expired(ttl_minutes=30) is True

    def test_session_is_not_expired_within_ttl(
        self,
        sample_card_request: CardGenerationRequest,
    ) -> None:
        """Test that is_expired returns False when session is within TTL."""
        # Arrange
        session = GenerationSession(
            id=str(uuid.uuid4()),
            original_request=sample_card_request,
            original_text=None,
            text_variants=[],
            image_variants=[],
            created_at=datetime.now(timezone.utc),
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
        """Test that get_image_data returns the correct image bytes."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
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
        """Test that get_image_data returns None for invalid session ID."""
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
        """Test that get_image_data returns None for invalid image ID."""
        # Arrange
        manager = SessionManager(max_regenerations=3, session_ttl_minutes=30)
        session_id = manager.create_session(
            request=sample_card_request,
            original_text=None,
            text_variants=sample_text_variants,
            image_variants=sample_image_variants,
            image_data=sample_image_data,
        )

        # Act
        image_data = manager.get_image_data(session_id, "non-existent-url")

        # Assert
        assert image_data is None
