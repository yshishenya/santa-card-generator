<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, APIError } from '@/api/client'
import {
  IMAGE_STYLE_LABELS,
  type ImageStyle,
  type PhotocardImageVariant,
} from '@/types'

const router = useRouter()

const fullName = ref('')
const alterEgo = ref('')
const sessionId = ref<string | null>(null)
const imageVariants = ref<PhotocardImageVariant[]>([])
const selectedImageIndex = ref(0)
const confirmSend = ref(false)
const isGenerating = ref(false)
const isSending = ref(false)
const error = ref<string | null>(null)
const isImageZoomed = ref(false)

const hasGenerated = computed(() => imageVariants.value.length === 3 && sessionId.value !== null)
const selectedImage = computed(() => imageVariants.value[selectedImageIndex.value] ?? null)
const resolvedFullName = computed(() => fullName.value.trim())

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof APIError) {
    return err.getUserMessage()
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
}

function resetGeneratedState(): void {
  sessionId.value = null
  imageVariants.value = []
  selectedImageIndex.value = 0
  confirmSend.value = false
}

function resetAll(): void {
  fullName.value = ''
  alterEgo.value = ''
  error.value = null
  resetGeneratedState()
}

function openImageZoom(index: number): void {
  selectedImageIndex.value = index
  confirmSend.value = false
  isImageZoomed.value = true
}

function closeImageZoom(): void {
  isImageZoomed.value = false
}

function selectPreviousImage(): void {
  if (imageVariants.value.length === 0) {
    return
  }
  const nextIndex = selectedImageIndex.value === 0
    ? imageVariants.value.length - 1
    : selectedImageIndex.value - 1
  selectedImageIndex.value = nextIndex
  confirmSend.value = false
}

function selectNextImage(): void {
  if (imageVariants.value.length === 0) {
    return
  }
  const nextIndex = (selectedImageIndex.value + 1) % imageVariants.value.length
  selectedImageIndex.value = nextIndex
  confirmSend.value = false
}

