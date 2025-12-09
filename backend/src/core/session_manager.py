"""Session management for card generation sessions.

This module provides in-memory session storage for tracking card generation
sessions, variants, and regeneration limits.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from src.models.card import CardGenerationRequest, ImageVariant, TextVariant

logger = logging.getLogger(__name__)


@dataclass
class GenerationSession:
    """Stores generation session data.

    A session contains all the information needed to track a card generation
    request, including the original request, generated variants, and remaining
    regeneration attempts.
    """

    id: str
    original_request: CardGenerationRequest
    original_text: Optional[str]  # User's original message
    text_variants: List[TextVariant]
    image_variants: List[ImageVariant]
    image_data: Dict[str, bytes] = field(default_factory=dict)
    text_regenerations_left: int = 3
    image_regenerations_left: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self, ttl_minutes: int) -> bool:
        """Check if the session has expired.

        Args:
            ttl_minutes: Time-to-live in minutes.

        Returns:
            True if the session has exceeded the TTL, False otherwise.
        """
        expiry_time = self.created_at + timedelta(minutes=ttl_minutes)
        return datetime.now(timezone.utc) > expiry_time


class SessionManager:
    """Manages card generation sessions.

    Provides in-memory storage for session data with TTL expiration,
    regeneration tracking, and image data storage.
    """

    def __init__(self, max_regenerations: int = 3, session_ttl_minutes: int = 30) -> None:
        """Initialize session manager.

        Args:
            max_regenerations: Maximum number of regenerations allowed per element type.
            session_ttl_minutes: Time-to-live for sessions in minutes.
        """
        self._sessions: Dict[str, GenerationSession] = {}
        self._max_regenerations = max_regenerations
        self._session_ttl_minutes = session_ttl_minutes
        logger.info(
            f"Initialized SessionManager with max_regenerations={max_regenerations}, "
            f"ttl={session_ttl_minutes}min"
        )

    def create_session(
        self,
        request: CardGenerationRequest,
        original_text: Optional[str],
        text_variants: List[TextVariant],
        image_variants: List[ImageVariant],
        image_data: Dict[str, bytes],
    ) -> str:
        """Create new session and return session ID.

        Args:
            request: Original card generation request.
            original_text: User's original message text.
            text_variants: List of generated text variants.
            image_variants: List of generated image variants.
            image_data: Dictionary mapping image variant IDs to image bytes.

        Returns:
            Unique session ID (UUID).
        """
        session_id = str(uuid.uuid4())

        session = GenerationSession(
            id=session_id,
            original_request=request,
            original_text=original_text,
            text_variants=text_variants,
            image_variants=image_variants,
            image_data=image_data,
            text_regenerations_left=self._max_regenerations,
            image_regenerations_left=self._max_regenerations,
        )

        self._sessions[session_id] = session

        logger.info(
            f"Created session {session_id} for recipient: {request.recipient}, "
            f"text_variants={len(text_variants)}, image_variants={len(image_variants)}"
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[GenerationSession]:
        """Get session by ID.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            GenerationSession if found and not expired, None otherwise.
        """
        session = self._sessions.get(session_id)

        if session is None:
            logger.warning(f"Session not found: {session_id}")
            return None

        if session.is_expired(self._session_ttl_minutes):
            logger.warning(f"Session expired: {session_id}")
            # Clean up expired session
            del self._sessions[session_id]
            return None

        logger.debug(f"Retrieved session {session_id}")
        return session

    def replace_text_variants(
        self, session_id: str, variants: List[TextVariant]
    ) -> int:
        """Replace all text variants in session and decrement regeneration counter.

        Args:
            session_id: Session ID to update.
            variants: New text variants to replace existing ones.

        Returns:
            Number of regenerations remaining.

        Raises:
            ValueError: If session not found or regeneration limit exceeded.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        if session.text_regenerations_left <= 0:
            raise ValueError(
                f"Regeneration limit exceeded for text in session {session_id}"
            )

        session.text_variants = variants
        session.text_regenerations_left -= 1

        logger.info(
            f"Replaced {len(variants)} text variants in session {session_id}, "
            f"regenerations_left={session.text_regenerations_left}"
        )

        return session.text_regenerations_left

    def replace_image_variants(
        self,
        session_id: str,
        variants: List[ImageVariant],
        image_data: Dict[str, bytes],
    ) -> int:
        """Replace all image variants in session and decrement regeneration counter.

        Args:
            session_id: Session ID to update.
            variants: New image variants to replace existing ones.
            image_data: New image data dictionary.

        Returns:
            Number of regenerations remaining.

        Raises:
            ValueError: If session not found or regeneration limit exceeded.
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        if session.image_regenerations_left <= 0:
            raise ValueError(
                f"Regeneration limit exceeded for image in session {session_id}"
            )

        # Clear old image data to free memory
        session.image_data.clear()
        session.image_variants = variants
        session.image_data = image_data
        session.image_regenerations_left -= 1

        logger.info(
            f"Replaced {len(variants)} image variants in session {session_id}, "
            f"regenerations_left={session.image_regenerations_left}"
        )

        return session.image_regenerations_left

    def get_image_data(self, session_id: str, image_id: str) -> Optional[bytes]:
        """Get image bytes for sending.

        Args:
            session_id: Session ID containing the image.
            image_id: Image identifier (typically the URL).

        Returns:
            Image bytes if found, None otherwise.
        """
        session = self.get_session(session_id)
        if session is None:
            logger.warning(f"Session not found: {session_id}")
            return None

        image_data = session.image_data.get(image_id)

        if image_data is None:
            logger.warning(f"Image data not found for {image_id} in session {session_id}")
        else:
            logger.debug(
                f"Retrieved image data for {image_id} in session {session_id}, "
                f"size={len(image_data)} bytes"
            )

        return image_data

    def cleanup_expired(self) -> int:
        """Remove expired sessions from storage.

        Returns:
            Number of sessions removed.
        """
        expired_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired(self._session_ttl_minutes)
        ]

        for session_id in expired_sessions:
            del self._sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    def get_session_count(self) -> int:
        """Get the current number of active sessions.

        Returns:
            Number of active sessions.
        """
        return len(self._sessions)
