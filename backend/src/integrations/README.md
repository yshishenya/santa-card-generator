# External Integrations

This package provides clients for external services used by the Santa application.

## Gemini AI Integration

The `GeminiClient` provides text generation capabilities for creating stylized greeting card content.

### Features

- **5 Text Styles:**
  - `ode` - Торжественная ода (pompous, solemn style)
  - `future` - Отчет из будущего (report from the future)
  - `haiku` - Хайку (short poetic style)
  - `newspaper` - Заметка в газете "Вестник Компании" (newspaper article)
  - `standup` - Дружеский стендап (friendly comedy style)

- **4 Image Styles:**
  - `digital_art` - Digital painting, vibrant colors
  - `pixel_art` - Retro pixel art, 8-bit style
  - `space` - Space fantasy, cosmic background
  - `movie` - Cinematic movie scene

- **Automatic retry** with exponential backoff (3 attempts)
- **Comprehensive error handling** with custom exceptions
- **Structured logging** of all API calls

### Usage Example

```python
from integrations import GeminiClient

# Initialize client
client = GeminiClient(api_key="your-api-key")

# Generate text
text = await client.generate_text(
    prompt="",
    style="ode",
    recipient="Иван Петров",
    reason="отличную работу над проектом",
    message="С Новым Годом!"
)

# Generate image (Note: Requires Imagen API integration)
try:
    image_bytes = await client.generate_image(
        recipient="Петр Иванов",
        reason="инновационные идеи",
        style="space"
    )
except NotImplementedError:
    # Image generation not yet implemented
    pass

# Cleanup
await client.close()
```

### Error Handling

The client raises specific exceptions for different error scenarios:

```python
from integrations import (
    GeminiTextGenerationError,
    GeminiImageGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
)

try:
    text = await client.generate_text(...)
except GeminiRateLimitError as e:
    # Handle rate limit (retry after some time)
    print(f"Rate limited: {e.details.get('retry_after')} seconds")
except GeminiTextGenerationError as e:
    # Handle generation failure
    print(f"Generation failed: {e.message}")
except GeminiConfigError as e:
    # Handle configuration error (permanent)
    print(f"Config error: {e.message}")
```

### Implementation Notes

1. **Text Generation**: Uses `gemini-pro` model with carefully crafted Russian prompts for each style
2. **Image Generation**: Placeholder implementation - requires Google Imagen API integration
3. **Retry Logic**: Uses `tenacity` library with exponential backoff (2s, 4s, 8s delays)
4. **Logging**: All operations logged with structured context (style, recipient, error details)

### Text Style Prompt Details

Each text style has a unique prompt template that:
- Sets the tone and context
- Provides clear requirements (length, structure, tone)
- Includes placeholders for `{recipient}`, `{reason}`, `{message}`
- Ensures appropriate corporate and festive content
- Avoids clichés and maintains authenticity

### Image Style Prompt Details

Each image style prompt:
- Uses English (better for image generation models)
- Specifies visual style, mood, and composition
- Includes Christmas/New Year thematic elements
- Explicitly forbids text in images
- Maintains professional quality suitable for corporate use

## Exception Hierarchy

```
GeminiError (base)
├── GeminiTextGenerationError
├── GeminiImageGenerationError
├── GeminiRateLimitError
└── GeminiConfigError

TelegramError (base)
├── TelegramSendError
├── TelegramConfigError
├── TelegramNetworkError
└── TelegramRateLimitError
```

## Testing

```bash
# Run tests
pytest tests/integrations/test_gemini.py -v

# Run with coverage
pytest tests/integrations/test_gemini.py --cov=src/integrations
```

## Configuration

Required environment variables:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Loaded automatically via `config.Settings`.

## Dependencies

- `google-generativeai >= 0.3` - Gemini API SDK
- `tenacity >= 8.2` - Retry logic with exponential backoff
- `pydantic >= 2.5` - Data validation
- Python 3.11+

## Future Improvements

1. **Image Generation**: Integrate Google Imagen API for actual image generation
2. **Caching**: Add Redis caching for identical prompts
3. **Streaming**: Support streaming responses for long text generation
4. **Batch Processing**: Generate multiple variants in parallel
5. **Metrics**: Add Prometheus metrics for monitoring API usage

## Troubleshooting

### Common Issues

1. **"Gemini API key is required"**
   - Ensure `GEMINI_API_KEY` is set in `.env` file
   - Check that the key is valid and not expired

2. **"Rate limit exceeded"**
   - Wait before retrying (check `retry_after` in error details)
   - Consider implementing request queuing

3. **"Image generation not implemented"**
   - This is expected - implement Imagen API integration
   - See TODO comments in `generate_image` method

## License

Part of the Santa project. Internal use only.
