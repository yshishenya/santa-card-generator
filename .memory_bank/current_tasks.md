# Current Tasks

## Project: Santa — AI-генератор корпоративных открыток

---

## Done

### Backend Setup ✅
- [x] [SETUP-01] Инициализировать проект с Poetry и настроить зависимости
- [x] [SETUP-02] Создать структуру каталогов backend согласно tech_stack.md
- [x] [SETUP-03] Настроить конфигурацию через pydantic-settings (.env)
- [x] [SETUP-04] Настроить логирование и middleware
- [x] [SETUP-05] Создать Dockerfile для backend

### Docker & Deployment ✅
- [x] [DOCKER-01] Создать docker-compose.yml
- [x] [DOCKER-02] Создать Dockerfile для frontend
- [x] [DOCKER-03] Настроить nginx.conf для frontend
- [ ] [DOCKER-04] Протестировать запуск через docker compose up

### Data Preparation ✅
- [x] [DATA-01] Создать скрипт конвертации Excel → JSON для списка сотрудников (sample data created)
- [x] [DATA-02] Реализовать EmployeeRepository для чтения из JSON

### Core Features ✅
- [x] [CARD-01] Реализовать Pydantic модели для открыток (см. specs/card_generation.md)
- [x] [CARD-02] Создать API эндпоинты для генерации открыток
- [x] [CARD-03] Реализовать сервис генерации контента
- [x] [CARD-04] Реализовать механизм перегенерации и выбора вариантов

### AI Integration ✅
- [x] [AI-01] Интегрировать Google Gemini API для генерации текста
- [x] [AI-02] Интегрировать Google Gemini API для генерации изображений (placeholder - requires Imagen API)
- [x] [AI-03] Создать промпты для 5 стилей текста
- [x] [AI-04] Создать промпты для 4 стилей изображений

### Telegram Integration ✅
- [x] [TG-01] Реализовать клиент для Telegram Bot API (см. specs/telegram_integration.md)
- [x] [TG-02] Реализовать форматирование сообщений
- [x] [TG-03] Добавить retry логику для отправки

### Frontend Setup ✅
- [x] [UI-SETUP-01] Инициализировать Vue.js проект с Vite
- [x] [UI-SETUP-02] Настроить Tailwind CSS + daisyUI (winter theme)
- [x] [UI-SETUP-03] Установить и настроить PrimeVue
- [x] [UI-SETUP-04] Настроить tsParticles для снежинок

### Frontend Components ✅
- [x] [UI-01] Создать SnowBackground.vue — падающий снег
- [x] [UI-02] Создать GlassCard.vue — карточка с glassmorphism
- [x] [UI-03] Создать компонент формы CardForm.vue
- [x] [UI-04] Создать компонент превью GenerationPreview.vue
- [x] [UI-05] Создать TextCarousel.vue с vue3-carousel
- [x] [UI-06] Создать ImageCarousel.vue с vue3-carousel
- [x] [UI-07] Создать SuccessScreen.vue — экран после отправки
- [x] [UI-08] Интегрировать фронтенд с API (axios client)

### Documentation ✅
- [x] [DOCS-01] Создать README.md с инструкциями по запуску
- [x] [DOCS-02] Создать .env.example с описанием переменных

---

## To Do

### Testing ✅
- [x] [TEST-01] Написать unit тесты для сервисов
- [x] [TEST-02] Написать интеграционные тесты для API
- [x] [TEST-03] Написать тесты для Gemini интеграции (с моками)
- [x] [TEST-04] Написать тесты для Telegram интеграции (с моками)

### Final Verification
- [ ] [VERIFY-01] Протестировать запуск через docker compose up
- [ ] [VERIFY-02] Проверить все API endpoints через Swagger UI
- [ ] [VERIFY-03] Сквозное тестирование формы → генерация → отправка

---

## In Progress

*Нет активных задач*

---

## Bug Fixes

### [BUG] Поле "Кому" оставалось пустым при отправке в Telegram ✅

**Дата**: 2025-12-09

