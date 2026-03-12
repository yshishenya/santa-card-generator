"""Photocard generation service for the MVP flow."""

import logging
import re
import uuid
from collections import defaultdict
from typing import Dict, List, Literal, Optional, Protocol, Sequence

from src.core.exceptions import CardServiceError, SessionNotFoundError, VariantNotFoundError
from src.core.session_manager import GenerationSession, SessionManager
from src.models.card import ImageStyle
from src.models.photocard import (
    PhotocardGenerateRequest,
    PhotocardGenerateResponse,
    PhotocardImageVariant,
    PhotocardSendRequest,
    PhotocardSendResponse,
)

logger = logging.getLogger(__name__)

DEFAULT_STYLE_FALLBACKS: List[ImageStyle] = [
    ImageStyle.HYPERREALISM,
    ImageStyle.FANTASY,
    ImageStyle.DIGITAL_3D,
]

STYLE_PRIORITY: List[ImageStyle] = [
    ImageStyle.HYPERREALISM,
    ImageStyle.FANTASY,
    ImageStyle.DIGITAL_3D,
    ImageStyle.CYBERPUNK,
    ImageStyle.COMIC_BOOK,
    ImageStyle.PIXEL_ART,
    ImageStyle.WATERCOLOR,
    ImageStyle.MAGIC_REALISM,
    ImageStyle.POP_ART,
    ImageStyle.LEGO,
    ImageStyle.PAPER_CUTOUT,
    ImageStyle.LINOCUT,
    ImageStyle.KNITTED,
    ImageStyle.SOVIET_POSTER,
    ImageStyle.VINTAGE_RUSSIAN,
]

STYLE_HINTS: dict[ImageStyle, Sequence[str]] = {
    ImageStyle.CYBERPUNK: (
        "cyber",
        "neon",
        "hacker",
        "robot",
        "android",
        "ai",
        "matrix",
        "future",
        "futur",
        "кибер",
        "робот",
        "неон",
        "будущ",
        "техно",
    ),
    ImageStyle.DIGITAL_3D: (
        "3d",
        "digital",
        "avatar",
        "architect",
        "builder",
        "designer",
        "virtual",
        "цифр",
        "дизайн",
        "архит",
    ),
    ImageStyle.HYPERREALISM: (
        "hero",
        "icon",
        "legend",
        "captain",
        "star",
        "movie",
        "cinema",
        "спорт",
        "легенд",
        "икон",
        "звезд",
        "геро",
    ),
    ImageStyle.FANTASY: (
        "wizard",
        "mage",
        "dragon",
        "knight",
        "elf",
        "fantasy",
        "myth",
        "волшеб",
        "маг",
        "дракон",
        "рыцар",
        "миф",
    ),
    ImageStyle.COMIC_BOOK: (
        "super",
        "superhero",
        "comic",
        "marvel",
        "dc",
        "guardian",
        "спасат",
        "супер",
        "комик",
        "герой",
    ),
    ImageStyle.PIXEL_ART: (
        "gamer",
        "gaming",
        "arcade",
        "retro",
        "8-bit",
        "pixel",
        "геймер",
        "игр",
        "пиксел",
        "ретро",
    ),
    ImageStyle.WATERCOLOR: (
        "artist",
        "poet",
        "dream",
        "gentle",
        "romantic",
        "flora",
        "цвет",
        "поэт",
        "мечт",
        "нежн",
        "худож",
    ),
    ImageStyle.MAGIC_REALISM: (
        "mystic",
        "surreal",
        "oracle",
        "vision",
        "alchemy",
        "шаман",
        "мист",
        "виден",
        "алхим",
        "сюр",
    ),
    ImageStyle.POP_ART: (
        "pop",
        "bold",
        "fashion",
        "glam",
        "trendy",
        "pop-art",
        "модн",
        "ярк",
        "глам",
        "поп",
    ),
    ImageStyle.LEGO: (
        "lego",
        "brick",
        "block",
        "maker",
        "toy",
        "лего",
        "кирпич",
        "конструкт",
    ),
    ImageStyle.PAPER_CUTOUT: (
        "craft",
        "paper",
        "origami",
        "collage",
        "handmade",
        "бумаг",
        "оригами",
        "апплика",
        "подел",
    ),
    ImageStyle.LINOCUT: (
        "woodcut",
        "print",
        "engrave",
        "bold lines",
        "linocut",
        "гравюр",
        "линогр",
        "печать",
    ),
    ImageStyle.KNITTED: (
        "cozy",
        "warm",
        "winter",
        "knit",
        "wool",
        "уют",
        "тепл",
        "вязан",
        "шерст",
    ),
    ImageStyle.SOVIET_POSTER: (
        "commander",
        "leader",
        "chief",
        "revolution",
        "poster",
        "лидер",
        "команд",
        "вожд",
        "плакат",
    ),
    ImageStyle.VINTAGE_RUSSIAN: (
        "retro",
        "classic",
        "nostalgia",
        "vintage",
        "antique",
        "винтаж",
        "классик",
        "носталь",
        "ретро",
    ),
}


class GeminiClient(Protocol):
    """Protocol for the Gemini integration used by the photocard flow."""

    async def generate_image_direct(
        self,
        style: str,
        reason: str | None = None,
        message: str | None = None,
    ) -> tuple[bytes, str]:
        ...

    async def close(self) -> None:
        ...


