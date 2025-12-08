"""Session management for card generation sessions.

This module provides in-memory session storage for tracking card generation
sessions, variants, and regeneration limits.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

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
    text_variants: List[TextVariant]
    image_variants: List[ImageVariant]
    image_data: Dict[str, bytes] = field(default_factory=dict)
    text_regenerations_left: int = 3
    image_regenerations_left: int = 3
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self, ttl_minutes: int) -> bool:
        """Check if the session has expired.

        Args:
            ttl_minutes: Time-to-live in minutes.

        Returns:
            True if the session has exceeded the TTL, False otherwise.
        """
        expiry_time = self.created_at + timedelta(minutes=ttl_minutes)
        return datetime.utcnow() > expiry_time


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
        text_variants: List[TextVariant],
        image_variants: List[ImageVariant],
        image_data: Dict[str, bytes],
    ) -> str:
        """Create new session and return session ID.

        Args:
            request: Original card generation request.
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

    def add_text_variant(self, session_id: str, variant: TextVariant) -> int:
        """Add text variant to session and decrement regeneration counter.

        Args:
            session_id: Session ID to update.
            variant: New text variant to add.

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

        session.text_variants.append(variant)
        session.text_regenerations_left -= 1

        logger.info(
            f"Added text variant to session {session_id}, "
            f"regenerations_left={session.text_regenerations_left}"
        )

        return session.text_regenerations_left

    def add_image_variant(
        self, session_id: str, variant: ImageVariant, image_bytes: bytes
    ) -> int:
        """Add image variant to session and decrement regeneration counter.

        Args:
            session_id: Session ID to update.
            variant: New image variant to add.
            image_bytes: Raw image data for the variant.

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

        session.image_variants.append(variant)
        # Extract image ID from URL (assuming URL format contains an identifier)
        # For now, use the variant URL as the key
        image_id = variant.url
        session.image_data[image_id] = image_bytes
        session.image_regenerations_left -= 1

        logger.info(
            f"Added image variant to session {session_id}, "
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