**Описание проблемы**:
При отправке открытки в Telegram поле "Кому" отображалось пустым, несмотря на то, что пользователь выбирал получателя.

**Причина**:
В `card_service.py:send_card()` использовалось `request.employee_name` из `SendCardRequest`, которое приходило с фронтенда и могло быть пустым. При этом корректное имя получателя (`original_request.recipient`) уже было сохранено в сессии на этапе генерации.

**Решение**:
Изменён код отправки в Telegram — теперь `recipient` берётся из сессии (`original_request.recipient`), а не из запроса send. Это гарантирует, что имя получателя всегда будет корректным, так как оно было валидировано при генерации открытки.

**Изменённые файлы**:
- `backend/src/core/card_service.py` (строки 475-499)

---

## Feature Additions

### [FEATURE] Telegram @username mention при отправке открытки ✅

**Дата**: 2025-12-11

**Описание фичи**:
При отправке открытки в Telegram теперь добавляется @username сотрудника для уведомления получателя.

**Реализация**:
- Добавлено поле `telegram` в модель `Employee` (опциональное)
- Обновлён `employees.json` с актуальными telegram username сотрудников (49 записей)
- Для сотрудников без username используется числовой ID (но в таком случае mention не работает в Telegram)
- При отправке в Telegram caption формируется как: `**Кому:** Имя Фамилия (@username)`

**Изменённые файлы**:
- `backend/data/employees.json` — добавлены telegram username для всех сотрудников
- `backend/src/models/employee.py` — добавлено поле `telegram: Optional[str]`
- `backend/src/integrations/telegram.py` — добавлен параметр `recipient_telegram` в `send_card()` и `_format_caption()`
- `backend/src/core/card_service.py` — поиск telegram username сотрудника и передача в Telegram клиент

---

### [FEATURE] Улучшенный UX выбора текста при AI-стилизации ✅

**Дата**: 2025-12-09

**Описание фичи**:
При выборе AI-стилизации текста пользователь делает выбор на **втором экране** (после генерации), а не на первом:

**Первый экран (форма)**:
- Чекбокс "Улучшить текст с помощью AI"
- Если включён — выбор стиля текста (ода, хайку и т.д.)
- Никаких дополнительных чекбоксов

**Второй экран (превью)**:
- Оригинальный текст показан **отдельно** (сверху) с radio "Использовать"
- AI варианты показаны **в карусели** ниже с возможностью выбора
- Единый radio group — пользователь выбирает между своим текстом и AI-вариантами
- Кнопка регенерации только для AI вариантов

**Реализация**:
- **Backend**: Всегда генерирует оригинал + 3 AI варианта при `enhance_text=true`
- **Frontend**: TextCarousel разделяет варианты на оригинальный (отдельно) и AI (карусель)
- Используются `computed` для фильтрации по `style === 'original'`

**Изменённые файлы**:
- `frontend/src/components/CardForm.vue` — убран лишний чекбокс
- `frontend/src/components/TextCarousel.vue` — новый UI с раздельным отображением
- `.memory_bank/specs/card_generation.md` — обновлена спецификация

---

## Implementation Summary

### Backend Architecture

```
backend/
├── src/
│   ├── api/                    # REST API endpoints ✅
│   │   ├── auth.py             # POST /auth/verify (password authentication)
│   │   ├── cards.py            # POST /generate, /regenerate, /send, GET /images
│   │   ├── employees.py        # GET /employees
│   │   └── dependencies.py     # Dependency injection (rate limiting)
│   ├── core/                   # Business logic ✅
│   │   ├── card_service.py     # Main service orchestrator
│   │   ├── session_manager.py  # In-memory session storage
│   │   └── exceptions.py       # Service exceptions
│   ├── integrations/           # External services ✅
│   │   ├── gemini.py           # Google Gemini AI client (text & image)
│   │   ├── telegram.py         # Telegram Bot client
│   │   └── exceptions.py       # Integration exceptions
│   ├── models/                 # Pydantic models ✅
│   │   ├── card.py             # Card request/response models
│   │   ├── employee.py         # Employee model
│   │   └── response.py         # Generic API response
│   ├── repositories/           # Data access ✅
│   │   └── employee_repo.py    # JSON file repository
│   ├── config.py               # Settings ✅
│   └── main.py                 # FastAPI application ✅
├── data/
│   └── employees.json          # 61 employees from Excel ✅
├── Dockerfile                  # Production Docker image ✅
├── pyproject.toml              # Poetry dependencies ✅
└── .env.example                # Environment template ✅
```

