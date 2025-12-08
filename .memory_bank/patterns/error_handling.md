# Error Handling Patterns

## Project: Santa — AI-генератор корпоративных открыток

## Philosophy
- Fail fast and explicitly
- Always log errors with context
- User-facing errors should be actionable and in Russian
- Never expose internal implementation details to users
- Use structured error responses

## Error Categories

### 1. Validation Errors (4xx)
User input issues, bad requests

### 2. Authentication Errors (401, 403)
Invalid credentials, missing token, insufficient permissions

### 3. External Integration Errors
Gemini API failures, Telegram send errors

### 4. System Errors (5xx)
Internal failures, service unavailable

---

## Implementation Pattern

### Base Exception Hierarchy

```python
from typing import Dict, Any, Optional

class SantaError(Exception):
    """Base exception class for all Santa application errors."""

    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API response."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details
        }
```

### Validation Errors

```python
class ValidationError(SantaError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class RecipientNotFoundError(ValidationError):
    """Raised when recipient is not in employee list."""

    def __init__(self, recipient: str):
        super().__init__(
            message=f"Сотрудник '{recipient}' не найден в списке",
            field="recipient"
        )
        self.code = "RECIPIENT_NOT_FOUND"


class InvalidFileFormatError(ValidationError):
    """Raised when uploaded file format is invalid."""

    def __init__(self, filename: str, allowed_formats: list[str]):
        super().__init__(
            message=f"Неподдерживаемый формат файла. Используйте: {', '.join(allowed_formats)}",
            field="file"
        )
        self.code = "INVALID_FILE_FORMAT"
        self.details["filename"] = filename
        self.details["allowed_formats"] = allowed_formats
```

### External Integration Errors

**Note**: Аутентификация не используется в проекте — админ-панель отсутствует.

```python
class ExternalAPIError(SantaError):
    """Base class for external API errors."""

    def __init__(
        self,
        message: str,
        service: str,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code="EXTERNAL_API_ERROR",
            details={
                "service": service,
                "original_error": str(original_error) if original_error else None
            }
        )


class GeminiAPIError(ExternalAPIError):
    """Raised when Gemini API call fails."""

    def __init__(
        self,
        operation: str,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=f"Ошибка генерации {operation}. Попробуйте еще раз",
            service="gemini",
            original_error=original_error
        )
        self.code = "GEMINI_API_ERROR"
        self.details["operation"] = operation


class GeminiTextGenerationError(GeminiAPIError):
    """Raised when text generation fails."""

    def __init__(self, original_error: Optional[Exception] = None):
        super().__init__(
            operation="текста",
            original_error=original_error
        )
        self.code = "GEMINI_TEXT_GENERATION_ERROR"


class GeminiImageGenerationError(GeminiAPIError):
    """Raised when image generation fails."""

    def __init__(self, original_error: Optional[Exception] = None):
        super().__init__(
            operation="изображения",
            original_error=original_error
        )
        self.code = "GEMINI_IMAGE_GENERATION_ERROR"


class TelegramError(ExternalAPIError):
    """Raised when Telegram API call fails."""

    def __init__(
        self,
        message: str = "Не удалось отправить открытку в Telegram",
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            service="telegram",
            original_error=original_error
        )
        self.code = "TELEGRAM_ERROR"


class TelegramSendError(TelegramError):
    """Raised when sending message to Telegram fails."""

    def __init__(self, original_error: Optional[Exception] = None):
        super().__init__(
            message="Не удалось отправить открытку в Telegram. Попробуйте позже",
            original_error=original_error
        )
        self.code = "TELEGRAM_SEND_ERROR"


class TelegramConfigError(TelegramError):
    """Raised when Telegram is not configured."""

    def __init__(self, missing_config: str):
        super().__init__(
            message="Telegram не настроен. Обратитесь к администратору",
            original_error=None
        )
        self.code = "TELEGRAM_CONFIG_ERROR"
        self.details["missing_config"] = missing_config
```

### Generation Errors

