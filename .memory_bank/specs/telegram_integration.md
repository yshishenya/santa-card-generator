# Specification: Telegram Integration

## Feature ID
`TG-INT-01`

## Overview
Интеграция с Telegram Bot API для отправки сгенерированных открыток в специальную ветку (topic) командного чата.

## Business Context
Открытки благодарности должны публиковаться в общедоступном канале/чате компании, чтобы вся команда могла видеть признание заслуг коллег.

## User Stories

### US-01: Отправка открытки
**Как** пользователь,
**Я хочу** отправить готовую открытку в Telegram,
**Чтобы** коллега получил публичное признание своих заслуг.

### US-02: Подтверждение отправки
**Как** пользователь,
**Я хочу** получить подтверждение успешной отправки,
**Чтобы** убедиться, что открытка доставлена.

---

## Functional Requirements

### FR-01: Формат сообщения

#### FR-01.1: Структура сообщения
Сообщение отправляется как фото с подписью (caption):

```
**Кому:** [Имя сотрудника из поля "Кому"]

**За что:** [текст из поля 3.1.3, если заполнено]

[Финальный выбранный текст благодарности]

**От кого:** [имя из поля 3.1.2, если заполнено]
```

#### FR-01.2: Условная логика
- Секция "За что" включается только если поле было заполнено
- Секция "От кого" включается только если указан отправитель (иначе анонимно)
- Упоминание через `@username` НЕ требуется

#### FR-01.3: Форматирование
- Использовать Markdown форматирование
- Ограничение подписи: 1024 символа (Telegram limit)
- При превышении - обрезать текст благодарности

---

### FR-02: Механизм отправки

#### FR-02.1: Telegram Bot API
- Использовать метод `sendPhoto`
- Передавать `message_thread_id` для отправки в конкретную ветку (topic)
- Изображение передается как bytes (не URL)

#### FR-02.2: Конфигурация
Параметры из environment variables:
- `TELEGRAM_BOT_TOKEN` - токен бота
- `TELEGRAM_CHAT_ID` - ID чата (группы/супергруппы)
- `TELEGRAM_TOPIC_ID` - ID ветки (thread/topic)

#### FR-02.3: Обработка ошибок
- Retry при временных ошибках (3 попытки с exponential backoff)
- Graceful degradation при недоступности Telegram
- Логирование всех попыток

---

## API Integration

### Telegram Bot API Call

```python
from telegram import Bot
from telegram.constants import ParseMode
import logging

logger = logging.getLogger(__name__)

async def send_card_to_telegram(
    image_bytes: bytes,
    recipient: str,
    reason: Optional[str],
    message: str,
    sender: Optional[str]
) -> int:
    """
    Send card to Telegram thread.

    Args:
        image_bytes: Generated card image
        recipient: Name of the recipient
        reason: Optional reason for gratitude
        message: The gratitude message
        sender: Optional sender name (None for anonymous)

    Returns:
        Telegram message ID

    Raises:
        TelegramSendError: If sending fails
    """
    bot = Bot(token=settings.telegram_bot_token)

    caption = format_telegram_caption(
        recipient=recipient,
        reason=reason,
        message=message,
        sender=sender
    )

    try:
        result = await bot.send_photo(
            chat_id=settings.telegram_chat_id,
            message_thread_id=settings.telegram_topic_id,
            photo=image_bytes,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(
            f"Card sent to Telegram",
            extra={
                "message_id": result.message_id,
                "recipient": recipient
            }
        )
        return result.message_id

    except TelegramError as e:
        logger.error(
            f"Failed to send card to Telegram: {e}",
            extra={"recipient": recipient}
        )
        raise TelegramSendError(
            message="Не удалось отправить открытку в Telegram",
            original_error=e
        )
```

### Caption Formatting

```python
def format_telegram_caption(
    recipient: str,
    reason: Optional[str],
    message: str,
    sender: Optional[str]
) -> str:
    """Format caption for Telegram message."""
    MAX_CAPTION_LENGTH = 1024

    parts = [f"**Кому:** {recipient}"]

    if reason:
        parts.append(f"\n**За что:** {reason}")

    parts.append(f"\n\n{message}")

    if sender:
        parts.append(f"\n\n**От кого:** {sender}")

    caption = "".join(parts)

    # Truncate if too long
    if len(caption) > MAX_CAPTION_LENGTH:
        # Keep structure, truncate message
        suffix = "..."
        available_length = MAX_CAPTION_LENGTH - len(suffix)
        caption = caption[:available_length] + suffix

    return caption
```

