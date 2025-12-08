# Gemini Integration - Quick Reference

## Installation

```bash
cd /home/yan/santa/backend
poetry install
```

## Text Styles

| Code | Name | Length | Use Case |
|------|------|--------|----------|
| `ode` | Торжественная ода | 500-800 chars | Formal, poetic recognition |
| `future` | Отчет из будущего | 400-600 chars | Visionary, forward-looking |
| `haiku` | Хайку | 200-400 chars | Brief, elegant poetry |
| `newspaper` | Заметка в газете | 500-700 chars | Professional storytelling |
| `standup` | Дружеский стендап | 400-600 chars | Friendly, humorous |

## Image Styles

| Code | Name | Description |
|------|------|-------------|
| `digital_art` | Digital painting | Vibrant colors, professional |
| `pixel_art` | Retro pixel art | 8-bit nostalgia |
| `space` | Space fantasy | Cosmic, ethereal |
| `movie` | Cinematic scene | Dramatic, inspiring |

## Basic Usage

```python
from src.integrations import GeminiClient
from src.config import settings

client = GeminiClient(api_key=settings.gemini_api_key)

# Generate text
text = await client.generate_text(
    prompt="",
    style="ode",  # or: future, haiku, newspaper, standup
    recipient="Иван Петров",
    reason="отличную работу над проектом",
    message="С Новым Годом!"
)

# Cleanup
await client.close()
```

## Error Handling

```python
from src.integrations.exceptions import (
    GeminiTextGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
)

try:
    text = await client.generate_text(...)
except GeminiRateLimitError as e:
    retry_after = e.details.get("retry_after", 60)
    await asyncio.sleep(retry_after)
except GeminiTextGenerationError as e:
    logger.error(f"Generation failed: {e.message}")
except GeminiConfigError as e:
    logger.error(f"Config error: {e.message}")
```

## Configuration

In `.env`:
```bash
GEMINI_API_KEY=your_api_key_here
```

## Testing

```bash
# Run example
python -m examples.gemini_usage_example

# Run tests (when implemented)
pytest tests/integrations/test_gemini.py -v
```

## Files

- `gemini.py` - Main client (496 lines)
- `exceptions.py` - Custom exceptions (276 lines)
- `__init__.py` - Package exports (42 lines)
- `README.md` - Full documentation
- `QUICK_REFERENCE.md` - This file

## Important Notes

1. **Image generation** raises `NotImplementedError` - requires Imagen API
2. **Retry logic** is automatic - 3 attempts with exponential backoff
3. **All operations** are async - use `await`
4. **Logging** is automatic - check logs for debugging
5. **Type hints** are complete - use IDE autocomplete

## Common Issues

**Import fails**:
```bash
poetry install  # Install dependencies first
```

**"API key required"**:
```bash
# Add to .env file:
GEMINI_API_KEY=your_key_here
```

**Rate limited**:
```python
# Automatic retry with exponential backoff
# Or catch GeminiRateLimitError and wait
```

## Support

- Full docs: `README.md`
- Usage example: `examples/gemini_usage_example.py`
- Memory Bank: `.memory_bank/patterns/error_handling.md`
