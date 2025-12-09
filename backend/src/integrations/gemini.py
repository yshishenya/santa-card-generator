"""Google Gemini AI integration for text and image generation via LiteLLM proxy.

This module provides a client for interacting with Google Gemini API
through LiteLLM proxy to generate stylized greeting card text and festive images.

Features:
- 5 text styles (ode, future, haiku, newspaper, standup)
- 4 image styles (digital_art, pixel_art, space, movie)
- Text generation via gemini-2.5-flash
- Image generation via gemini-2.5-flash-image-preview
- Automatic retry on transient errors
- Comprehensive error handling
- Structured logging
"""

import logging
import base64
from typing import Optional, Any, Dict, Tuple

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

# Named constants for configuration
HTTP_TIMEOUT_SECONDS = 120.0
TEXT_MAX_TOKENS = 8192
IMAGE_MAX_TOKENS = 4096
TEXT_TEMPERATURE = 0.8
MAX_RETRY_ATTEMPTS = 3
RETRY_MIN_WAIT = 2
RETRY_MAX_WAIT = 10

from .exceptions import (
    GeminiTextGenerationError,
    GeminiImageGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
)

logger = logging.getLogger(__name__)


# Text style prompts in Russian for corporate greeting cards
# Best practices: concise, persona-first, few-shot examples, structured input
TEXT_STYLE_PROMPTS = {
    "ode": """<persona>Ты — придворный поэт с чувством юмора</persona>

<task>Преврати поздравление в торжественную оду (400-600 символов)</task>

<input>
Кому: {recipient}
От: {sender}
За что: {reason}
Текст: {message}
</input>

<example>
Input: "Спасибо за помощь с отчётом"
Output: "О, великий {recipient}! В час, когда тьма квартальных отчётов сгущалась над нашими головами, ты явился подобно лучу света средь бури! Цифры, что казались хаосом, под твоей рукой сложились в симфонию, и дедлайн был повержен!"
</example>

Пиши возвышенно, с лёгкой иронией. Упомяни {recipient}. Выведи только текст оды.""",

    "future": """<persona>Ты — историк из 2030 года</persona>

<task>Напиши ретроспективную заметку о событии декабря 2025 (350-500 символов)</task>

<input>
Герой: {recipient}
Автор благодарности: {sender}
Достижение: {reason}
Контекст: {message}
</input>

<example>
Input: "внедрение новой CRM"
Output: "2030 год. Листая архивы, понимаем: когда {recipient} в декабре 2025-го запустил новую CRM, это казалось рядовым апдейтом. Никто не знал, что именно этот момент станет точкой отсчёта новой эры продаж..."
</example>

Стиль: "мы тогда не понимали масштаб". Выведи только текст.""",

    "haiku": """<persona>Ты — мастер хайку</persona>

<task>Напиши 2-3 хайку по мотивам поздравления</task>

<input>
Адресат: {recipient}
От: {sender}
Повод: {reason}
Слова: {message}
</input>

<rules>
- Зимние образы (снег, лёд, тепло)
- Имя {recipient} минимум один раз
- Пустая строка между хайку
</rules>

<example>
Input: "за поддержку в трудный момент"
Output:
Снег кружит в ночи
{recipient} руку подал —
Путь стал светлее

Лёд на окне тает
От слов благодарности
Сердце согрето
</example>

Выведи только хайку, без пояснений.""",

    "newspaper": """<persona>Ты — журналист корпоративной газеты</persona>

<task>Напиши новостную заметку с заголовком (400-600 символов)</task>

<input>
Герой статьи: {recipient}
Источник: {sender}
Событие: {reason}
Цитата: {message}
</input>

<format>
**Заголовок: цепляющий, с именем героя**
Текст заметки в журналистском стиле
</format>

<example>
Input: "спас проект от срыва"
Output:
**{recipient}: как один человек спас квартальный проект**
Редакция выяснила подробности. Когда до дедлайна оставались часы, а ситуация казалась безнадёжной, именно {recipient} взял ответственность на себя...
</example>

Тон тёплый, но профессиональный. Выведи заголовок и текст.""",

    "standup": """<persona>Ты — добрый комик на корпоративе</persona>

<task>Напиши тёплый стендап-монолог (350-500 символов)</task>

<input>
Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}
</input>

<rules>
- Обращение на "ты"
- Шутки над ситуацией, НЕ над человеком
- Финал — искренняя благодарность
</rules>

<example>
Input: "за терпение с правками"
Output: "{recipient}, слушай, я тут посчитал — ты героически пережил 47 версий моих правок. Сорок. Семь. И ни разу не закатил глаза! Ну, может закатил, но я не видел, а значит не считается. Серьёзно, твоё терпение — это суперсила уровня Marvel. Спасибо тебе огромное!"
</example>

Выведи только монолог.""",
}


