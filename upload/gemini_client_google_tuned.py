"""Reference-aware Google Gemini image client tuned for P4.0 photocard generation.

Why this exists:
- The stock prompts in the original module are too creative and under-constrained.
- For close reference matching, Google recommends multimodal image+text prompting,
  iterative refinement, and specific scene descriptions rather than keyword soup.
- This client keeps everything in Google models while adding reference-image support
  and much stricter art-direction control.

Usage example
-------------
from .gemini_client_google_tuned import ReferenceAwareGeminiClient, ReferenceImage

client = ReferenceAwareGeminiClient(
    api_key=...,
    # keep your current LiteLLM endpoint if needed
    base_url="https://litellm.pro-4.ru/v1",
    # if your proxy supports newer Google image models, prefer these:
    image_model="gemini/gemini-3.1-flash-image-preview",
    # or for highest-quality multi-turn design work:
    # image_model="gemini/gemini-3-pro-image-preview",
)

image_bytes, prompt = await client.generate_image_direct(
    style="bento_grid",
    reason="DJ / music lover",
    message="tile for P4.0 hobby mosaic",
    reference_images=[
        ReferenceImage("/path/to/ref_style_1.png", role="style", caption="primary style reference"),
        ReferenceImage("/path/to/ref_layout.png", role="layout", caption="layout / crop / scale reference"),
    ],
)
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import httpx

from .gemini import (
    GeminiClient,
    VisualConcept,
    IMAGE_STYLE_PROMPTS,
    IMAGE_MAX_TOKENS,
    TEXT_TEMPERATURE,
    PHOTOCARD_PRIMARY_TEMPERATURE,
    PHOTOCARD_RETRY_TEMPERATURE,
    PHOTOCARD_BRAND_PALETTE,
    _get_photocard_agent_overrides,
    _get_photocard_variation,
    _sample_photocard_palette,
    GeminiImageGenerationError,
    GeminiRateLimitError,
)

logger = logging.getLogger(__name__)

REFERENCE_MAX_IMAGES = 6
REFERENCE_PRIMARY_TEMPERATURE = 0.05

GOOGLE_IMAGE_SYSTEM_INSTRUCTION = """You are a Google multimodal image generation system operating in strict reference-following mode.

General behavior:
- If reference images are provided, treat them as binding art direction, not loose inspiration.
- Preserve the visual family of the references: crop, subject scale, background lightness, line weight, shape language, palette proportions, and detail density.
- Do not invent a different scene or a different dominant subject.
- Novelty is allowed only in tiny non-essential micro-details.
- Output a single final image, not explanatory text.
"""

GOOGLE_REFERENCE_LOCK = """REFERENCE LOCK:
- Preserve the main subject scale in frame.
- Preserve the negative-space ratio and light background.
- Preserve silhouette hierarchy and simplification level.
- Preserve line weight / module thickness / contour behavior.
- Preserve palette family and color balance.
- Keep secondary details sparse and subordinate.
- If text instructions conflict with the reference style/layout, prioritize the reference for style/layout and the text for the employee-specific hobby or role cue.
"""

REFERENCE_AWARE_PHOTOCARD_IMAGE_STYLE_PROMPTS = {
    "bento_grid": """Create one square 1:1 flat vector tile in geometric modular minimalism (Bento Grid).

BRIEF:
- Main hobby / role cue: {alter_ego}
- Context hint: {brief}

STYLE RULES:
- Use a 3x3 or 4x3 rectangular bento grid with hard module separations.
- Build one dominant connected central cluster that occupies about 70-80% of the tile.
- The main figure/object may fragment across adjacent modules, but must still read as one clear subject.
- Allow only 1-3 tiny supporting hobby icons in leftover cells.
- Structural modules must remain rectangular. Circles and simple arcs are allowed only inside motifs/icons.
- Use flat fills only. Keep the look vector-clean and mosaic-readable.
- Use exactly 4-5 colors from the approved palette as main fills. Black/white may be used as structure accents.
- Prefer #FFFFFF or #B9CDFF as the outer background.
- Any depth between modules must be extremely subtle.
- Do not create abstract pattern noise, detached decorative blocks, dark background fields, or crowded side fragments.

ALLOWED PALETTE:
- Primary: {primary_colors}
- Accent: {accent_colors}

COMPOSITION NOTE:
- {composition}
""",

    "minimalist_corporate_line_art": """Create one square 1:1 vector tile in minimalist corporate line-art.

