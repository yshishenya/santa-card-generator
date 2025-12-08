# API Standards

## Project: Santa — AI-генератор корпоративных открыток

## Naming Conventions
- Endpoints use lowercase with underscores: `/api/v1/cards/generate`, `/api/v1/employees`
- Resource-based URLs, not action-based (exception: generate, regenerate for AI operations)
- API versioning in URL: `/api/v1/...`

## Request/Response Format
- All requests/responses use JSON
- File uploads use `multipart/form-data`
- Date formats: ISO 8601 (YYYY-MM-DDTHH:mm:ssZ)
- All dates in UTC timezone

## Standard Response Structure

### Success Response
```json
{
  "success": true,
  "data": {
    // response payload
  },
  "meta": {
    "timestamp": "2024-10-19T12:00:00Z",
    "version": "v1"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message in Russian",
    "details": {
      "field": "additional context"
    }
  },
  "meta": {
    "timestamp": "2024-10-19T12:00:00Z",
    "version": "v1"
  }
}
```

## Santa API Endpoints

### Public Endpoints (no auth)

#### Cards API
```
POST /api/v1/cards/generate     # Generate card (text + image)
POST /api/v1/cards/regenerate   # Regenerate text or image
POST /api/v1/cards/send         # Send card to Telegram
```

#### Employees API
```
GET  /api/v1/employees          # Get employee list for autocomplete
```

### Health Check
```
GET  /health                    # Service health check
```

**Note**: Админ-панель не требуется. Список сотрудников загружается разово из Excel файла.

## FastAPI Router Structure

### Example Router Setup
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/api/v1/cards", tags=["cards"])

@router.post("/generate", response_model=CardGenerationResponse)
async def generate_card(
    request: CardGenerationRequest,
    generation_service: GenerationService = Depends(get_generation_service)
) -> CardGenerationResponse:
    """
    Generate a new greeting card with AI-generated text and image.

    - **recipient**: Name of the card recipient (required)
    - **sender**: Name of the sender (optional, anonymous if not provided)
    - **reason**: Short reason for gratitude (optional, max 150 chars)
    - **message**: Gratitude message (optional, max 1000 chars)
    - **enhance_text**: Whether to enhance text with AI
    - **text_style**: Style for text enhancement (required if enhance_text=true)
    - **image_style**: Style for generated image (required)
    """
    try:
        result = await generation_service.generate(request)
        return CardGenerationResponse(
            success=True,
            data=result
        )
    except GenerationError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## External API Integration Standards

### Base Class for Integrations
All integrations with external APIs must follow this pattern:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

class BaseAPIIntegration(ABC):
    """Base class for all external API integrations"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is available."""
        pass

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

### Gemini Integration Pattern
```python
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

class GeminiClient(BaseAPIIntegration):
    """Client for Google Gemini API."""

    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
        genai.configure(api_key=api_key)
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.image_model = genai.GenerativeModel('gemini-pro-vision')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_text(
        self,
        prompt: str,
        style: TextStyle
    ) -> str:
        """Generate styled text using Gemini."""
        styled_prompt = self._build_text_prompt(prompt, style)
        response = await self.text_model.generate_content_async(styled_prompt)
        return response.text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_image(
        self,
        prompt: str,
        style: ImageStyle
    ) -> bytes:
        """Generate image using Gemini/Imagen."""
        image_prompt = self._build_image_prompt(prompt, style)
        # Implementation depends on actual Gemini image generation API
        ...

    async def health_check(self) -> bool:
        """Check if Gemini API is available."""
        try:
            response = await self.text_model.generate_content_async("test")
            return True
        except Exception:
            return False
```

### Telegram Integration Pattern
```python
from telegram import Bot
from telegram.constants import ParseMode

class TelegramClient(BaseAPIIntegration):
    """Client for Telegram Bot API."""

    def __init__(
        self,
        bot_token: str,
        chat_id: int,
        topic_id: int
    ):
        super().__init__(api_key=bot_token)
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.topic_id = topic_id

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send_card(
        self,
        image: bytes,
        caption: str
    ) -> int:
        """Send card to Telegram thread."""
        result = await self.bot.send_photo(
            chat_id=self.chat_id,
            message_thread_id=self.topic_id,
            photo=image,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )
        return result.message_id

    async def health_check(self) -> bool:
        """Check if Telegram bot is available."""
        try:
            await self.bot.get_me()
            return True
        except Exception:
            return False
```

## Retry Logic
- Use exponential backoff for retry attempts
- Maximum 3 attempts for transient errors (5xx, timeout)
- Do not retry for client errors (4xx)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
```

## Authentication

**Аутентификация не требуется** — все эндпоинты публичные.

- No authentication for any endpoints
- No rate limiting in MVP (can be added later)
- Employee list is pre-loaded from JSON file

## Data Validation
- Use Pydantic models for all request/response
- Validate input data at the API endpoint level
- Explicitly define types for all fields

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

class TextStyle(str, Enum):
    ODE = "ode"
    FUTURE_REPORT = "future"
    HAIKU = "haiku"
    NEWSPAPER = "newspaper"
    STANDUP = "standup"

class ImageStyle(str, Enum):
    DIGITAL_ART = "digital_art"
    PIXEL_ART = "pixel_art"
    SPACE = "space"
    MOVIE = "movie"

class CardGenerationRequest(BaseModel):
    """Request model for card generation."""
    recipient: str = Field(..., min_length=1, max_length=100)
    sender: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = Field(None, max_length=150)
    message: Optional[str] = Field(None, max_length=1000)
    enhance_text: bool = False
    text_style: Optional[TextStyle] = None
    image_style: ImageStyle

    @field_validator('recipient')
    @classmethod
    def recipient_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Имя получателя не может быть пустым')
        return v.strip()

    @field_validator('text_style')
    @classmethod
    def validate_text_style(cls, v: Optional[TextStyle], info) -> Optional[TextStyle]:
        if info.data.get('enhance_text') and v is None:
            raise ValueError('Выберите стиль текста при включенном улучшении')
        return v
```

## Logging Standards
- Log all external API requests
- Include correlation ID for tracing
- Do not log sensitive data (API keys, personal info)

```python
import logging
import uuid

logger = logging.getLogger(__name__)

async def generate_card(request: CardGenerationRequest) -> CardGenerationResponse:
    correlation_id = str(uuid.uuid4())

    logger.info(
        "Card generation started",
        extra={
            "correlation_id": correlation_id,
            "recipient": request.recipient,
            "image_style": request.image_style,
            "enhance_text": request.enhance_text
        }
    )

    try:
        result = await _do_generation(request)
        logger.info(
            "Card generation completed",
            extra={"correlation_id": correlation_id}
        )
        return result
    except Exception as e:
        logger.error(
            f"Card generation failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise
```

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Health Check Endpoint

```python
@router.get("/health")
async def health_check(
    gemini: GeminiClient = Depends(get_gemini_client),
    telegram: TelegramClient = Depends(get_telegram_client)
) -> Dict[str, Any]:
    """Check service health."""
    return {
        "status": "healthy",
        "services": {
            "gemini": await gemini.health_check(),
            "telegram": await telegram.health_check()
        }
    }
```

---

**Last Updated**: 2023-11-26
**Project**: Santa