---

## Data Models

### SendCardRequest
```python
class SendCardRequest(BaseModel):
    """Request to send card to Telegram."""
    generation_id: str
    selected_text_id: str
    selected_image_id: str
```

### SendCardResponse
```python
class SendCardResponse(BaseModel):
    """Response after sending card."""
    message: str
    telegram_message_id: int
```

---

## Configuration

### Environment Variables
```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_TOPIC_ID=123
```

### Settings Model
```python
class TelegramSettings(BaseSettings):
    """Telegram integration settings."""

    telegram_bot_token: str
    telegram_chat_id: int
    telegram_topic_id: int

    class Config:
        env_file = ".env"
```

---

## Error Handling

### Error Types

```python
class TelegramError(SantaError):
    """Base class for Telegram-related errors."""
    pass

class TelegramSendError(TelegramError):
    """Error when sending message to Telegram fails."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            code="TELEGRAM_SEND_ERROR",
            details={
                "original_error": str(original_error) if original_error else None
            }
        )

class TelegramConfigError(TelegramError):
    """Error when Telegram is not configured properly."""

    def __init__(self, missing_config: str):
        super().__init__(
            message=f"Telegram не настроен: отсутствует {missing_config}",
            code="TELEGRAM_CONFIG_ERROR",
            details={"missing_config": missing_config}
        )
```

### Retry Logic

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    retry=retry_if_exception_type(TelegramNetworkError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def send_with_retry(
    bot: Bot,
    **kwargs
) -> Message:
    """Send message with retry on network errors."""
    return await bot.send_photo(**kwargs)
```

---

## Acceptance Criteria

### AC-01: Отправка сообщения
- [ ] Сообщение отправляется в указанный чат
- [ ] Сообщение попадает в правильную ветку (topic)
- [ ] Изображение отображается корректно
- [ ] Подпись форматируется правильно

### AC-02: Форматирование
- [ ] Имя получателя отображается жирным
- [ ] Секция "За что" присутствует только если заполнена
- [ ] Секция "От кого" присутствует только если не анонимно
- [ ] Длинный текст корректно обрезается

### AC-03: Обработка ошибок
- [ ] При временной ошибке происходит повторная попытка
- [ ] При постоянной ошибке показывается понятное сообщение
- [ ] Все ошибки логируются

### AC-04: Подтверждение
- [ ] Пользователь видит сообщение об успешной отправке
- [ ] Возвращается ID отправленного сообщения

---

## Telegram Bot Setup

### Prerequisites
1. Создать бота через @BotFather
2. Получить токен бота
3. Добавить бота в группу/супергруппу
4. Включить Topics в настройках группы (если нужны ветки)
5. Получить chat_id и topic_id

### Getting Chat ID
```python
# Временный код для получения chat_id
@bot.message_handler(commands=['chatid'])
async def get_chat_id(message):
    await message.reply(
        f"Chat ID: {message.chat.id}\n"
        f"Topic ID: {message.message_thread_id}"
    )
```

### Bot Permissions
Бот должен иметь права:
- Отправка сообщений в группу
- Отправка фото
- Отправка сообщений в топики (если используются)

---

## Message Examples

### Full Message (with all fields)
```
**Кому:** Иванов Иван Иванович

**За что:** За отличную работу над проектом Alpha

О славный воин офисных баталий!
Твой труд неутомимый, словно реки течение,
Принес команде нашей озарение!
Пусть кофе будет крепким, а баги - редкими,
А совещания - короткими и меткими!

**От кого:** Петров Петр
```

### Anonymous Message (without sender)
```
**Кому:** Сидорова Анна Сергеевна

**За что:** За помощь с презентацией

Спасибо за твою поддержку и профессионализм!
Презентация получилась великолепной благодаря тебе.
```

### Minimal Message (only recipient)
```
**Кому:** Козлов Дмитрий Александрович

Спасибо за всё!
```

---

## Performance Considerations

- Timeout для отправки: 30 секунд
- Размер изображения: рекомендуется < 5 MB
- Формат изображения: JPEG/PNG

## Security

- Bot token хранится только в environment variables
- Не логировать полный токен
- Валидация всех входных данных перед отправкой

---

## Dependencies
- `python-telegram-bot>=20.0` (async support)
- `tenacity` (для retry logic)

## Related Specifications
- [Card Generation](./card_generation.md) - источник данных для отправки

---

**Version**: 1.0
**Last Updated**: 2023-11-26
**Status**: Draft
