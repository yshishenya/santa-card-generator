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
# Context: "Профессионалы 4.0" platform for professional excellence recognition
TEXT_STYLE_PROMPTS = {
    "ode": """Перепиши это поздравление в стиле торжественной оды для платформы «Профессионалы 4.0».

Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}

Стиль: возвышенный слог, поэтические обороты, лёгкая ирония. Как придворный поэт на церемонии награждения профессионалов.

Пример трансформации:
Было: "Спасибо за помощь с отчётом"
Стало: "О, {recipient}! Когда тьма квартальных отчётов сгущалась над нами, ты явился как луч света! Благодаря твоей помощи, цифры сложились в симфонию, а дедлайн был повержен!"

Теперь перепиши в этом стиле. 400-600 символов. Упомяни {recipient}. Только текст, без комментариев.""",

    "future": """Перепиши это поздравление как статью из 2030 года — будто оглядываешься на исторический момент для платформы «Профессионалы 4.0».

Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}

Стиль: ретроспектива, восхищение, "мы тогда ещё не знали, что это изменит всё".

Пример трансформации:
Было: "Спасибо за новую систему учёта"
Стало: "2030 год. Оглядываясь назад, мы понимаем: когда {recipient} в декабре 2025-го внедрил систему учёта, это казалось рутиной. Но именно с этого началась новая эра. Мы ещё не знали, что этот шаг приведёт к..."

Теперь перепиши в этом стиле. 350-500 символов. Только текст.""",

    "haiku": """Вырази суть этого поздравления в 2-3 хайку для платформы «Профессионалы 4.0».

Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}

Правила: зимние образы, имя {recipient} хотя бы раз, между хайку пустая строка.

Пример:
Было: "Спасибо за поддержку в трудный момент"
Стало:
Снег падает тихо
{recipient} рядом был —
Теплее зимы

Только хайку, без комментариев.""",

    "newspaper": """Перепиши это поздравление как новостную заметку для корпоративной газеты «Профессионалы 4.0».

Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}

Формат: цепляющий заголовок + текст заметки. Стиль — журналистский, но тёплый.

Пример:
Было: "Спасибо что вытянул проект"
Стало:
**{recipient} спасает проект в последний момент: как это было**
Наш корреспондент выяснил подробности. Когда казалось, что сроки сорваны...

Теперь напиши заметку про {reason}. 400-600 символов. Только текст.""",

    "standup": """Перепиши это поздравление как дружеский стендап-монолог на корпоративе «Профессионалы 4.0».

Кому: {recipient}
От кого: {sender}
За что: {reason}
Послание: {message}

Стиль: тёплый юмор, обращение на "ты", шутки над ситуацией (не над человеком!), искренний финал.

Пример:
Было: "Спасибо за терпение с моими правками"
Стало: "{recipient}, слушай, я посчитал — ты пережил 47 версий моих правок и ни разу не закатил глаза. Ну, может, закатил, но я не видел. Серьёзно, твоё терпение — это суперсила. Спасибо тебе!"

Теперь напиши монолог. 350-500 символов. Только текст.""",
}


# Image style prompts in English for Gemini image generation
# Context: "Профессионалы 4.0" platform for professional excellence recognition
IMAGE_STYLE_PROMPTS = {
    "digital_art": """Create a festive digital painting for "Professionals 4.0" platform.

Achievement being celebrated: {reason}

Style: Modern digital art, warm vibrant colors, professional quality.
Scene: Winter wonderland with Christmas lights, professional excellence symbols.
Mood: Celebration of professional achievement and gratitude.
Colors: Rich reds, warm golds, snow whites, deep blues.

STRICT RULES:
- ABSOLUTELY NO text, letters, numbers, or writing of any kind
- NO realistic human faces
- Use visual metaphors: trophies, stars, laurels, ascending paths

Create a beautiful holiday scene celebrating professional excellence.""",

    "pixel_art": """Create retro pixel art for "Professionals 4.0" platform celebration.

Achievement being celebrated: {reason}

Style: 8-bit/16-bit video game aesthetic, like classic NES/SNES games.
Scene: Festive winter pixel scene with Christmas tree, trophy, victory elements.
Mood: Nostalgic, triumphant — like completing a challenging level.
Palette: 16-32 vibrant colors, clear pixel grid.

STRICT RULES:
- ABSOLUTELY NO text, letters, numbers, or writing of any kind
- Include: pixelated trophy, stars, holiday elements
- Victory screen aesthetic

Create charming pixel art celebrating professional achievement.""",

    "space": """Create a cosmic scene for "Professionals 4.0" platform.

Achievement being celebrated: {reason}

Style: Space fantasy, ethereal nebulae, cosmic grandeur.
Scene: Galaxy or nebula with stars forming celebration patterns.
Mood: Awe-inspiring, reaching for the stars, unlimited potential.
Colors: Deep purples, cosmic blues, golden starlight, nebula pinks.

STRICT RULES:
- ABSOLUTELY NO text, letters, numbers, or writing of any kind
- NO human figures
- Stars should form festive, celebratory patterns

Create a breathtaking cosmic scene symbolizing stellar achievement.""",

    "movie": """Create a cinematic scene for "Professionals 4.0" hero moment.

Achievement being celebrated: {reason}

Style: Movie poster aesthetic, dramatic cinematic lighting.
Genre: Inspiring drama about professional triumph.
Scene: Epic moment of victory with winter/holiday atmosphere.
Colors: Cinematic color grading — teals, warm oranges, deep blues, golden highlights.

STRICT RULES:
- ABSOLUTELY NO text, titles, or writing of any kind
- NO realistic human faces — use silhouettes or abstract figures
- Dramatic lighting: golden hour, lens flares, volumetric light

Create an epic scene of professional triumph.""",

    "hyperrealism": """Create a hyperrealistic still life for "Professionals 4.0" platform.

Achievement being celebrated: {reason}

Style: Photorealistic, hyperrealism, extreme detail and texture.
Scene: Elegant desk or podium with professional achievement symbols.
Elements: Crystal trophy, golden medal, laurel wreath, premium materials.
Lighting: Soft studio lighting, beautiful reflections, depth of field.
Colors: Rich golds, deep burgundy, emerald green, pristine whites.

STRICT RULES:
- ABSOLUTELY NO text, letters, numbers, engravings, or writing of any kind
- NO human figures or faces
- Focus on textures: polished metal, crystal, velvet, wood grain
- Premium, luxurious aesthetic

Create a stunning hyperrealistic image of professional excellence symbols.""",
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
        style: str,
    ) -> Tuple[bytes, str]:
        """Generate festive image using Gemini image model.

        Args:
            recipient: Name of the person receiving the greeting
            reason: Reason for gratitude (used in prompt context)
            style: Image style code (digital_art, pixel_art, space, movie)

        Returns:
            Tuple of (image_bytes, prompt_used) where image_bytes is PNG format

        Raises:
            GeminiImageGenerationError: If generation fails
            GeminiRateLimitError: If rate limit is exceeded

        Example:
            >>> image_bytes, prompt = await client.generate_image(
            ...     recipient="Петр Иванов",
            ...     reason="инновационные идеи",
            ...     style="space"
            ... )
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
            reason=reason or "outstanding contributions",
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