# Image style prompts for Gemini - narrative style, camera language, subject-action-scene
# Best practices: describe scene narratively, use photographic terms, be specific
IMAGE_STYLE_PROMPTS = {
    "digital_art": """Generate an image of a symbolic scene that represents this gratitude:
"{reason}" — "{message}"

The scene should be a visual metaphor. Think: what OBJECT or SCENE captures this feeling?
- Saving a project → a lighthouse beam cutting through stormy seas, guiding ships to safety
- Patience → an ancient oak tree standing serene amid swirling snow
- Creative ideas → a garden where flowers made of light bloom through fresh snow
- Support → a stone bridge arching gracefully over a misty chasm
- Leadership → a bright star at the center of a constellation, other stars orbiting it

Style: Modern digital painting with magical realism aesthetic. Warm, vibrant colors with rich saturation. Think concept art for a Pixar film.

Composition: Wide shot establishing the full scene. Dramatic lighting from a warm source (firelight, sunset, magic glow). Winter atmosphere with falling snow or frost.

Color palette: Deep midnight blues, warm amber and gold, pure snow white, touches of festive red.

Technical: High detail, painterly brushstrokes visible, atmospheric perspective with soft background.

CRITICAL: No text, letters, numbers, or writing of any kind. No realistic human faces. The image tells the story through symbols, not words.""",

    "pixel_art": """Generate an image of a retro video game victory scene representing:
"{reason}" — "{message}"

Design this like a triumphant moment in a classic 16-bit RPG. What achievement does this gratitude represent?
- Teamwork → tiny pixel heroes standing together atop a completed castle they built
- Problem solving → a maze with the exit revealed, treasure chest glowing at the end
- Mentorship → a small sprite following a glowing guide star through a snowy forest
- Hard work → pixel character planting a victory flag on a snow-covered mountain peak
- Innovation → a pixelated rocket launching from a festive winter launchpad, stars twinkling

Style: Authentic 16-bit SNES/Genesis era pixel art. Clean pixel grid, no anti-aliasing. Think Final Fantasy VI or Chrono Trigger victory screens.

Composition: Classic game scene framing. Centered subject with decorative border of snow and holiday lights. Pixel-perfect symmetry where appropriate.

Color palette: Limited to 32 colors maximum. Warm glowing yellows, cool snow blues, festive reds and greens, pixel-perfect gradients.

Technical: Each pixel intentionally placed. Clear silhouettes. Animated feel even in still image — sparkles, snow particles.

CRITICAL: No text, UI elements, health bars, or letters. Pure visual storytelling through pixel art.""",

    "space": """Generate an image of a cosmic scene that symbolizes this gratitude:
"{reason}" — "{message}"

Transform the gratitude into celestial phenomena. What would this thank-you look like written in the stars?
- Guidance → a constellation that forms the shape of a compass, golden stars connected by ethereal lines
- Bright ideas → a supernova explosion in warm gold and white, creative energy radiating outward
- Being a star → a beautiful nebula in the act of birthing new stars, cosmic creation
- Reaching goals → a spacecraft approaching a golden planet, rings of stardust like celebration confetti
- Connecting people → two galaxies gracefully spiraling toward each other, their arms intertwining

Style: Space fantasy art with ethereal, painterly quality. Think NASA imagery meets fantasy illustration. Luminous and awe-inspiring.

Composition: Deep space vista shot. Subject celestial object in golden ratio position. Depth created by distant galaxies and nearby cosmic dust.

Color palette: Deep space purples and blues, nebula pinks and magentas, stardust gold, icy comet whites.

Technical: Volumetric nebula clouds, point-light stars with subtle glow, cosmic scale with tiny details that reward close viewing.

CRITICAL: No text, constellations forming letters, or writing. No human figures. Pure cosmic visual poetry.""",

    "movie": """Generate an image of a cinematic scene capturing the emotion of:
"{reason}" — "{message}"

Frame this like the key visual from an inspiring film. What dramatic moment represents this gratitude?
- Courage → silhouette standing at cliff edge, facing a brilliant sunrise breaking through storm clouds
- Perseverance → lone figure reaching a snow-covered mountain summit, arms raised, golden light flooding the scene
- Protection → a shield catching warm light while storm rages in the background, safe glow within
- Breakthrough → massive doors swinging open to reveal blinding golden light, snow swirling through
- Inspiration → phoenix made of golden light rising against a winter night sky, embers like stars

Style: Hollywood blockbuster cinematography. Think Roger Deakins lighting meets epic adventure film. Every frame a painting.

Camera: Wide establishing shot or dramatic low angle. 35mm anamorphic lens feel with subtle lens flares. Golden hour or magic hour lighting.

Color grading: Teal and orange contrast, deep shadows with warm highlights, cinematic color science.

Technical: Volumetric light rays, atmospheric haze, shallow depth of field on edges, film grain texture.

CRITICAL: No text, titles, credits, or writing. No realistic human faces — use silhouettes, distant figures, or symbolic representations only.""",

    "hyperrealism": """Generate an image of a photorealistic still life symbolizing:
"{reason}" — "{message}"

Compose this like a high-end product photograph where objects tell the story. What tangible things represent this gratitude?
- Guidance → vintage brass compass lying on an aged leather map, needle pointing toward a golden destination marked with warm light
- Unlocking potential → ornate antique key with delicate frost crystals forming on the metal, resting on velvet
- Time and patience → elegant crystal hourglass with golden sand suspended mid-flow, surrounded by frost
- Clarity → cut crystal prism splitting a beam of winter light into a rainbow across fresh snow
- Warmth → steaming ceramic cup of cocoa with cinnamon stick, condensation on the cup, cozy knit fabric beneath

Style: Hyperrealistic photography. The viewer should question if this is a photograph. Commercial product photography quality.

Camera setup: 85mm portrait lens, f/2.8 aperture for creamy bokeh. Soft studio lighting with one warm key light. Shallow depth of field.

Technical details: Extreme texture detail — visible metal grain, fabric weave, water droplet reflections. Subtle dust particles in light beams.

Color palette: Rich warm golds, deep burgundy velvet, cool frost blues, pristine whites. Premium luxury aesthetic.

CRITICAL: Absolutely no text, engravings, labels, numbers, or writing on any object. No human hands, faces, or figures. Objects alone tell the story.""",
}


