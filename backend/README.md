# Santa Backend

AI-generated corporate greeting cards backend service.

## Tech Stack

- **Python 3.11**
- **FastAPI** - Modern web framework
- **Pydantic** - Data validation
- **Google Generative AI (Gemini)** - Text and image generation
- **python-telegram-bot** - Telegram integration
- **httpx** - Async HTTP client
- **aiofiles** - Async file operations

## Project Structure

```
backend/
├── src/
│   ├── api/              # API endpoints
│   │   ├── cards.py      # Card generation endpoints
│   │   └── employees.py  # Employee endpoints
│   ├── core/             # Business logic (to be implemented)
│   ├── integrations/     # External service integrations
│   │   ├── gemini.py     # Gemini AI client (to be implemented)
│   │   └── telegram.py   # Telegram bot client (to be implemented)
│   ├── models/           # Pydantic models
│   │   ├── card.py       # Card-related models
│   │   └── employee.py   # Employee model
│   ├── repositories/     # Data access layer
│   │   └── employee_repo.py
│   ├── config.py         # Application settings
│   └── main.py           # FastAPI application
├── data/
│   └── employees.json    # Employee data file
├── tests/                # Test suite (to be implemented)
├── Dockerfile
├── pyproject.toml
└── .env.example
```

## Setup

### 1. Install dependencies with Poetry

```bash
cd backend
poetry install
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required variables:
- `GEMINI_API_KEY` - Google Gemini API key
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `TELEGRAM_CHAT_ID` - Target chat ID
- `TELEGRAM_TOPIC_ID` - Target topic/thread ID

### 3. Run the development server

```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation (Swagger UI): `http://localhost:8000/docs`

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Employees
- `GET /api/v1/employees` - Get list of all employees

### Cards (placeholders - to be implemented)
- `POST /api/v1/cards/generate` - Generate new greeting card
- `POST /api/v1/cards/regenerate` - Regenerate specific card element
- `POST /api/v1/cards/send` - Send card to Telegram

## Docker

### Build image

```bash
docker build -t santa-backend:latest .
```

### Run container

```bash
docker run -d \
  --name santa-backend \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  santa-backend:latest
```

## Development

### Code formatting

```bash
poetry run black src/
```

### Linting

```bash
poetry run ruff check src/
```

### Type checking

```bash
poetry run mypy src/
```

### Run tests

```bash
poetry run pytest
```

### Run tests with coverage

```bash
poetry run pytest --cov=src --cov-report=html
```

## Architecture Principles

### Async/Await
All I/O operations MUST be asynchronous:
- Use `async def` and `await` for all functions with I/O
- Use `httpx` for HTTP requests (NOT `requests`)
- Use `aiofiles` for file operations

### Type Safety
All functions MUST have complete type hints:
```python
async def get_employee(employee_id: str) -> Optional[Employee]:
    ...
```

### Error Handling
All external calls must have proper error handling:
```python
try:
    result = await external_api_call()
except httpx.HTTPError as e:
    logger.error(f"API error: {e}")
    raise
```

### Logging
- Use `logging` module, NOT `print()`
- Include context in all log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## TODO

- [ ] Implement Gemini AI integration for text generation
- [ ] Implement Gemini AI integration for image generation
- [ ] Implement Telegram bot client
- [ ] Implement card generation service
- [ ] Add session management (Redis or in-memory)
- [ ] Add retry mechanisms with tenacity
- [ ] Write unit tests
- [ ] Add integration tests
- [ ] Add API rate limiting
- [ ] Add request validation middleware
- [ ] Add monitoring and metrics

## License

Proprietary
