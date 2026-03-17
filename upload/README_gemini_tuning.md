# Что менять в проекте

Я подготовил 2 файла.

## 1) `photocard_prompt_agent_overrides.py`
Это самый быстрый drop-in вариант.

Ваш исходный модуль уже пытается импортировать:

```python
from .photocard_prompt_agent_overrides import PHOTOCARD_AGENT_STYLE_OVERRIDES
```

Поэтому достаточно положить этот файл рядом с исходным модулем. Он:
- делает prompts заметно строже;
- подгоняет scale / whitespace / detail density под ТЗ и референсы;
- исправляет самое вредное расхождение: в line-art и quirky главный объект теперь должен занимать ~70–80% кадра, а не 18–34%.

## 2) `gemini_client_google_tuned.py`
Это reference-aware клиент на Google Gemini models.

Что он добавляет:
- поддержку `reference_images` прямо в запросе к Gemini;
- system prompt с жёстким режимом reference-following;
- отдельные, сильно ужесточённые промпты для:
  - `bento_grid`
  - `minimalist_corporate_line_art`
  - `quirky_hand_drawn_flat`
- отказ от случайной “креативной болтанки” в production-режиме;
- для legacy-стилей — сначала строит `VisualConcept`, потом рендерит его, а не подсовывает случайный subject.

## Как использовать tuned client

```python
from .gemini_client_google_tuned import ReferenceAwareGeminiClient, ReferenceImage

client = ReferenceAwareGeminiClient(
    api_key=API_KEY,
    base_url="https://litellm.pro-4.ru/v1",
    # если proxy поддерживает новые google image models, лучше так:
    image_model="gemini/gemini-3.1-flash-image-preview",
    # а для самых капризных photocard кейсов:
    # image_model="gemini/gemini-3-pro-image-preview",
)

image_bytes, prompt = await client.generate_image_direct(
    style="bento_grid",
    reason="DJ / музыка / сцена",
    message="тайл для мозаики P4.0",
    reference_images=[
        ReferenceImage("/absolute/path/ref_style.png", role="style", caption="main style reference"),
        ReferenceImage("/absolute/path/ref_layout.png", role="layout", caption="crop / scale reference"),
    ],
)
```

## Практический совет
Если нужен максимум сходства:
1. всегда передавайте `reference_images`;
2. минимум одна `style` reference + одна `layout` reference;
3. background reference делайте светлой;
4. не грузите в prompt длинное эссе — лучше короткий hobby/role cue + реальные референсы.