class TelegramClient(Protocol):
    """Protocol for the Telegram integration used by the photocard flow."""

    delivery_env: Literal["staging", "prod"]

    async def send_photocard(
        self,
        image_bytes: bytes,
        full_name: str,
        alter_ego: str,
        correlation_id: Optional[str] = None,
    ) -> int:
        ...


class CardService:
    """Generate and deliver photocard sessions."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        telegram_client: TelegramClient,
        session_ttl_minutes: int = 30,
    ) -> None:
        self._gemini_client = gemini_client
        self._telegram_client = telegram_client
        self._session_manager = SessionManager(session_ttl_minutes=session_ttl_minutes)

    def get_session(self, session_id: str) -> Optional[GenerationSession]:
        return self._session_manager.get_session(session_id)

    def get_image_data(self, session_id: str, image_url: str) -> bytes | None:
        return self._session_manager.get_image_data(session_id, image_url)

    async def generate_photocard(
        self,
        request: PhotocardGenerateRequest,
    ) -> PhotocardGenerateResponse:
        correlation_id = str(uuid.uuid4())
        candidate_styles = self._build_style_candidates(request.alter_ego)
        image_variants, image_data = await self._generate_exactly_three_images(
            full_name=request.full_name,
            alter_ego=request.alter_ego,
            candidate_styles=candidate_styles,
            correlation_id=correlation_id,
        )
        session_id = self._session_manager.create_session(
            full_name=request.full_name,
            alter_ego=request.alter_ego,
            image_variants=image_variants,
            image_data=image_data,
            generated_styles=[variant.style for variant in image_variants],
        )
        return PhotocardGenerateResponse(
            session_id=session_id,
            image_variants=image_variants,
        )

    async def send_photocard(
        self,
        request: PhotocardSendRequest,
    ) -> PhotocardSendResponse:
        correlation_id = str(uuid.uuid4())
        session = self._session_manager.get_session(request.session_id)
        if session is None:
            raise SessionNotFoundError(request.session_id)

        if request.selected_image_index >= len(session.image_variants):
            raise VariantNotFoundError("image", request.selected_image_index)

        selected_image = session.image_variants[request.selected_image_index]
        image_data = self._session_manager.get_image_data(
            request.session_id,
            selected_image.url,
        )
        if image_data is None:
            raise VariantNotFoundError("image", request.selected_image_index)

        try:
            message_id = await self._telegram_client.send_photocard(
                image_bytes=image_data,
                full_name=session.full_name,
                alter_ego=session.alter_ego,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            raise CardServiceError(f"Failed to send photocard: {exc}") from exc

        return PhotocardSendResponse(
            success=True,
            message="Photocard sent successfully",
            telegram_message_id=message_id,
            delivery_env=self._telegram_client.delivery_env,
        )

    def _normalize_text(self, value: str) -> str:
        normalized = value.lower().strip()
        normalized = re.sub(r"[^a-z0-9а-яё+ ]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized)

    def _classify_styles(self, alter_ego: str) -> List[ImageStyle]:
        normalized = self._normalize_text(alter_ego)
        tokens = normalized.split()
        scores: Dict[ImageStyle, int] = defaultdict(int)

        for style, hints in STYLE_HINTS.items():
            for hint in hints:
                normalized_hint = self._normalize_text(hint)
                if " " in normalized_hint:
                    if normalized_hint in normalized:
                        scores[style] += 2
                    continue

                if any(
                    token == normalized_hint or token.startswith(normalized_hint)
                    for token in tokens
                ):
                    scores[style] += 1

        ranked_styles = sorted(
            scores.items(),
            key=lambda item: (-item[1], STYLE_PRIORITY.index(item[0])),
        )
        return [style for style, score in ranked_styles if score > 0]

    def _build_style_candidates(self, alter_ego: str) -> List[ImageStyle]:
        candidates = self._classify_styles(alter_ego)
        for style in DEFAULT_STYLE_FALLBACKS:
            if style not in candidates:
                candidates.append(style)
        for style in STYLE_PRIORITY:
            if style not in candidates:
                candidates.append(style)
        return candidates

    async def _generate_exactly_three_images(
        self,
        full_name: str,
        alter_ego: str,
        candidate_styles: Sequence[ImageStyle],
        correlation_id: str,
    ) -> tuple[List[PhotocardImageVariant], Dict[str, bytes]]:
        variants: List[PhotocardImageVariant] = []
        image_data: Dict[str, bytes] = {}
        failures: List[str] = []

        for style in candidate_styles:
            if len(variants) == 3:
                break

            try:
                image_bytes, _prompt = await self._gemini_client.generate_image_direct(
                    style=style.value,
                    reason=f"Alter ego: {alter_ego}",
                    message=f"Create a festive photocard portrait for {full_name}",
                )
            except Exception as exc:
                failures.append(style.value)
                logger.warning(
                    "[%s] Failed generating style %s: %s",
                    correlation_id,
                    style.value,
                    exc,
                )
                continue

            image_id = str(uuid.uuid4())
            image_url = f"generated://{image_id}"
            variant = PhotocardImageVariant(url=image_url, style=style)
            variants.append(variant)
            image_data[image_url] = image_bytes

        if len(variants) != 3:
            raise CardServiceError(
                "Unable to generate exactly 3 image variants "
                f"(generated={len(variants)}, failed_styles={failures})"
            )

        return variants, image_data
