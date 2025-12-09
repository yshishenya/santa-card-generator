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
TEXT_STYLE_PROMPTS = {
    "ode": """Ты — великий придворный поэт, мастер торжественной оды.

Задача: Напиши торжественную оду в честь сотрудника {recipient}.

Контекст:
- За что благодарим: {reason}
- Дополнительное сообщение: {message}

Требования:
1. Стиль: возвышенный, торжественный, но с легким юмором
2. Длина: 500-800 символов
3. Используй поэтические обороты, но без излишнего пафоса
4. Обязательно упомяни имя получателя {recipient} в тексте
5. Новогодняя/рождественская тематика приветствуется
6. Избегай клише типа "незаменимый сотрудник"
7. Пиши от первого лица (я/мы благодарим)

Пример стиля (не копируй дословно):
"О, {recipient}, светило наших офисных просторов! В этот предновогодний час спешим воздать тебе хвалу за труды твои ратные..."

Создай ОДНУ оду, без вариантов и дополнительных комментариев.""",
    "future": """Ты — журналист из будущего, пишущий ретроспективный отчет о достижениях.

Задача: Напиши отчет из 2025 года о том, как {recipient} изменил(а) компанию.

Контекст:
- За что благодарим: {reason}
- Дополнительное сообщение: {message}

Требования:
1. Стиль: как будто пишешь из будущего, оглядываясь назад на 2024 год
2. Длина: 400-600 символов
3. Используй конструкции "благодаря {recipient}, мы смогли...", "именно в конце 2024 года..."
4. Упомяни конкретные достижения (даже если в шутливой форме)
5. Новогодняя тематика: как новогодние праздники стали поворотным моментом
6. Оптимистичный тон, вера в светлое будущее
7. Пиши от лица компании (мы/наша команда)

Пример стиля (не копируй дословно):
"2025 год. Оглядываясь назад, мы понимаем: именно зимой 2024, когда {recipient} {reason}, началась новая эра в истории нашей компании..."

Создай ОДИН отчет, без вариантов и комментариев.""",
    "haiku": """Ты — мастер хайку, поэт минималист.

Задача: Напиши хайку (или несколько связанных хайку) для {recipient}.

Контекст:
- За что благодарим: {reason}
- Дополнительное сообщение: {message}

Требования:
1. Стиль: лаконичный, образный, философский
2. Длина: 2-4 хайку (всего 200-400 символов)
3. Классическая структура хайку: 5-7-5 слогов (допускается небольшое отклонение в русском языке)
4. Упомяни имя {recipient} хотя бы один раз
5. Зимняя/новогодняя образность (снег, звезды, огни)
6. Избегай прямолинейности, используй метафоры
7. Каждое хайку с новой строки, пустая строка между хайку

Пример стиля (не копируй):
Снег кружит над крышей
{recipient} — как маяк —
Светит сквозь метель

Новый год стучится
Благодарность наша —
Теплее огня

Создай 2-4 хайку, без дополнительных комментариев.""",
    "newspaper": """Ты — журналист корпоративной газеты "Вестник Компании".

Задача: Напиши заметку о {recipient} для предновогоднего выпуска.

Контекст:
- За что благодарим: {reason}
- Дополнительное сообщение: {message}

Требования:
1. Стиль: журналистский, информативный, но теплый
2. Длина: 500-700 символов
3. Структура: яркий заголовок + основной текст
4. Используй журналистские приемы: цитаты (можно вымышленные от коллег), факты
5. Упомяни {recipient} в заголовке или первом абзаце
6. Новогодняя рубрика: "Герои уходящего года" или "Звезды 2024"
7. Позитивный, вдохновляющий тон
8. Без излишнего пафоса, живой язык

Пример структуры (не копируй):
**Звезда декабря: {recipient} показывает класс**

В преддверии новогодних праздников редакция "Вестника" традиционно подводит итоги года. И сегодня наш герой — {recipient}...

Создай ОДНУ заметку с заголовком, без вариантов.""",
    "standup": """Ты — стендап-комик на корпоративе, дружелюбный и остроумный.

Задача: Напиши дружеский стендап-монолог про {recipient}.

Контекст:
- За что благодарим: {reason}
- Дополнительное сообщение: {message}

Требования:
1. Стиль: легкий, дружеский юмор, без сарказма и обидных шуток
2. Длина: 400-600 символов
3. Обращайся к {recipient} напрямую (на "ты")
4. Используй юмор, но с теплотой и благодарностью
5. Новогодняя тематика: корпоратив, елка, подарки
6. Избегай профессиональных стереотипов
7. Финал — искренняя благодарность

Пример стиля (не копируй):
"{recipient}, друг, помнишь, как в начале года мы думали, что {reason}? А ты взял и сделал это! Коллеги до сих пор в шоке... В хорошем смысле!"

Создай ОДИН монолог, без вариантов и комментариев.""",
}


