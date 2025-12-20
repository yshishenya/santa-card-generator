# Memory Bank: Single Source of Truth for Santa

## Project: Santa — AI-генератор корпоративных открыток

This memory bank is your main source of information. Before starting any task, **mandatory** review this file and follow the relevant links.

---

## Quick Start: Before ANY Task

1. **[Tech Stack](./tech_stack.md)**: Technologies, Docker, Christmas UI libraries
2. **[Coding Standards](./guides/coding_standards.md)**: Code style, naming, type hints
3. **[Current Tasks](./current_tasks.md)**: Active tasks and priorities

---

## Knowledge System Map

### 1. About the Project (Context "WHY")
- **[Product Brief](./product_brief.md)**: Business goals, user stories, UI mockups
  - Target users: Company employees
  - Main feature: AI-generated Christmas greeting cards with Telegram delivery

### 2. Technical Foundation (Context "HOW")
- **[Tech Stack](./tech_stack.md)**: Complete list of frameworks and libraries
  - Backend: Python 3.11+, FastAPI, Docker
  - Frontend: Vue.js 3, Tailwind CSS, daisyUI, PrimeVue
  - Effects: tsParticles (snow), glassmorphism
  - AI: Google Gemini API
  - Messaging: Telegram Bot API

- **[Architectural Patterns](./patterns/)**:
  - **[API Standards](./patterns/api_standards.md)**: REST API design, endpoints
  - **[Error Handling](./patterns/error_handling.md)**: Exception hierarchy

- **[Subsystem Guides](./guides/)**:
  - **[Coding Standards](./guides/coding_standards.md)**: Style guide, async patterns
  - **[Testing Strategy](./guides/testing_strategy.md)**: Test structure, coverage

### 3. Feature Specifications (Context "WHAT")
- **[Specifications](./specs/)**: Detailed technical requirements
  - **[Card Generation](./specs/card_generation.md)**: Form, AI generation, carousels
  - **[Telegram Integration](./specs/telegram_integration.md)**: Message sending

### 4. Task Management (Context "WHAT TO DO")
- **[Current Tasks](./current_tasks.md)**: Task list with phases
- **[Workflows](./workflows/)**: Step-by-step processes

---

## Project Architecture

```
santa/
├── backend/                    # FastAPI Backend (Docker container)
│   ├── src/
│   │   ├── api/               # REST API endpoints
│   │   │   ├── auth.py        # Password authentication
│   │   │   ├── cards.py       # Card generation endpoints
│   │   │   ├── employees.py   # Employee list endpoint
│   │   │   └── dependencies.py # Rate limiting
│   │   ├── core/              # Business logic
│   │   │   ├── card_service.py
│   │   │   ├── session_manager.py
│   │   │   └── exceptions.py
│   │   ├── integrations/      # Gemini & Telegram clients
│   │   ├── models/            # Pydantic models
│   │   ├── repositories/      # Data access (JSON file)
│   │   └── config.py          # Settings
│   ├── data/
│   │   └── employees.json     # 61 employees from Excel
│   └── Dockerfile
├── frontend/                   # Vue.js Frontend (Docker container)
│   ├── src/
│   │   ├── components/        # Vue components
│   │   │   ├── CardForm.vue
│   │   │   ├── GenerationPreview.vue
│   │   │   ├── TextCarousel.vue
│   │   │   ├── ImageCarousel.vue
│   │   │   ├── PreviewModal.vue
│   │   │   ├── SnowGlobe.vue  # Interactive canvas snow
│   │   │   └── GlassCard.vue
│   │   ├── stores/            # Pinia stores
│   │   │   ├── auth.ts
│   │   │   └── card.ts
│   │   ├── router/
│   │   └── views/
│   │       ├── HomeView.vue
│   │       ├── LoginView.vue
│   │       └── SuccessView.vue
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml          # Orchestration
├── .env                        # Environment variables
└── .memory_bank/              # This documentation
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Admin panel | **NOT NEEDED** | Employee list loaded once from Excel |
| Deployment | **Docker Compose** | Simple, reproducible deployment |
| UI Theme | **Winter Night** | Blue accent, snow effects, glassmorphism |
| Employee data | **JSON file** | No database needed for MVP |
| Auth | **Password** | Simple protection via APP_PASSWORD env var |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/verify` | Password authentication |
| POST | `/api/v1/cards/generate` | Generate card |
| POST | `/api/v1/cards/regenerate` | Regenerate text/image |
| POST | `/api/v1/cards/send` | Send to Telegram |
| GET | `/api/v1/cards/images/{session_id}/{image_id}` | Get image |
| GET | `/api/v1/employees` | Get employee list |
| GET | `/health` | Health check |

