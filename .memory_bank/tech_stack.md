# Technology Stack and Conventions

## Project: Santa — AI-генератор корпоративных открыток

---

## Core Stack

### Backend
- **Language**: Python 3.11+ (modern, type-safe approach)
- **Framework**: FastAPI (async web framework)
- **Asynchronous Runtime**: asyncio with async/await patterns
- **Package Management**: Poetry (dependency management and virtual environments)

### Frontend (Festive & Modern)
- **Framework**: Vue.js 3 (Composition API + `<script setup>`)
- **Build Tool**: Vite 5
- **UI Library**: **PrimeVue** с темой Aura (современный, элегантный дизайн)
- **CSS Framework**: **Tailwind CSS** + **daisyUI** (winter theme)
- **Animations**:
  - **tsParticles (vue3-particles)** — снежинки, конфетти, фейерверки
  - **@vueuse/motion** — плавные анимации компонентов
  - **vue3-carousel** — карусели для выбора вариантов
- **Effects**:
  - **Glass UI** (glassmorphism) — эффект матового стекла
  - CSS градиенты в новогодних цветах

### AI/ML Integration
- **Provider**: Google Gemini API via LiteLLM Proxy
- **Text Generation**: `gemini/gemini-2.5-flash-image-preview` (для стилизации текста)
- **Image Generation**: `gemini/gemini-3-pro-image-preview` (для генерации изображений)
- **Client**: `httpx` с OpenAI-совместимым API форматом
- **Proxy URL**: Конфигурируется через `GEMINI_BASE_URL`

### Messaging
- **Platform**: Telegram Bot API
- **Library**: `python-telegram-bot` (async) или `aiogram` 3.x
- **Features**: Отправка сообщений с изображениями в threads (topics)

### Data Storage
- **Employee List**: JSON файл (загружается разово из Excel)
- **Generated Images**: Temporary file storage / memory
- **Configuration**: Environment variables via `.env`

### Deployment
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx (в compose для production)

---

## Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data  # для списка сотрудников
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  # Production: nginx reverse proxy
  # nginx:
  #   image: nginx:alpine
  #   ports:
  #     - "80:80"
  #   volumes:
  #     - ./nginx.conf:/etc/nginx/nginx.conf
  #   depends_on:
  #     - backend
  #     - frontend
```

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## Frontend Design System (Christmas Theme)

### Color Palette
```css
:root {
  /* Primary - Christmas Red */
  --color-primary: #DC2626;      /* red-600 */
  --color-primary-dark: #991B1B; /* red-800 */

  /* Secondary - Christmas Green */
  --color-secondary: #16A34A;    /* green-600 */
  --color-secondary-dark: #166534; /* green-800 */

  /* Accent - Gold */
  --color-accent: #F59E0B;       /* amber-500 */
  --color-accent-light: #FCD34D; /* amber-300 */

  /* Background - Winter */
  --color-bg-primary: #0F172A;   /* slate-900 */
  --color-bg-secondary: #1E293B; /* slate-800 */
  --color-bg-glass: rgba(255, 255, 255, 0.1);

  /* Snow White */
  --color-snow: #F8FAFC;         /* slate-50 */
}
```

### Glassmorphism Effect
```css
.glass-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
```

### Snow Animation (tsParticles)
```typescript
// particles config for snow effect
export const snowConfig = {
  particles: {
    number: { value: 100 },
    color: { value: "#ffffff" },
    shape: { type: "circle" },
    opacity: {
      value: 0.8,
      random: true
    },
    size: {
      value: 3,
      random: true
    },
    move: {
      enable: true,
      speed: 2,
      direction: "bottom",
      straight: false
    },
    wobble: {
      enable: true,
      distance: 10,
      speed: 10
    }
  },
  background: {
    color: "transparent"
  }
};
```

---

## Python Dependencies

### Core Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109"
uvicorn = {extras = ["standard"], version = "^0.27"}
pydantic = "^2.5"
pydantic-settings = "^2.1"
httpx = "^0.26"              # HTTP client for LiteLLM proxy
python-telegram-bot = "^20.7"
aiofiles = "^23.2"
python-multipart = "^0.0.6"
tenacity = "^8.2"            # Retry logic for transient errors
```