function getStyleLabel(style: ImageStyle): string {
  const mappedLabel = IMAGE_STYLE_LABELS[style]
  if (mappedLabel) {
    return mappedLabel
  }

  return String(style)
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

async function handleGenerate(): Promise<void> {
  const name = fullName.value.trim()
  if (!name || !alterEgo.value.trim()) {
    return
  }
  fullName.value = name

  try {
    isGenerating.value = true
    error.value = null
    resetGeneratedState()

    const response = await apiClient.generatePhotocard({
      full_name: name,
      alter_ego: alterEgo.value.trim(),
    })

    sessionId.value = response.session_id
    imageVariants.value = response.image_variants
  } catch (err) {
    error.value = getErrorMessage(err, 'Не удалось сгенерировать варианты открытки.')
  } finally {
    isGenerating.value = false
  }
}

async function handleSend(): Promise<void> {
  if (!sessionId.value || !selectedImage.value || !confirmSend.value) {
    return
  }

  try {
    isSending.value = true
    error.value = null

    const response = await apiClient.sendPhotocard({
      session_id: sessionId.value,
      selected_image_index: selectedImageIndex.value,
    })

    await router.push({
      name: 'success',
      query: {
        env: response.delivery_env,
        message_id: response.telegram_message_id ? String(response.telegram_message_id) : '',
      },
    })
  } catch (err) {
    error.value = getErrorMessage(err, 'Не удалось отправить открытку в Telegram.')
  } finally {
    isSending.value = false
  }
}
</script>

<template>
  <div class="workspace">
    <form class="glass-card studio-panel control-panel" @submit.prevent="handleGenerate">
      <div class="space-y-3">
        <p class="section-kicker">
          П4.0 7 лет
        </p>

        <div class="space-y-2">
          <h1 class="text-3xl font-bold leading-tight text-platform-light sm:text-[2rem]">
            Соберите фотокарточку
          </h1>
          <p class="text-sm leading-6 text-platform-text-secondary sm:text-[15px]">
            Введите свое имя, опишите образ и после генерации утвердите один вариант для отправки в Telegram.
          </p>
        </div>
      </div>

      <div class="space-y-2">
        <label for="full-name" class="section-kicker">
          Ваше имя
        </label>
        <input
          id="full-name"
          v-model="fullName"
          type="text"
          maxlength="200"
          placeholder="Например: Катя"
          class="input-magic w-full px-4 py-3 text-base"
          :disabled="isGenerating || isSending"
        />
      </div>

      <div class="space-y-2">
        <label for="alter-ego" class="section-kicker">
          Альтер-эго
        </label>
        <textarea
          id="alter-ego"
          v-model="alterEgo"
          rows="6"
          maxlength="200"
          placeholder="Например: капитан летающего книжного магазина над ночным городом"
          class="input-magic w-full resize-none px-4 py-3 text-base"
          :disabled="isGenerating || isSending"
        ></textarea>
        <p class="text-sm leading-6 text-platform-text-muted">
          Коротко опишите образ, роль или настроение. Чем конкретнее формулировка, тем чище будут варианты.
        </p>
      </div>

      <div v-if="error" class="rounded-2xl border border-platform-primary/40 bg-platform-primary/10 px-4 py-3 text-sm text-platform-primary-light">
        {{ error }}
      </div>

      <div class="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
        <button
          type="submit"
          :disabled="isGenerating || isSending || !fullName.trim() || !alterEgo.trim()"
          class="btn-magic rounded-xl px-6 py-4 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
        >
          <span class="flex items-center justify-center gap-2">
            <span v-if="isGenerating" class="loading loading-spinner loading-sm"></span>
            <i v-else class="pi pi-sparkles"></i>
            <span>{{ isGenerating ? 'Генерируем 3 варианта...' : 'Сгенерировать 3 варианта' }}</span>
          </span>
        </button>

        <button
          type="button"
          class="rounded-xl border border-platform-line/30 bg-platform-bg-secondary/85 px-5 py-4 font-semibold text-platform-text-primary transition hover:border-platform-accent/30 hover:bg-platform-line/20"
          :disabled="isGenerating || isSending"
          @click="resetAll"
        >
          Сбросить
        </button>
      </div>
    </form>

    <section class="glass-card studio-panel result-panel">
      <div class="result-panel__header">
        <div class="space-y-2">
          <p class="section-kicker">
            Результат
          </p>
          <h2 class="text-2xl font-semibold text-platform-light sm:text-[2rem]">
            Превью карточки
          </h2>
          <p class="max-w-2xl text-sm leading-6 text-platform-text-secondary">
            После генерации откройте варианты, выберите лучший и подтвердите отправку.
          </p>
        </div>

      </div>

      <div v-if="!hasGenerated" class="empty-state">
        <div class="empty-state__icon" aria-hidden="true">✨</div>
        <div class="space-y-2">
          <p class="text-lg font-semibold text-platform-text-primary">
            Здесь появятся три готовых варианта
          </p>
          <p class="mx-auto max-w-md text-sm leading-6 text-platform-text-muted">
            Сначала запустите генерацию слева. Затем можно будет открыть изображение крупно, выбрать один вариант и отправить его в Telegram.
          </p>
        </div>
      </div>

      <template v-else>
        <div class="preview-stack">
          <div class="space-y-3">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-sm font-semibold uppercase tracking-[0.16em] text-platform-accent">
                Варианты
              </h3>
              <p class="variant-counter">
                {{ selectedImageIndex + 1 }} из {{ imageVariants.length }}
              </p>
            </div>

            <div class="variant-rail">
              <button
                v-for="(variant, index) in imageVariants"
                :key="variant.url"
                type="button"
                class="variant-card text-left"
                :class="{ 'variant-card--active': index === selectedImageIndex }"
                @click="openImageZoom(index)"
              >
                <div class="aspect-[3/4] overflow-hidden rounded-[1.1rem] bg-platform-bg-secondary">
                  <img
                    :src="variant.url"
                    :alt="`Вариант ${index + 1}`"
                    class="h-full w-full object-cover"
                  />
                </div>

                <div class="mt-3 flex items-start gap-3">
                  <span
                    class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold"
                    :class="index === selectedImageIndex ? 'border-platform-accent bg-platform-accent/15 text-platform-accent' : 'border-platform-line/30 text-platform-text-muted'"
                  >
                    {{ index + 1 }}
                  </span>

                  <div class="min-w-0 flex-1">
                    <p class="text-[10px] uppercase tracking-[0.16em] text-platform-text-muted">
                      Стиль
                    </p>
                    <p class="variant-card__label mt-1 text-sm font-semibold leading-5 text-platform-text-primary">
                      {{ getStyleLabel(variant.style) }}
                    </p>
                  </div>
                </div>
              </button>
            </div>
          </div>

          <section v-if="selectedImage" class="selected-stage">
            <button
              type="button"
              class="selected-stage__media"
              @click="openImageZoom(selectedImageIndex)"
            >
              <img
                :src="selectedImage.url"
                alt="Выбранная фотокарточка"
                class="h-full w-full object-cover"
              />
              <span class="selected-stage__badge">
                {{ getStyleLabel(selectedImage.style) }}
              </span>
            </button>

            <div class="selected-stage__meta">
              <div>
                <p class="text-xs uppercase tracking-[0.18em] text-platform-text-muted">
                  Ваше имя
                </p>
                <h3 class="mt-2 text-2xl font-semibold text-platform-text-primary sm:text-3xl">
                  {{ resolvedFullName }}
                </h3>
              </div>

              <label class="selected-stage__confirm">
                <input
                  v-model="confirmSend"
                  type="checkbox"
                  class="mt-0.5 h-4 w-4 shrink-0 rounded border-platform-accent/60 bg-transparent"
                />
                <span>
                  Подтверждаю отправку выбранного изображения в Telegram с подписью только из имени.
                </span>
              </label>

              <div class="selected-stage__actions">
                <button
                  type="button"
                  class="btn-magic rounded-xl px-6 py-3 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="!confirmSend || isSending"
                  @click="handleSend"
                >
                  <span class="flex items-center justify-center gap-2">
                    <span v-if="isSending" class="loading loading-spinner loading-sm"></span>
                    <i v-else class="pi pi-send"></i>
                    <span>{{ isSending ? 'Отправляем...' : 'Отправить в Telegram' }}</span>
                  </span>
                </button>

                <button
                  type="button"
                  class="selected-stage__secondary rounded-xl border border-platform-line/30 bg-transparent px-5 py-3 font-semibold text-platform-text-primary transition hover:border-platform-accent/30 hover:bg-platform-line/20"
                  :disabled="isSending"
                  @click="handleGenerate"
                >
                  Перегенерировать 3 варианта
                </button>
              </div>
            </div>
          </section>
        </div>
      </template>
    </section>
  </div>

  <div
    v-if="isImageZoomed && selectedImage"
    class="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-4"
    @click="closeImageZoom"
  >
    <div
      class="relative w-full max-w-2xl rounded-[1.5rem] border border-platform-line/35 bg-platform-bg-secondary p-3"
      @click.stop
    >
      <button
        type="button"
        class="absolute right-2 top-2 z-10 inline-flex h-9 w-9 items-center justify-center rounded-full border border-platform-line/40 bg-platform-bg-primary/80 text-sm text-platform-text-secondary transition hover:bg-platform-accent/20"
        @click="closeImageZoom"
      >
        ×
      </button>

      <div class="grid place-items-center">
        <div class="relative w-full overflow-hidden rounded-[1.2rem] bg-platform-bg-primary">
          <img
            :src="selectedImage.url"
            alt="Увеличенный вид"
            class="mx-auto max-h-[75vh] w-full rounded-[1.2rem] object-contain"
          />

          <button
            type="button"
            class="absolute left-3 top-1/2 -translate-y-1/2 rounded-full border border-platform-line/40 bg-platform-bg-primary/80 px-3 py-2 text-sm text-platform-text-secondary transition hover:bg-platform-accent/20"
            @click="selectPreviousImage"
          >
            ←
          </button>
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full border border-platform-line/40 bg-platform-bg-primary/80 px-3 py-2 text-sm text-platform-text-secondary transition hover:bg-platform-accent/20"
            @click="selectNextImage"
          >
            →
          </button>
        </div>

        <p class="mt-3 text-sm text-platform-text-secondary">
          {{ selectedImageIndex + 1 }} / {{ imageVariants.length }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace {
  display: grid;
  gap: 1.5rem;
}

.control-panel,
.result-panel {
  position: relative;
  min-width: 0;
  padding: 1.25rem;
}

.control-panel {
  display: grid;
  gap: 1.25rem;
  align-content: start;
}

.result-panel {
  display: grid;
  gap: 1.5rem;
  min-height: 100%;
  overflow: hidden;
}

.result-panel__header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.session-pill {
  max-width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1px solid rgba(129, 140, 248, 0.16);
  border-radius: 1rem;
  background: rgba(15, 23, 42, 0.55);
  font-size: 0.75rem;
  line-height: 1.45;
  color: var(--color-text-muted);
  word-break: break-all;
}

.empty-state {
  display: grid;
  place-items: center;
  gap: 1rem;
  min-height: 21rem;
  padding: 2rem 1.25rem;
  border: 1px dashed rgba(129, 140, 248, 0.22);
  border-radius: 1.75rem;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.5) 0%, rgba(15, 23, 42, 0.34) 100%);
  text-align: center;
}