# Image style prompts in English for Gemini image generation
IMAGE_STYLE_PROMPTS = {
    "digital_art": """Create a vibrant digital painting for a corporate Christmas greeting card.

Subject: Celebrating in a festive winter setting

Requirements:
1. Style: Modern digital art, vibrant colors, professional quality
2. Scene: Winter wonderland with Christmas/New Year elements
3. Mood: Warm, celebratory, inspiring
4. Elements to include:
   - Festive decorations (lights, ornaments, snowflakes)
   - Corporate/office elements subtly integrated
   - Warm color palette: reds, golds, blues, whites
5. Composition: Balanced, eye-catching, suitable for a greeting card
6. NO TEXT in the image
7. NO realistic human faces or identifiable people
8. Professional and tasteful, suitable for workplace

Additional context: {reason}

Create a beautiful, festive digital painting that captures the spirit of gratitude and celebration.""",
    "pixel_art": """Create a retro pixel art image for a corporate Christmas greeting card.

Subject: Festive pixel art celebration

Requirements:
1. Style: 8-bit/16-bit retro pixel art, reminiscent of classic video games
2. Color palette: Limited palette (16-32 colors), vibrant but not garish
3. Scene: Winter/Christmas themed office or celebration scene
4. Elements to include:
   - Pixelated Christmas tree with gifts
   - Snow falling (simple pixel snow)
   - Festive lights or decorations
   - Office/workspace elements in pixel style
5. Mood: Nostalgic, fun, cheerful
6. NO TEXT in the image
7. Clear pixel grid, authentic retro aesthetic
8. Professional quality despite retro style

Additional context: {reason}

Create charming pixel art that combines workplace appreciation with holiday cheer.""",
    "space": """Create a cosmic space fantasy image for a corporate Christmas greeting card.

Subject: Spectacular space celebration setting

Requirements:
1. Style: Space fantasy, cosmic, ethereal
2. Scene: Beautiful nebula or galaxy with Christmas/winter elements
3. Elements to include:
   - Colorful nebula clouds (purples, blues, golds)
   - Stars and cosmic lights resembling Christmas lights
   - Snowflakes made of stardust
   - Abstract representation of celebration/achievement
4. Mood: Awe-inspiring, majestic, optimistic
5. Color palette: Deep blues, purples, gold, white, cosmic colors
6. NO TEXT in the image
7. NO realistic human figures
8. Professional quality, suitable for corporate use

Additional context: {reason}

Create a breathtaking cosmic scene that symbolizes reaching for the stars and celebrating achievements.""",
    "movie": """Create a cinematic movie poster style image for a corporate greeting card.

Subject: Epic movie poster celebrating contributions

Requirements:
1. Style: Cinematic, dramatic lighting, movie poster aesthetic
2. Genre inspiration: Feel-good drama or inspiring adventure
3. Scene: Dramatic winter/holiday scene with professional elements
4. Elements to include:
   - Cinematic lighting (golden hour or dramatic shadows)
   - Winter/Christmas atmosphere
   - Sense of achievement and celebration
   - Corporate/professional context
5. Mood: Inspiring, epic, heartwarming
6. Color grading: Cinematic color palette (teals, oranges, deep blues)
7. NO TEXT in the image
8. NO realistic faces or identifiable people
9. Professional quality, could be a real movie poster

Additional context: {reason}

Create an epic, cinematic image that makes the recipient feel like the hero of their own inspiring story.""",
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
    ) -> str:
        """Generate stylized greeting text using Gemini.

        Args:
            prompt: Base prompt (usually empty, style template is used)
            style: Text style code (ode, future, haiku, newspaper, standup)
            recipient: Name of the person receiving the greeting
            reason: Reason for gratitude (optional)
            message: Additional message from sender (optional)

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
            ...     message="С Новым Годом!"
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