### Development Dependencies
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
black = "^24.1"
ruff = "^0.1"
mypy = "^1.8"
```

---

## Frontend Dependencies

### package.json
```json
{
  "dependencies": {
    "vue": "^3.4",
    "vue-router": "^4.2",
    "pinia": "^2.1",

    "primevue": "^3.47",
    "primeicons": "^6.0",

    "tailwindcss": "^3.4",
    "daisyui": "^4.5",

    "vue3-particles": "^2.12",
    "tsparticles": "^2.12",
    "tsparticles-slim": "^2.12",

    "@vueuse/core": "^10.7",
    "@vueuse/motion": "^2.1",

    "vue3-carousel": "^0.3",

    "axios": "^1.6"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0",
    "vite": "^5.0",
    "typescript": "^5.3",
    "autoprefixer": "^10.4",
    "postcss": "^8.4"
  }
}
```

### Tailwind Config with daisyUI
```javascript
// tailwind.config.js
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        christmas: {
          red: '#DC2626',
          green: '#16A34A',
          gold: '#F59E0B',
        }
      },
      animation: {
        'snow-fall': 'snowfall 10s linear infinite',
        'twinkle': 'twinkle 2s ease-in-out infinite',
      }
    }
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['winter', 'night'],
    darkTheme: 'night',
  }
}
```

---

## Project Structure

```
santa/
├── backend/
│   ├── src/
│   │   ├── api/                # FastAPI routers
│   │   │   ├── __init__.py
│   │   │   ├── cards.py        # Card generation endpoints
│   │   │   └── employees.py    # Employee list endpoint
│   │   ├── core/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── card_service.py
│   │   │   └── generation_service.py
│   │   ├── integrations/       # External API integrations
│   │   │   ├── __init__.py
│   │   │   ├── gemini.py       # Google Gemini client
│   │   │   └── telegram.py     # Telegram bot client
│   │   ├── models/             # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── card.py
│   │   │   └── employee.py
│   │   ├── repositories/       # Data access layer
│   │   │   ├── __init__.py
│   │   │   └── employee_repo.py
│   │   ├── config.py           # Settings management
│   │   └── main.py             # FastAPI application
│   ├── tests/
│   ├── data/
│   │   └── employees.json      # Список сотрудников (из Excel)
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CardForm.vue         # Форма создания
│   │   │   ├── GenerationPreview.vue # Превью результата
│   │   │   ├── TextCarousel.vue     # Карусель текстов
│   │   │   ├── ImageCarousel.vue    # Карусель изображений
│   │   │   ├── SnowBackground.vue   # Падающий снег
│   │   │   └── GlassCard.vue        # Стеклянная карточка
│   │   ├── views/
│   │   │   └── HomeView.vue
│   │   ├── composables/
│   │   │   └── useParticles.ts      # Настройки снега
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── assets/
│   │   │   └── styles/
│   │   │       ├── main.css
│   │   │       └── christmas.css
│   │   ├── App.vue
│   │   └── main.ts
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── .memory_bank/
└── SRS.md
```

---

## Environment Configuration

### .env.example
```bash
# ===================
# Gemini API (via LiteLLM Proxy)
# ===================
GEMINI_API_KEY=your_litellm_api_key_here
GEMINI_BASE_URL=https://litellm.pro-4.ru/v1
GEMINI_TEXT_MODEL=gemini/gemini-2.5-flash-image-preview
GEMINI_IMAGE_MODEL=gemini/gemini-3-pro-image-preview

# ===================
# Telegram
# ===================
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_TOPIC_ID=123