.empty-state__icon {
  display: grid;
  place-items: center;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 1rem;
  background: rgba(99, 102, 241, 0.12);
  font-size: 1.75rem;
}

.preview-stack {
  display: grid;
  gap: 1.25rem;
}

.variant-counter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.65rem;
  border: 1px solid rgba(129, 140, 248, 0.16);
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.52);
  font-size: 0.75rem;
  line-height: 1;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.variant-rail {
  display: flex;
  gap: 0.9rem;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 0.25rem;
  scroll-snap-type: x proximity;
  scrollbar-width: thin;
}

.variant-card {
  flex: 0 0 9.5rem;
  min-width: 9.5rem;
  padding: 0.7rem;
  border: 1px solid rgba(186, 200, 215, 0.16);
  border-radius: 1.25rem;
  background: rgba(10, 22, 35, 0.58);
  overflow: hidden;
  scroll-snap-align: start;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.variant-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.35);
}

.variant-card--active {
  border-color: rgba(99, 102, 241, 0.72);
  box-shadow: 0 18px 44px rgba(6, 17, 27, 0.32);
}

.variant-card__label {
  display: -webkit-box;
  min-height: 2.5rem;
  overflow: hidden;
  word-break: break-word;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.selected-stage {
  display: grid;
  gap: 1rem;
  min-width: 0;
  padding: 1rem;
  border: 1px solid rgba(99, 102, 241, 0.16);
  border-radius: 1.75rem;
  background: rgba(11, 21, 38, 0.55);
  overflow: hidden;
}

.selected-stage__media {
  position: relative;
  display: block;
  overflow: hidden;
  min-width: 0;
  aspect-ratio: 4 / 5;
  border: 1px solid rgba(129, 140, 248, 0.14);
  border-radius: 1.35rem;
  background: rgba(15, 23, 42, 0.9);
  text-align: left;
}

.selected-stage__badge {
  position: absolute;
  left: 0.9rem;
  top: 0.9rem;
  max-width: calc(100% - 1.8rem);
  padding: 0.45rem 0.75rem;
  border: 1px solid rgba(99, 102, 241, 0.35);
  border-radius: 999px;
  background: rgba(99, 102, 241, 0.16);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-accent-light);
  overflow-wrap: anywhere;
}