```python
class GenerationError(SantaError):
    """Base class for generation-related errors."""
    pass


class RegenerationLimitExceededError(GenerationError):
    """Raised when regeneration limit is exceeded."""

    def __init__(self, content_type: str, max_attempts: int):
        super().__init__(
            message=f"Достигнут лимит перегенераций {content_type} ({max_attempts} попыток)",
            code="REGENERATION_LIMIT_EXCEEDED",
            details={
                "content_type": content_type,
                "max_attempts": max_attempts
            }
        )


class GenerationNotFoundError(GenerationError):
    """Raised when generation session is not found."""

    def __init__(self, generation_id: str):
        super().__init__(
            message="Сессия генерации не найдена или истекла",
            code="GENERATION_NOT_FOUND",
            details={"generation_id": generation_id}
        )


class VariantNotFoundError(GenerationError):
    """Raised when selected variant is not found."""

    def __init__(self, variant_id: str, variant_type: str):
        super().__init__(
            message=f"Выбранный вариант {variant_type} не найден",
            code="VARIANT_NOT_FOUND",
            details={
                "variant_id": variant_id,
                "variant_type": variant_type
            }
        )
```

---

## Error Handling in Async Functions

### Standard Pattern
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

async def generate_card(
    request: CardGenerationRequest,
    correlation_id: str
) -> CardGenerationResult:
    """
    Generate a greeting card.

    Args:
        request: Card generation parameters
        correlation_id: Request tracking ID

    Returns:
        Generated card with text and image variants

    Raises:
        ValidationError: If input is invalid
        GeminiAPIError: If generation fails
    """
    try:
        # Validate recipient
        if not await employee_repo.exists(request.recipient):
            raise RecipientNotFoundError(request.recipient)

        # Generate content
        text_result, image_result = await asyncio.gather(
            generate_text(request, correlation_id),
            generate_image(request, correlation_id),
            return_exceptions=True
        )

        # Check for errors in parallel tasks
        if isinstance(text_result, Exception):
            raise GeminiTextGenerationError(original_error=text_result)
        if isinstance(image_result, Exception):
            raise GeminiImageGenerationError(original_error=image_result)

        return CardGenerationResult(
            text_variants=[text_result],
            image_variants=[image_result]
        )

    except SantaError:
        # Re-raise known errors
        raise

    except Exception as e:
        logger.exception(
            "Unexpected error during card generation",
            extra={"correlation_id": correlation_id}
        )
        raise SantaError(
            message="Произошла непредвиденная ошибка. Попробуйте позже",
            code="INTERNAL_ERROR"
        )
```

---

## Error Handling in FastAPI

### Exception Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(SantaError)
async def santa_error_handler(request: Request, exc: SantaError) -> JSONResponse:
    """Handle all Santa application errors."""
    logger.warning(
        f"Application error: {exc.code}",
        extra={
            "error_code": exc.code,
            "error_message": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )

    status_code = _get_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.to_dict()
        }
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.exception(
        f"Unexpected error: {exc}",
        extra={"path": request.url.path}
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Произошла непредвиденная ошибка. Попробуйте позже"
            }
        }
    )


def _get_status_code(exc: SantaError) -> int:
    """Map exception to HTTP status code."""
    if isinstance(exc, ValidationError):
        return 400
    if isinstance(exc, AuthenticationError):
        return 401
    if isinstance(exc, GenerationNotFoundError):
        return 404
    if isinstance(exc, RegenerationLimitExceededError):
        return 429
    if isinstance(exc, ExternalAPIError):
        return 502
    return 500
```

### API Endpoint Example

```python
from fastapi import APIRouter, Depends, HTTPException
import uuid

router = APIRouter()

@router.post("/api/v1/cards/generate")
async def generate_card_endpoint(
    request: CardGenerationRequest,
    generation_service: GenerationService = Depends(get_generation_service)
) -> CardGenerationResponse:
    """Generate a new greeting card."""
    correlation_id = str(uuid.uuid4())

    logger.info(
        "Card generation request received",
        extra={
            "correlation_id": correlation_id,
            "recipient": request.recipient
        }
    )

    # Errors are handled by exception handlers
    result = await generation_service.generate(request, correlation_id)

    logger.info(
        "Card generation completed",
        extra={"correlation_id": correlation_id}
    )

    return CardGenerationResponse(
        success=True,
        data=result
    )
```