# ===================
# Application
# ===================
DEBUG=false
LOG_LEVEL=INFO
MAX_REGENERATIONS=3

# ===================
# Data
# ===================
EMPLOYEES_FILE_PATH=/app/data/employees.json
```

---

## Asynchronous Patterns (CRITICAL)

**All I/O operations MUST be asynchronous:**

### HTTP Requests (Backend)
```python
import httpx
from typing import Dict, Any

async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
```

### Gemini API Integration (via LiteLLM Proxy)
```python
import httpx
from typing import Optional

async def generate_text(
    prompt: str,
    style: str,
    api_key: str,
    base_url: str = "https://litellm.pro-4.ru/v1"
) -> str:
    """Generate text using Gemini via LiteLLM proxy."""
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {api_key}"}
    ) as client:
        response = await client.post(
            "/chat/completions",
            json={
                "model": "gemini/gemini-2.5-flash-image-preview",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.8,
            }
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

---

## Data Validation with Pydantic

### Card Request Model
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum

class TextStyle(str, Enum):
    ODE = "ode"              # Торжественная ода
    FUTURE_REPORT = "future" # Отчет из будущего
    HAIKU = "haiku"          # Хайку
    NEWSPAPER = "newspaper"  # Заметка в газете
    STANDUP = "standup"      # Дружеский стендап

class ImageStyle(str, Enum):
    DIGITAL_ART = "digital_art"    # Цифровая живопись
    PIXEL_ART = "pixel_art"        # Пиксель-арт
    SPACE = "space"                # Космическая фантастика
    MOVIE = "movie"                # Кадр из фильма

class CardGenerationRequest(BaseModel):
    """Request model for card generation."""
    recipient: str = Field(..., min_length=1, description="Имя получателя")
    sender: Optional[str] = Field(None, max_length=100)
    reason: Optional[str] = Field(None, max_length=150)
    message: Optional[str] = Field(None, max_length=1000)
    enhance_text: bool = Field(False)
    text_style: Optional[TextStyle] = Field(None)
    image_style: ImageStyle = Field(...)

    @field_validator('recipient')
    @classmethod
    def recipient_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Recipient name cannot be empty')
        return v.strip()
```

---

## API Endpoints Structure

### Public API (no auth required)
```
POST /api/v1/cards/generate      # Generate card (text + image)
POST /api/v1/cards/regenerate    # Regenerate text or image
POST /api/v1/cards/send          # Send card to Telegram
GET  /api/v1/employees           # Get employee list for autocomplete
GET  /health                     # Health check
```

---

## Prohibited Practices

### FORBIDDEN:
1. **Synchronous I/O in async code** - Blocks event loop
2. **Using `Any` type hints** - Defeats type safety
3. **Storing secrets in code** - Use environment variables
4. **Hardcoded Telegram IDs** - Use config
5. **Empty exception handlers** - Always log errors

---

## Code Quality Tools

```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP", "ANN", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true
```

---

## Git Workflow

### Branch Naming
- `feature/card-generation` - new feature
- `feature/snow-animation` - UI feature
- `bugfix/telegram-send-error` - bug fix

### Commit Messages (Conventional Commits)
- `feat(api): add card generation endpoint`
- `feat(ui): add snow particle effects`
- `fix(telegram): handle message thread errors`

---

## Frontend Library References

- [PrimeVue](https://primevue.org/) - UI компоненты
- [daisyUI](https://daisyui.com/) - Tailwind компоненты + темы
- [tsParticles](https://particles.js.org/) - Частицы, снег, конфетти
- [vue3-carousel](https://ismail9k.github.io/vue3-carousel/) - Карусели
- [@vueuse/motion](https://motion.vueuse.org/) - Анимации
- [Glass UI](https://ui.glass/) - Glassmorphism эффекты

---

**Last Updated**: 2023-11-26
**Python Version**: 3.11+
**Framework**: FastAPI + Vue.js 3
**Deployment**: Docker Compose