class GeminiClient:
    """Client for Google Gemini API via LiteLLM proxy.

    Provides methods for generating stylized text and images for greeting cards.
    Handles errors, retries, and logging automatically.

    Example:
        >>> client = GeminiClient(
        ...     api_key="your-key",
        ...     base_url="https://litellm.pro-4.ru/v1"
        ... )
        >>> text = await client.generate_text(
        ...     prompt="",
        ...     style="ode",
        ...     recipient="Иван Петров",
        ...     reason="отличную работу над проектом"
        ... )
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://litellm.pro-4.ru/v1",
        text_model: str = "gemini-2.5-flash",
        image_model: str = "gemini/gemini-2.5-flash-image-preview",
    ):
        """Initialize Gemini client via LiteLLM proxy.

        Args:
            api_key: LiteLLM API key
            base_url: LiteLLM proxy base URL
            text_model: Model for text generation
            image_model: Model for image generation

        Raises:
            GeminiConfigError: If API key is missing or invalid
        """
        if not api_key or not api_key.strip():
            raise GeminiConfigError(
                message="Gemini API key is required",
                missing_param="api_key",
            )

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._text_model = text_model
        self._image_model = image_model
        self._http_client: Optional[httpx.AsyncClient] = None

        logger.info(
            "Gemini client initialized (LiteLLM proxy)",
            extra={
                "base_url": self._base_url,
                "text_model": self._text_model,
                "image_model": self._image_model,
            },
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=HTTP_TIMEOUT_SECONDS,
            )
        return self._http_client

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def generate_text(
        self,
        prompt: str,
        style: str,
        recipient: str,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        sender: Optional[str] = None,
    ) -> str:
        """Generate stylized greeting text using Gemini.

        Args:
            prompt: Base prompt (usually empty, style template is used)
            style: Text style code (ode, future, haiku, newspaper, standup)
            recipient: Name of the person receiving the greeting
            reason: Reason for gratitude (optional)
            message: Additional message from sender (optional)
            sender: Name of the person sending the greeting (optional)

        Returns:
            Generated text content

        Raises:
            GeminiTextGenerationError: If generation fails
            GeminiRateLimitError: If rate limit is exceeded

        Example:
            >>> text = await client.generate_text(
            ...     prompt="",
            ...     style="haiku",
            ...     recipient="Анна Смирнова",
            ...     reason="успешный запуск нового продукта",
            ...     message="С Новым Годом!",
            ...     sender="Иван Петров"
            ... )
        """
        if style not in TEXT_STYLE_PROMPTS:
            raise GeminiTextGenerationError(
                message=f"Неизвестный стиль текста: {style}",
                details={"style": style, "available_styles": list(TEXT_STYLE_PROMPTS.keys())},
            )

        # Build the prompt from template
        style_template = TEXT_STYLE_PROMPTS[style]
        full_prompt = style_template.format(
            recipient=recipient,
            reason=reason or "вклад в развитие компании",
            message=message or "Спасибо за работу!",
            sender=sender or "коллеги",
        )

        logger.debug(
            f"Generating text with style '{style}' for recipient",
            extra={
                "style": style,
                "has_reason": bool(reason),
                "has_message": bool(message),
            },
        )

        try:
            client = await self._get_client()

            # OpenAI-compatible chat completions request
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self._text_model,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ],
                    "max_tokens": TEXT_MAX_TOKENS,
                    "temperature": TEXT_TEMPERATURE,
                },
            )

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()

            # Extract text from response
            if not data.get("choices"):
                raise GeminiTextGenerationError(
                    message="Gemini API вернул пустой ответ",
                    details={"style": style},
                )

            generated_text = data["choices"][0]["message"]["content"].strip()

            logger.info(
                f"Text generated successfully: {len(generated_text)} characters",
                extra={
                    "style": style,
                    "text_length": len(generated_text),
                },
            )

            return generated_text

        except GeminiTextGenerationError:
            raise
        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during text generation: {e}",
                extra={"status_code": e.response.status_code},
                exc_info=True,
            )
            raise GeminiTextGenerationError(
                message=f"HTTP ошибка при генерации текста: {e.response.status_code}",
                details={"style": style},
                original_error=e,
            )
        except Exception as e:
            logger.error(
                f"Text generation failed: {e}",
                extra={
                    "style": style,
                    "recipient": recipient,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Check for rate limit errors
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise GeminiRateLimitError(original_error=e)

            raise GeminiTextGenerationError(
                message=f"Не удалось сгенерировать текст в стиле '{style}'",
                details={"style": style},
                original_error=e,
            )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
    )
    async def generate_image(
        self,
        recipient: str,
        reason: Optional[str],
        message: Optional[str],
        style: str,
    ) -> Tuple[bytes, str]:
        """Generate a festive image using the Gemini image model.
        
        This function constructs a prompt based on the recipient's name, reason for
        gratitude, and a personal message. It then sends a request to the Gemini image
        model to generate an image in the specified style. The function handles various
        exceptions, including rate limits and HTTP errors, ensuring robust error
        management.
        
        Args:
            recipient (str): Name of the person receiving the greeting.
            reason (Optional[str]): Reason for gratitude (used in prompt context).
            message (Optional[str]): Personal message from sender (used for visual metaphor).
            style (str): Image style code (digital_art, pixel_art, space, movie, hyperrealism).
        
        Returns:
            Tuple[bytes, str]: A tuple containing image_bytes in PNG format and the prompt used.
        
        Raises:
            GeminiImageGenerationError: If generation fails.
            GeminiRateLimitError: If rate limit is exceeded.
        """
        if style not in IMAGE_STYLE_PROMPTS:
            raise GeminiImageGenerationError(
                message=f"Неизвестный стиль изображения: {style}",
                details={"style": style, "available_styles": list(IMAGE_STYLE_PROMPTS.keys())},
            )

        # Build the prompt from template
        style_template = IMAGE_STYLE_PROMPTS[style]
        full_prompt = style_template.format(
            recipient=recipient,
            reason=reason or "профессиональные достижения",
            message=message or "Спасибо за отличную работу!",
        )

        logger.debug(
            f"Generating image with style '{style}' for recipient",
            extra={
                "style": style,
                "has_reason": bool(reason),
            },
        )

        try:
            client = await self._get_client()

            # Request image generation via chat completions
            # Gemini image models use modalities parameter for image generation
            # Using 3:2 aspect ratio for horizontal A6 postcard format (148x105mm)
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self._image_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Generate an image based on this description:\n\n{full_prompt}"
                        }
                    ],
                    "max_tokens": IMAGE_MAX_TOKENS,
                    "modalities": ["image", "text"],
                    "extra_body": {
                        "imageConfig": {
                            "aspectRatio": "3:2"
                        }
                    },
                },
            )

            if response.status_code == 429:
                raise GeminiRateLimitError(original_error=Exception("Rate limit exceeded"))

            response.raise_for_status()
            data = response.json()

            # Extract image from response
            image_bytes = self._extract_image_from_response(data, style)

            logger.info(
                f"Image generated successfully: {len(image_bytes)} bytes",
                extra={
                    "style": style,
                    "image_size": len(image_bytes),
                },
            )

            return image_bytes, full_prompt

        except GeminiImageGenerationError:
            raise
        except GeminiRateLimitError:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error during image generation: {e}",
                extra={"status_code": e.response.status_code},
                exc_info=True,
            )
            raise GeminiImageGenerationError(
                message=f"HTTP ошибка при генерации изображения: {e.response.status_code}",
                details={"style": style},
                original_error=e,
            )
        except Exception as e:
            logger.error(
                f"Image generation failed: {e}",
                extra={
                    "style": style,
                    "recipient": recipient,
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            # Check for rate limit errors
            error_str = str(e).lower()
            if "rate limit" in error_str or "quota" in error_str:
                raise GeminiRateLimitError(original_error=e)

            raise GeminiImageGenerationError(
                message=f"Не удалось сгенерировать изображение в стиле '{style}'",
                details={"style": style},
                original_error=e,
            )

    def _extract_image_from_response(self, data: Dict[str, Any], style: str) -> bytes:
        """Extract image bytes from API response.

        Handles multiple response formats:
        1. LiteLLM format: message.images[0]["image_url"]["url"]
        2. Direct base64 in message content
        3. Image URL in response
        4. Inline data with base64 encoding

        Args:
            data: API response data
            style: Image style (for error context)

        Returns:
            Image bytes in PNG format

        Raises:
            GeminiImageGenerationError: If image extraction fails
        """
        if not data.get("choices"):
            raise GeminiImageGenerationError(
                message="API вернул пустой ответ",
                details={"style": style},
            )

        choice = data["choices"][0]
        message = choice.get("message", {})

        # Format 0: LiteLLM Gemini image format - message.images array
        images = message.get("images", [])
        if images and len(images) > 0:
            image_obj = images[0]
            if isinstance(image_obj, dict) and "image_url" in image_obj:
                url = image_obj["image_url"]
                if isinstance(url, dict):
                    url = url.get("url", "")
                if url.startswith("data:image"):
                    base64_data = url.split("base64,")[1]
                    return base64.b64decode(base64_data)

        content = message.get("content", "")

        # Try to extract base64 image from content
        # Format 1: Direct base64 string
        if content and not content.startswith("http"):
            try:
                # Check if it's a base64 image
                if "base64," in content:
                    # data:image/png;base64,... format
                    base64_data = content.split("base64,")[1]
                else:
                    # Raw base64
                    base64_data = content

                # Clean and decode
                base64_data = base64_data.strip()
                image_bytes = base64.b64decode(base64_data)

                # Verify it's valid image data (PNG starts with specific bytes)
                if image_bytes[:4] == b"\x89PNG" or image_bytes[:2] == b"\xff\xd8":
                    return image_bytes

            except (ValueError, base64.binascii.Error) as e:
                logger.debug(
                    "Failed to decode base64 from direct content, trying other formats",
                    extra={"error": str(e), "style": style},
                )

        # Format 2: Check for image_url in content parts
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if "image_url" in part:
                        url = part["image_url"]
                        if isinstance(url, dict):
                            url = url.get("url", "")
                        if url.startswith("data:image"):
                            base64_data = url.split("base64,")[1]
                            return base64.b64decode(base64_data)
                    if "inline_data" in part:
                        inline = part["inline_data"]
                        if "data" in inline:
                            return base64.b64decode(inline["data"])

        # Format 3: Check message for image data
        if "image" in message:
            image_data = message["image"]
            if isinstance(image_data, str):
                return base64.b64decode(image_data)
            if isinstance(image_data, dict) and "data" in image_data:
                return base64.b64decode(image_data["data"])

        # Format 4: Check for data field directly
        if "data" in data:
            for item in data.get("data", []):
                if "b64_json" in item:
                    return base64.b64decode(item["b64_json"])
                if "url" in item and item["url"].startswith("data:"):
                    base64_data = item["url"].split("base64,")[1]
                    return base64.b64decode(base64_data)

        # Log detailed response structure for debugging
        content_preview = str(content)[:500] if content else "empty"
        logger.error(
            f"Failed to extract image from response. "
            f"style={style}, response_keys={list(data.keys()) if data else []}, "
            f"choice_keys={list(choice.keys()) if choice else []}, "
            f"message_keys={list(message.keys()) if message else []}, "
            f"content_type={type(content).__name__}, has_images={bool(images)}, "
            f"content_preview={content_preview}"
        )
        raise GeminiImageGenerationError(
            message="Не удалось извлечь изображение из ответа API",
            details={
                "style": style,
                "response_keys": list(data.keys()) if data else [],
                "message_keys": list(message.keys()) if message else [],
            },
        )

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("Gemini client closed")