.selected-stage__meta {
  display: grid;
  gap: 1rem;
  min-width: 0;
  align-content: start;
}

.selected-stage__confirm {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  padding: 1rem 1.05rem;
  border: 1px solid rgba(99, 102, 241, 0.22);
  border-radius: 1rem;
  background: rgba(99, 102, 241, 0.1);
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--color-text-primary);
}

.selected-stage__actions {
  display: grid;
  gap: 0.75rem;
}

.selected-stage__actions > * {
  width: 100%;
  min-width: 0;
}

.selected-stage__secondary {
  line-height: 1.35;
}

@media (min-width: 768px) {
  .control-panel,
  .result-panel {
    padding: 1.5rem;
  }

  .variant-card {
    flex-basis: 10.5rem;
    min-width: 10.5rem;
  }

  .result-panel__header {
    flex-direction: row;
    justify-content: space-between;
    align-items: flex-start;
  }

  .session-pill {
    max-width: 15rem;
  }
}

@media (min-width: 1280px) {
  .workspace {
    grid-template-columns: minmax(19rem, 25rem) minmax(0, 1fr);
    align-items: start;
  }

  .control-panel {
    position: sticky;
    top: 1.5rem;
  }

  .selected-stage {
    grid-template-columns: minmax(15rem, 17.5rem) minmax(0, 1fr);
    align-items: start;
    gap: 1.25rem;
  }

  .variant-rail {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    overflow: visible;
  }

  .variant-card {
    min-width: 0;
  }
}
</style>