---

## Error Handling in Frontend (Vue.js)

### API Client Error Handling

```typescript
import axios, { AxiosError } from 'axios';

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
}

export async function generateCard(request: CardRequest): Promise<CardResponse> {
  try {
    const response = await axios.post<ApiResponse<CardResponse>>(
      '/api/v1/cards/generate',
      request
    );

    if (!response.data.success) {
      throw new Error(response.data.error?.message || 'Неизвестная ошибка');
    }

    return response.data.data!;

  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data?.error;
      throw new Error(apiError?.message || 'Ошибка соединения с сервером');
    }
    throw error;
  }
}
```

### Vue Component Error Handling

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { generateCard } from '@/api/client';

const error = ref<string | null>(null);
const loading = ref(false);

async function onGenerate() {
  error.value = null;
  loading.value = true;

  try {
    const result = await generateCard(formData.value);
    // Handle success
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Произошла ошибка';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <v-alert v-if="error" type="error" dismissible @click:close="error = null">
    {{ error }}
  </v-alert>
</template>
```

---

## Logging Standards

### Log Levels
- `DEBUG`: Detailed information for debugging
- `INFO`: General operational information
- `WARNING`: Warning messages (handled errors, validation failures)
- `ERROR`: Error messages (unhandled exceptions, external API failures)
- `CRITICAL`: Critical errors (system cannot continue)

### Structured Logging
Always include:
- `correlation_id`: Request tracking ID
- `operation`: What was being done
- Context-specific data

### What NOT to Log
- API keys, tokens, passwords
- Full user messages (may contain PII)
- Full stack traces in production (use error tracking service)

```python
# Good logging
logger.info(
    "Card generation started",
    extra={
        "correlation_id": correlation_id,
        "recipient": recipient,
        "image_style": image_style
    }
)

logger.error(
    "Gemini API error",
    extra={
        "correlation_id": correlation_id,
        "error_type": type(e).__name__
    },
    exc_info=True
)

# Bad logging - exposes sensitive data
logger.info(f"Calling Gemini with key: {api_key}")  # NEVER!
logger.debug(f"User message: {message}")  # Avoid in production
```

---

## Error Recovery Strategies

### Retry with Exponential Backoff
For transient errors (network issues, temporary API unavailability):

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_gemini_api(prompt: str) -> str:
    """Call Gemini API with retry on transient errors."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GEMINI_API_URL,
            json={"prompt": prompt},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["text"]
```

### Graceful Degradation
When a service is unavailable:

```python
async def generate_with_fallback(request: CardRequest) -> CardResult:
    """Generate card with fallback options."""
    try:
        # Try to generate with AI
        text = await gemini_client.generate_text(request.message, request.style)
    except GeminiAPIError:
        # Fallback: use original message without styling
        logger.warning("Falling back to original message due to Gemini error")
        text = request.message or f"Благодарю тебя, {request.recipient}!"

    return CardResult(text=text, ...)
```

---

## Error Monitoring

### Sentry Integration (Optional)

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    environment=settings.environment
)
```

---

## Error Code Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Generic validation error |
| `RECIPIENT_NOT_FOUND` | 400 | Recipient not in employee list |
| `GENERATION_NOT_FOUND` | 404 | Generation session expired |
| `VARIANT_NOT_FOUND` | 404 | Selected variant not found |
| `REGENERATION_LIMIT_EXCEEDED` | 429 | Max regenerations reached |
| `GEMINI_API_ERROR` | 502 | Gemini API failure |
| `GEMINI_TEXT_GENERATION_ERROR` | 502 | Text generation failed |
| `GEMINI_IMAGE_GENERATION_ERROR` | 502 | Image generation failed |
| `TELEGRAM_ERROR` | 502 | Telegram API failure |
| `TELEGRAM_SEND_ERROR` | 502 | Failed to send message |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

**Last Updated**: 2023-11-26
**Project**: Santa