---

## Quick Reference

### Text Styles (AI)
| Code | Name |
|------|------|
| `ode` | Торжественная ода |
| `future` | Отчет из будущего |
| `haiku` | Хайку |
| `newspaper` | Заметка в газете |
| `standup` | Дружеский стендап |

### Image Styles (AI) — 15 стилей с Two-Stage Generation
| Code | Name |
|------|------|
| `knitted` | Вязаная текстура |
| `magic_realism` | Магический реализм |
| `pixel_art` | Пиксель-арт 16-bit |
| `vintage_russian` | Русская открытка 1910 |
| `soviet_poster` | Советский плакат |
| `hyperrealism` | Гиперреализм |
| `digital_3d` | 3D изометрия |
| `fantasy` | Эпическое фэнтези |
| `comic_book` | Комикс |
| `watercolor` | Акварель |
| `cyberpunk` | Киберпанк |
| `paper_cutout` | Бумажная аппликация |
| `pop_art` | Поп-арт |
| `lego` | LEGO конструктор |
| `linocut` | Линогравюра |

### Winter Night Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Accent Blue | `#3382FE` | Buttons, highlights |
| Red | `#E25555` | Festive accents |
| Green | `#4A9F4A` | Pine green |
| Background | `#0B1929` | Deep night sky |
| Text Primary | `#F0F8FF` | Main text |
| Text Secondary | `#B8D4F0` | Secondary text |

---

## Environment Variables

```bash
# Gemini API (via LiteLLM Proxy)
GEMINI_API_KEY=...
GEMINI_BASE_URL=https://litellm.pro-4.ru/v1
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_IMAGE_MODEL=gemini/gemini-2.5-flash-image-preview

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
TELEGRAM_TOPIC_ID=...

# Application
APP_PASSWORD=...           # Required password for login
DEBUG=false
LOG_LEVEL=INFO
MAX_REGENERATIONS=3
EMPLOYEES_FILE_PATH=/app/data/employees.json
```

---

## Running the Project

```bash
# Build and start containers
docker compose up --build

# Access
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Working Rules

**Rule 1:** If you make architectural changes, update Memory Bank.

**Rule 2:** Before starting work, check `current_tasks.md`.

**Rule 3:** Follow patterns from `patterns/` and standards from `guides/`.

**Rule 4:** All I/O operations must be asynchronous.

**Rule 5:** No admin panel — employee data is pre-loaded from Excel.

---

## Waiting For

- [x] ~~Excel файл со списком сотрудников~~ (61 сотрудник добавлен)

---

## Frontend Libraries

- [PrimeVue](https://primevue.org/) — UI components
- [daisyUI](https://daisyui.com/) — Tailwind components + winter theme
- [tsParticles](https://particles.js.org/) — Snow, confetti effects
- [vue3-carousel](https://ismail9k.github.io/vue3-carousel/) — Carousels
- [@vueuse/motion](https://motion.vueuse.org/) — Animations
- [Glass UI](https://ui.glass/) — Glassmorphism

---

**Last Updated**: 2025-12-18
**Deployment**: Docker Compose
**Image Styles**: 15 (two-stage generation)
