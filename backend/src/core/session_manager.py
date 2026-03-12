"""In-memory session management for the photocard MVP flow."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from src.models.card import ImageStyle
from src.models.photocard import PhotocardImageVariant

logger = logging.getLogger(__name__)


@dataclass
class GenerationSession:
    """Stored data for one generated photocard session."""

    session_id: str
    full_name: str
    alter_ego: str
    image_variants: List[PhotocardImageVariant]
    image_data: Dict[str, bytes] = field(default_factory=dict)
    generated_styles: List[ImageStyle] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self, ttl_minutes: int) -> bool:
        expiry_time = self.created_at + timedelta(minutes=ttl_minutes)
        return datetime.now(timezone.utc) > expiry_time


class SessionManager:
    """Manage photocard sessions in memory with TTL expiration."""

    def __init__(self, session_ttl_minutes: int = 30) -> None:
        self._sessions: Dict[str, GenerationSession] = {}
        self._session_ttl_minutes = session_ttl_minutes

    def create_session(
        self,
        full_name: str,
        alter_ego: str,
        image_variants: List[PhotocardImageVariant],
        image_data: Dict[str, bytes],
        generated_styles: Optional[List[ImageStyle]] = None,
    ) -> str:
        session_id = str(uuid.uuid4())
        session = GenerationSession(
            session_id=session_id,
            full_name=full_name,
            alter_ego=alter_ego,
            image_variants=image_variants,
            image_data=image_data,
            generated_styles=list(generated_styles or []),
        )
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[GenerationSession]:
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired(self._session_ttl_minutes):
            del self._sessions[session_id]
            return None
        return session

    def get_image_data(self, session_id: str, image_id: str) -> Optional[bytes]:
        session = self.get_session(session_id)
        if session is None:
            return None
        return session.image_data.get(image_id)

    def cleanup_expired(self) -> int:
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if session.is_expired(self._session_ttl_minutes)
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
        return len(expired_ids)

    def get_session_count(self) -> int:
        return len(self._sessions)