BRIEF:
- Main hobby / role cue: {alter_ego}
- Context hint: {brief}

STYLE RULES:
- One dominant centered figure/object occupies about 70-80% of the tile.
- Use clean fixed-weight black vector contours with closed shapes.
- Hair, clothes, or major object masses may be solid black fills.
- White negative space should stay important and calm.
- Use only black, white, and 1-2 accent colors from the approved palette.
- Add at most 1-2 thin geometric UI-like frames/tabs and at most 1-2 tiny symbols (star, arrow, note, target) close to the main subject.
- The silhouette must remain immediately readable in a small mosaic tile.
- No dense decoration, no large dark background panels, no gradients, no textures, no realistic faces.

ALLOWED COLORS:
- Core: #000000, #FFFFFF
- Accent: {accent_colors}

COMPOSITION NOTE:
- {composition}
""",

    "quirky_hand_drawn_flat": """Create one square 1:1 flat illustration tile in contemporary quirky hand-drawn minimalism.

BRIEF:
- Main hobby / role cue: {alter_ego}
- Context hint: {brief}

STYLE RULES:
- One dominant rounded figure/object occupies about 70-80% of the tile.
- Use black or dark-graphite lively marker-like contour with visible variation in stroke thickness.
- Use bright flat fills from the approved palette with slight intentional color-offset / misregistration relative to the contour.
- Keep only 2-5 tiny doodle accents, close to the main subject.
- The figure should feel soft, human, charismatic, and immediately readable in a mosaic tile.
- Background must stay light and open.
- No clutter, no gradients, no realistic texture, no 3D depth cues, no photorealism.

ALLOWED PALETTE:
- Primary: {primary_colors}
- Accent: {accent_colors}

COMPOSITION NOTE:
- {composition}
""",
}


@dataclass
class ReferenceImage:
    """Image reference passed to Gemini as multimodal context.

    role:
        - style: rendering language / line behavior / material treatment
        - layout: crop, subject scale, subject placement, aspect-ratio lock
        - palette: color balance and background lightness
        - content: hobby cue / object / role signal that should survive in the final image
    """

    source: str
    role: str = "style"
    caption: str = ""


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://") or value.startswith("data:image/")


def _file_to_data_url(path_str: str) -> str:
    path = Path(path_str)
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/png"
    data = path.read_bytes()
    return f"data:{mime_type};base64,{base64.b64encode(data).decode('utf-8')}"


def _normalize_reference_images(
    reference_images: Optional[List[Union[str, ReferenceImage]]]
) -> List[ReferenceImage]:
    if not reference_images:
        return []
    normalized: List[ReferenceImage] = []
    for item in reference_images[:REFERENCE_MAX_IMAGES]:
        if isinstance(item, ReferenceImage):
            normalized.append(item)
        else:
            normalized.append(ReferenceImage(source=str(item)))
    return normalized


def _sorted_reference_images(reference_images: List[ReferenceImage]) -> List[ReferenceImage]:
    # Keep layout references last because Gemini tends to inherit aspect/crop
    # strongly from the last image in a multi-image prompt.
    priority = {
        "content": 0,
        "subject": 0,
        "character": 0,
        "style": 1,
        "palette": 2,
        "layout": 3,
        "composition": 3,
    }
    return sorted(reference_images, key=lambda item: priority.get(item.role, 10))


def _reference_summary(reference_images: List[ReferenceImage]) -> str:
    if not reference_images:
        return "No explicit image references supplied."
    lines: List[str] = []
    for idx, ref in enumerate(_sorted_reference_images(reference_images), start=1):
        note = f" — {ref.caption}" if ref.caption else ""
        lines.append(f"{idx}. role={ref.role}{note}")
    return "\n".join(lines)


def _build_multimodal_user_content(
    prompt: str,
    reference_images: List[ReferenceImage],
):
    if not reference_images:
        return prompt

    content = [{"type": "text", "text": prompt}]
    for ref in _sorted_reference_images(reference_images):
        url = ref.source if _looks_like_url(ref.source) else _file_to_data_url(ref.source)
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": url,
                    "detail": "auto",
                },
            }
        )
    return content


class ReferenceAwareGeminiClient(GeminiClient):
    """Drop-in replacement for image generation with stricter Google-style prompting."""

    def _build_image_messages(
        self,
        prompt: str,
        reference_images: Optional[List[Union[str, ReferenceImage]]] = None,
    ) -> list[dict]:
        refs = _normalize_reference_images(reference_images)
        return [
            {"role": "system", "content": GOOGLE_IMAGE_SYSTEM_INSTRUCTION},
            {"role": "user", "content": _build_multimodal_user_content(prompt, refs)},
        ]

    async def _post_image_request(
        self,
        *,
        style: str,
        prompt: str,
        aspect_ratio: str,
        temperature: float,
        reference_images: Optional[List[Union[str, ReferenceImage]]] = None,
    ) -> Tuple[bytes, str]:
        try:
            client = await self._get_client()
            messages = self._build_image_messages(prompt, reference_images)

            payload = {
                "model": self._image_model,
                "messages": messages,
                "max_tokens": IMAGE_MAX_TOKENS,
                "temperature": temperature,
                "modalities": ["image", "text"],
                "extra_body": {
                    "imageConfig": {
                        "aspectRatio": aspect_ratio,
                    }
                },
            }

            response = await client.post("/chat/completions", json=payload)

            # Some OpenAI-compatible proxies reject imageConfig. Retry without it.
            if response.status_code == 400 and "imageconfig" in str(response.text or "").lower():
                logger.warning(
                    "Upstream rejected imageConfig, retrying without it",
                    extra={"style": style},
                )
                fallback_payload = {**payload}
                fallback_payload.pop("extra_body", None)
                response = await client.post("/chat/completions", json=fallback_payload)

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()
            image_bytes = self._extract_image_from_response(data, style)

            logger.info(
                "Reference-aware image generated successfully",
                extra={
                    "style": style,
                    "image_size": len(image_bytes),
                    "has_references": bool(reference_images),
                },
            )
            return image_bytes, prompt

        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            raise GeminiImageGenerationError(
                message=f"HTTP ошибка при генерации изображения: {e.response.status_code}",
                details={"style": style},
                original_error=e,
            ) from e
        except Exception as e:
            raise GeminiImageGenerationError(
                message=f"Не удалось сгенерировать изображение в стиле '{style}'",
                details={"style": style},
                original_error=e,
            ) from e

    def _build_legacy_prompt(
        self,
        *,
        style: str,
        visual_concept: VisualConcept,
        reference_images: Optional[List[Union[str, ReferenceImage]]] = None,
    ) -> str:
        style_prompt = IMAGE_STYLE_PROMPTS[style].format(
            core_theme=visual_concept.core_theme,
            visual_metaphor=visual_concept.visual_metaphor,
            key_elements=", ".join(visual_concept.key_elements),
            mood=visual_concept.mood,
        )
        reference_images = _normalize_reference_images(reference_images)

        reference_block = ""
        if reference_images:
            reference_block = f"""
{GOOGLE_REFERENCE_LOCK}