### Frontend Architecture

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts             # Axios HTTP client ✅
│   ├── components/
│   │   ├── CardForm.vue          # Card creation form ✅
│   │   ├── GenerationPreview.vue # Preview with carousels ✅
│   │   ├── GlassCard.vue         # Glassmorphism card wrapper ✅
│   │   ├── ImageCarousel.vue     # Image variants carousel ✅
│   │   ├── PreviewModal.vue      # Send confirmation modal ✅
│   │   ├── SnowBackground.vue    # Static tsParticles snow ✅
│   │   ├── SnowGlobe.vue         # Interactive canvas snow with hidden objects ✅
│   │   ├── SnowflakeGame.vue     # Easter egg game component ✅
│   │   └── TextCarousel.vue      # Text variants carousel ✅
│   ├── composables/
│   │   └── useParticles.ts       # tsParticles configuration ✅
│   ├── router/
│   │   └── index.ts              # Vue Router with auth guards ✅
│   ├── stores/
│   │   ├── auth.ts               # Pinia auth store ✅
│   │   └── card.ts               # Pinia card state management ✅
│   ├── types/
│   │   └── index.ts              # TypeScript types & enums ✅
│   ├── views/
│   │   ├── HomeView.vue          # Main card creation page ✅
│   │   ├── LoginView.vue         # Password login page ✅
│   │   └── SuccessView.vue       # Success screen after send ✅
│   ├── assets/
│   │   └── styles/main.css       # Global styles (Winter Night Theme) ✅
│   ├── App.vue                   # Root component with ambient orbs ✅
│   └── main.ts                   # Vue initialization ✅
├── Dockerfile                    # Multi-stage build ✅
├── nginx.conf                    # Nginx config ✅
├── package.json                  # Dependencies ✅
├── tailwind.config.js            # Tailwind + daisyUI ✅
├── vite.config.ts                # Vite config ✅
└── tsconfig.json                 # TypeScript config ✅
```

### Docker Configuration

```
santa/
├── docker-compose.yml       # Production orchestration ✅
├── docker-compose.dev.yml   # Development with hot reload ✅
├── .env.example             # Environment variables ✅
└── .dockerignore            # Build exclusions ✅
```

---

## Notes

- **Админ-панель НЕ нужна** — список сотрудников загружается разово из Excel
- **Запуск через Docker Compose** — `docker compose up --build`
- **Новогодняя тематика UI** — снежинки, glassmorphism, winter theme
- Все задачи следуют стандартам из `.memory_bank/guides/coding_standards.md`
- Спецификации для каждой фичи находятся в `.memory_bank/specs/`
- Минимальное покрытие тестами: 80%

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/verify` | Password authentication |
| POST | `/api/v1/cards/generate` | Generate card with text & image variants |
| POST | `/api/v1/cards/regenerate` | Regenerate specific variant |
| POST | `/api/v1/cards/send` | Send to Telegram |
| GET | `/api/v1/cards/images/{session_id}/{image_id}` | Get generated image |
| GET | `/api/v1/employees` | Get employee list |
| GET | `/health` | Health check |

---

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env with your API keys
# GEMINI_API_KEY=your_key
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_CHAT_ID=your_chat_id
# TELEGRAM_TOPIC_ID=your_topic_id

# 3. Build and run
docker compose up --build

# 4. Access
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Waiting For

- [x] Excel файл со списком сотрудников (от пользователя) — **61 сотрудник добавлен**

---

**Last Updated**: 2025-12-11