REFERENCE IMAGES:
{_reference_summary(reference_images)}
""".strip()

        return f"""Generate one final illustration.

SCENE LOCK (binding):
- Render this exact scene: {visual_concept.visual_metaphor}
- Must include: {", ".join(visual_concept.key_elements[:5])}
- Composition: {visual_concept.composition}
- Lighting: {visual_concept.lighting}
- Mood: {visual_concept.mood}

{reference_block}

Fidelity rules:
- This is a fidelity task, not an exploration task.
- Do not invent a different main subject.
- Keep object count, crop, relative scale, and lighting direction.
- Translate the locked scene into the target style below.
- If the style brief contains words like "unique", "reinterpret", or "reimagine", ignore them and stay faithful to the locked scene and references.

TARGET STYLE BRIEF:
{style_prompt}
"""

    def _build_photocard_prompt(
        self,
        *,
        style: str,
        reason: Optional[str],
        message: Optional[str],
        reference_images: Optional[List[Union[str, ReferenceImage]]] = None,
    ) -> str:
        if style not in REFERENCE_AWARE_PHOTOCARD_IMAGE_STYLE_PROMPTS:
            raise GeminiImageGenerationError(
                message=f"Неизвестный photocard-стиль: {style}",
                details={"style": style},
            )

        variation = _get_photocard_variation(style)
        primary_colors, accent_colors = _sample_photocard_palette(style)

        style_template = REFERENCE_AWARE_PHOTOCARD_IMAGE_STYLE_PROMPTS[style]
        style_prompt = style_template.format(
            alter_ego=reason or "личное увлечение / роль сотрудника",
            brief=message or reason or "персональный сигнал для мозаичного тайла",
            composition=variation["composition"],
            primary_colors=", ".join(primary_colors),
            accent_colors=", ".join(accent_colors) if accent_colors else "none",
        )

        agent_overrides = _get_photocard_agent_overrides(style)
        if agent_overrides:
            style_prompt = f"{style_prompt}\n\nADDITIONAL STYLE OVERRIDES:\n{agent_overrides}"

        refs = _normalize_reference_images(reference_images)
        reference_block = ""
        if refs:
            reference_block = f"""
{GOOGLE_REFERENCE_LOCK}

REFERENCE IMAGES:
{_reference_summary(refs)}
""".strip()

        return f"""Generate one final square 1:1 vector illustration tile for the P4.0 mosaic logo.

PROJECT GOAL:
Visualize a personal hobby / personal role of a P4.0 employee in a unified graphic language.
The final image will be used as one tile inside a larger mosaic panel.

NON-NEGOTIABLE TECHNICAL LOCK:
- Square 1:1
- Illustration only; flat vector style / flat design
- Dominant central motif occupies roughly 70-80% of the frame
- Background is solid and light; prefer White (#FFFFFF) or Light Blue (#B9CDFF)
- Absolutely no letters, no numbers, no text, no logos
- Strict ban on photorealism and 3D rendering
- No gradients, no photographic texture, no painterly texture
- Use only the approved palette:
  Main: {", ".join(PHOTOCARD_BRAND_PALETTE["main"])}
  Additional accents: {", ".join(PHOTOCARD_BRAND_PALETTE["additional"])}
- No event-specific motifs (props, decorative wraps, gift-like ornaments, etc.) unless explicitly present in the reference images

{reference_block}

STYLE BRIEF:
{style_prompt}

Return image only.
"""

    async def generate_image(
        self,
        visual_concept: VisualConcept,
        style: str,
        reference_images: Optional[List[Union[str, ReferenceImage]]] = None,
        strict_reference_mode: bool = False,
    ) -> Tuple[bytes, str]:
        if style in REFERENCE_AWARE_PHOTOCARD_IMAGE_STYLE_PROMPTS:
            return await self.generate_image_direct(
                style=style,
                reason=visual_concept.core_theme,
                message=visual_concept.visual_metaphor,
                reference_images=reference_images,
                strict_reference_mode=True,
            )

        if style not in IMAGE_STYLE_PROMPTS:
            raise GeminiImageGenerationError(
                message=f"Неизвестный стиль изображения: {style}",
                details={"style": style, "available_styles": list(IMAGE_STYLE_PROMPTS.keys())},
            )

        prompt = self._build_legacy_prompt(
            style=style,
            visual_concept=visual_concept,
            reference_images=reference_images if strict_reference_mode else None,
        )

        temperature = (
            REFERENCE_PRIMARY_TEMPERATURE
            if strict_reference_mode and reference_images
            else TEXT_TEMPERATURE
        )

        return await self._post_image_request(
            style=style,
            prompt=prompt,
            aspect_ratio="2:3",
            temperature=temperature,
            reference_images=reference_images if strict_reference_mode else None,
        )

    async def generate_image_direct(
        self,
        style: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        reference_images: Optional[List[Union[str, ReferenceImage]]] = None,
        strict_reference_mode: bool = True,
        explore_variations: bool = False,
    ) -> Tuple[bytes, str]:
        # explore_variations is kept for signature compatibility, but reference-driven
        # production mode intentionally avoids creative randomness.
        _ = explore_variations

        if style in REFERENCE_AWARE_PHOTOCARD_IMAGE_STYLE_PROMPTS:
            prompt = self._build_photocard_prompt(
                style=style,
                reason=reason,
                message=message,
                reference_images=reference_images if strict_reference_mode else None,
            )

            temperature = (
                REFERENCE_PRIMARY_TEMPERATURE
                if strict_reference_mode and reference_images
                else PHOTOCARD_PRIMARY_TEMPERATURE
            )

            return await self._post_image_request(
                style=style,
                prompt=prompt,
                aspect_ratio="1:1",
                temperature=temperature,
                reference_images=reference_images if strict_reference_mode else None,
            )

        # For non-photocard legacy styles, keep the one-stage public API but
        # internally use the existing visual-concept analysis so the prompt stays
        # semantically grounded instead of using a random subject.
        visual_concept = await self.analyze_for_visual(
            recipient="сотрудник",
            reason=reason or "личный вклад",
            message=message or "внутренний корпоративный контекст",
        )
        return await self.generate_image(
            visual_concept=visual_concept,
            style=style,
            reference_images=reference_images,
            strict_reference_mode=strict_reference_mode,
        )
