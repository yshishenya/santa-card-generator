<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, APIError } from '@/api/client'
import {
  IMAGE_STYLE_LABELS,
  ImageStyle,
  type PhotocardImageVariant,
} from '@/types'
import { loadPlayerName, savePlayerName } from '@/utils/playerIdentity'

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
const isGameRevealOpen = ref(false)

const styleCatalog = [
  {
    style: ImageStyle.BENTO_GRID,
    slug: 'bento',
    code: 'BENTO GRID',
    icon: 'grid_view',
    shortLabel: 'Style 01',
    description: 'Модульная сетка, простые формы и иконки увлечений внутри ячеек.',
  },
  {
    style: ImageStyle.MINIMALIST_CORPORATE_LINE_ART,
    slug: 'line',
    code: 'CORPORATE LINE ART',
    icon: 'filter_center_focus',
    shortLabel: 'Style 02',
    description: 'Чистый контур, faceless персонажи и строгая схема чёрный + белый + акцент.',
  },
  {
    style: ImageStyle.QUIRKY_HAND_DRAWN_FLAT,
    slug: 'quirky',
    code: 'HAND-DRAWN FLAT',
    icon: 'gesture',
    shortLabel: 'Style 03',
    description: 'Живой контур, мягкие формы и яркие плоские пятна с дудлинг-акцентами.',
  },
] as const

const hasGenerated = computed(() => imageVariants.value.length === 3 && sessionId.value !== null)
const resolvedFullName = computed(() => fullName.value.trim())
const canRevealGame = computed(() => Boolean(resolvedFullName.value) && !isGenerating.value && !isSending.value)
const selectedImage = computed(() => imageVariants.value[selectedImageIndex.value] ?? null)
const selectedStyleMeta = computed(() => {
  if (!selectedImage.value) {
    return styleCatalog[1]
  }
  return styleCatalog.find((item) => item.style === selectedImage.value?.style) ?? styleCatalog[1]
})
const selectedStyleLabel = computed(() => getStyleLabel(selectedStyleMeta.value.style))
const stageReference = computed(() => {
  if (!sessionId.value) {
    return 'P4-LINE-ART-002'
  }
  return sessionId.value.slice(0, 12).toUpperCase()
})
const canGenerate = computed(() => {
  return !isGenerating.value && !isSending.value && Boolean(fullName.value.trim() && alterEgo.value.trim())
})
const canSend = computed(() => {
  return Boolean(sessionId.value && selectedImage.value && confirmSend.value && !isSending.value)
})
const stageStatus = computed(() => {
  if (confirmSend.value && selectedImage.value) {
    return 'Ready to send'
  }
  if (hasGenerated.value) {
    return '3 варианта готовы'
  }
  if (isGenerating.value) {
    return 'Собираем направления'
  }
  return 'Ожидаем ввод'
})
const styleCards = computed(() => {
  return styleCatalog.map((entry, index) => {
    const variant = imageVariants.value.find((item) => item.style === entry.style) ?? imageVariants.value[index] ?? null
    const isActive = hasGenerated.value
      ? selectedImage.value?.style === variant?.style
      : entry.style === ImageStyle.MINIMALIST_CORPORATE_LINE_ART

    return {
      ...entry,
      variant,
      isActive,
      styleLabel: getStyleLabel(entry.style),
    }
  })
})

let gameRevealTimer: ReturnType<typeof setTimeout> | null = null

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof APIError) {
    return err.getUserMessage()
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
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

function resetGeneratedState(): void {
  sessionId.value = null
  imageVariants.value = []
  selectedImageIndex.value = 0
  confirmSend.value = false
  isImageZoomed.value = false
}

function resetAll(): void {
  fullName.value = loadPlayerName()
  alterEgo.value = ''
  error.value = null
  resetGeneratedState()
}

function selectImage(index: number): void {
  selectedImageIndex.value = index
  confirmSend.value = false
}

function selectStyleCard(style: ImageStyle): void {
  const index = imageVariants.value.findIndex((variant) => variant.style === style)
  if (index >= 0) {
    selectImage(index)
  }
}

function openImageZoom(index: number): void {
  selectImage(index)
  isImageZoomed.value = true
}

function closeImageZoom(): void {
  isImageZoomed.value = false
}

function clearGameRevealTimer(): void {
  if (gameRevealTimer) {
    clearTimeout(gameRevealTimer)
    gameRevealTimer = null
  }
}

function beginGameRevealPress(): void {
  if (!canRevealGame.value) {
    return
  }

  clearGameRevealTimer()
  gameRevealTimer = setTimeout(() => {
    isGameRevealOpen.value = true
    clearGameRevealTimer()
  }, 800)
}

function cancelGameRevealPress(): void {
  clearGameRevealTimer()
}

function handleGameRevealKeydown(event: KeyboardEvent): void {
  if (event.repeat) {
    return
  }

  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    beginGameRevealPress()
  }
}

function handleGameRevealKeyup(event: KeyboardEvent): void {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    cancelGameRevealPress()
  }
}

function closeGameReveal(): void {
  isGameRevealOpen.value = false
  cancelGameRevealPress()
}

async function openTapP40Game(): Promise<void> {
  closeGameReveal()
  await router.push({ name: 'tap-p40' })
}

function selectPreviousImage(): void {
  if (imageVariants.value.length === 0) {
    return
  }

  const nextIndex = selectedImageIndex.value === 0
    ? imageVariants.value.length - 1
    : selectedImageIndex.value - 1
  selectImage(nextIndex)
}

function selectNextImage(): void {
  if (imageVariants.value.length === 0) {
    return
  }

  const nextIndex = (selectedImageIndex.value + 1) % imageVariants.value.length
  selectImage(nextIndex)
}

async function handleGenerate(): Promise<void> {
  const name = fullName.value.trim()
  const alterEgoPrompt = alterEgo.value.trim()
  if (!name || !alterEgoPrompt) {
    return
  }

  fullName.value = name
  alterEgo.value = alterEgoPrompt
  savePlayerName(name)

  try {
    isGenerating.value = true
    error.value = null
    resetGeneratedState()

    const response = await apiClient.generatePhotocard({
      full_name: name,
      alter_ego: alterEgoPrompt,
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

function handleKeydown(event: KeyboardEvent): void {
  if (!isImageZoomed.value) {
    return
  }

  if (event.key === 'Escape') {
    closeImageZoom()
  }

  if (event.key === 'ArrowLeft') {
    selectPreviousImage()
  }

  if (event.key === 'ArrowRight') {
    selectNextImage()
  }
}

onMounted(() => {
  if (!fullName.value.trim()) {
    fullName.value = loadPlayerName()
  }
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  clearGameRevealTimer()
})

watch(fullName, (value) => {
  savePlayerName(value)
})
</script>

<template>
  <section class="studio-page">
    <header class="studio-header">
      <div class="studio-header__brand">
        <div class="studio-header__title-wrap">
          <div class="studio-header__mark" :class="{ 'studio-header__mark--armed': canRevealGame }" aria-hidden="true">
            <img src="/favicon.svg" alt="" class="studio-header__mark-image" draggable="false">
          </div>

          <div
            class="studio-header__title-trigger"
            :class="{ 'studio-header__title-trigger--armed': canRevealGame }"
            role="button"
            tabindex="0"
            aria-label="Дополнительный режим P4.0"
            @keydown="handleGameRevealKeydown"
            @keyup="handleGameRevealKeyup"
            @pointerdown="beginGameRevealPress"
            @pointerup="cancelGameRevealPress"
            @pointerleave="cancelGameRevealPress"
            @pointercancel="cancelGameRevealPress"
            @contextmenu.prevent
          >
            <h1 class="studio-header__title">P4.0 Alter Ego</h1>
            <p class="studio-header__subtitle">Генератор мозаичных портретов</p>
          </div>
        </div>

        <div class="studio-header__divider"></div>

        <p class="studio-header__summary">
          Соберите свой образ вне работы, выберите лучший кадр и отправьте его в общую мозаику команды.
        </p>
      </div>

      <div class="studio-header__actions">
        <RouterLink to="/print-assets" class="studio-header__archive-link">
          <span class="material-symbols-outlined" aria-hidden="true">archive</span>
          Архив для печати
        </RouterLink>
      </div>
    </header>

    <div class="studio-grid">
      <aside class="studio-sidebar">
        <form class="app-panel app-panel--strong creator-card" @submit.prevent="handleGenerate">
          <div class="creator-card__head">
            <span class="material-symbols-outlined" aria-hidden="true">edit_square</span>
            <h2>Панель создания</h2>
          </div>

          <label class="app-field">
            <span class="app-label">Имя</span>
            <input
              v-model="fullName"
              type="text"
              maxlength="200"
              placeholder="Введите ваше имя"
              class="app-input"
              :disabled="isGenerating || isSending"
            >
          </label>

          <label class="app-field">
            <span class="app-label">Альтер-эго / Хобби</span>
            <textarea
              v-model="alterEgo"
              rows="6"
              maxlength="200"
              placeholder="Например: капитан летающего книжного магазина над ночным городом"
              class="app-textarea"
              :disabled="isGenerating || isSending"
            ></textarea>
            <p class="app-field-hint">
              Одной ёмкой фразой задайте роль, сцену и настроение. Генератор соберёт три графических направления.
            </p>
          </label>

          <div v-if="error" class="app-error">
            {{ error }}
          </div>

          <div class="creator-card__actions">
            <button type="submit" class="app-button" :disabled="!canGenerate">
              <span v-if="isGenerating" class="app-spinner" aria-hidden="true"></span>
              <span>{{ isGenerating ? 'Генерируем' : 'Сгенерировать' }}</span>
            </button>

            <button
              type="button"
              class="app-button-ghost"
              :disabled="isGenerating || isSending"
              @click="resetAll"
            >
              <span class="material-symbols-outlined" aria-hidden="true">refresh</span>
              Сбросить
            </button>
          </div>
        </form>
      </aside>

      <div class="studio-main">
        <section v-if="hasGenerated" class="style-rack">
          <button
            v-for="card in styleCards"
            :key="card.style"
            type="button"
            class="style-card"
            :class="[
              `style-card--${card.slug}`,
              { 'style-card--active': card.isActive },
            ]"
            :disabled="!card.variant"
            @click="selectStyleCard(card.style)"
          >
            <div class="style-card__header">
              <span>{{ card.code }}</span>
              <span class="material-symbols-outlined" aria-hidden="true">
                {{ card.isActive ? 'check_circle' : 'radio_button_unchecked' }}
              </span>
            </div>

            <div class="style-card__preview">
              <img
                v-if="card.variant"
                :src="card.variant.url"
                :alt="card.styleLabel"
              >

              <div v-else class="style-card__placeholder">
                <template v-if="card.slug === 'bento'">
                  <div class="style-card__placeholder-bento">
                    <span></span>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </template>

                <template v-else-if="card.slug === 'line'">
                  <div class="style-card__placeholder-line">
                    <div></div>
                  </div>
                </template>

                <template v-else>
                  <div class="style-card__placeholder-quirky">
                    <span class="material-symbols-outlined" aria-hidden="true">gesture</span>
                  </div>
                </template>
              </div>
            </div>

            <div class="style-card__body">
              <p class="style-card__eyebrow">{{ card.shortLabel }}</p>
              <h3>{{ card.styleLabel }}</h3>
              <p>{{ card.description }}</p>
            </div>

            <span v-if="card.isActive" class="style-card__active-tag">Active</span>
          </button>
        </section>

        <section class="app-panel preview-card">
          <div v-if="hasGenerated || isGenerating" class="preview-card__live">
            <span class="preview-card__live-dot"></span>
            <span>Live Preview: Standard Definition</span>
          </div>

          <div class="preview-card__stage">
            <div v-if="hasGenerated || isGenerating" class="preview-card__corner preview-card__corner--top"></div>
            <div v-if="hasGenerated || isGenerating" class="preview-card__corner preview-card__corner--bottom"></div>

            <template v-if="isGenerating">
              <div class="preview-loading">
                <div class="preview-loading__cards">
                  <div v-for="n in 3" :key="n" class="preview-loading__card"></div>
                </div>
                <p>Собираем три направления в общем графическом ключе P4.0.</p>
              </div>
            </template>

            <template v-else-if="selectedImage">
              <button
                type="button"
                class="preview-card__frame"
                @click="openImageZoom(selectedImageIndex)"
              >
                <img :src="selectedImage.url" alt="Выбранная карточка alter ego">
                <span class="preview-card__frame-zoom">
                  <span class="material-symbols-outlined" aria-hidden="true">open_in_full</span>
                </span>
                <span class="preview-card__frame-accent preview-card__frame-accent--top"></span>
                <span class="preview-card__frame-accent preview-card__frame-accent--bottom"></span>
              </button>
            </template>

            <template v-else>
              <div class="preview-card__placeholder">
                <div class="preview-card__placeholder-frame">
                  <span class="material-symbols-outlined" aria-hidden="true">account_circle</span>
                </div>
                <div class="preview-card__placeholder-copy">
                  <strong>Сначала сгенерируйте 3 варианта</strong>
                  <p>После этого здесь появится выбранный квадрат 1:1, а сверху откроется блок выбора стилей.</p>
                </div>
              </div>
            </template>

            <div v-if="hasGenerated" class="preview-card__hud">
              <p>REF: {{ stageReference }}</p>
              <p>MODE: {{ selectedStyleMeta.code }}</p>
              <p>STATUS: {{ stageStatus }}</p>
            </div>
          </div>

          <div v-if="hasGenerated" class="preview-card__details">
            <div class="preview-card__identity">
              <p class="app-kicker">Selected Direction</p>
              <h2 class="app-heading">{{ resolvedFullName || 'Ваше имя' }}</h2>
              <p class="app-subtle">
                {{ selectedStyleMeta.description }}
              </p>
            </div>

            <div class="preview-card__primitive-row">
              <div
                v-for="card in styleCards"
                :key="`${card.style}-primitive`"
                class="preview-card__primitive"
                :class="[
                  `preview-card__primitive--${card.slug}`,
                  { 'preview-card__primitive--active': card.isActive },
                ]"
              >
                <span class="material-symbols-outlined" aria-hidden="true">{{ card.icon }}</span>
              </div>
            </div>
          </div>

          <div v-if="hasGenerated" class="preview-card__footer">
            <div class="preview-card__footer-left">
              <label class="app-checkbox">
                <input
                  v-model="confirmSend"
                  type="checkbox"
                >
                <span>Готов к отправке в Telegram с подписью только из имени.</span>
              </label>

              <button
                type="button"
                class="app-button-ghost"
                :disabled="isGenerating || isSending"
                @click="handleGenerate"
              >
                <span class="material-symbols-outlined" aria-hidden="true">restart_alt</span>
                Сгенерировать заново
              </button>
            </div>

            <div class="preview-card__footer-right">
              <button
                type="button"
                class="app-button-dark"
                :disabled="!canSend"
                @click="handleSend"
              >
                <span v-if="isSending" class="app-spinner" aria-hidden="true"></span>
                <span v-else class="material-symbols-outlined" aria-hidden="true">send</span>
                <span>{{ isSending ? 'Отправляем...' : 'Отправить в Telegram' }}</span>
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>

    <div
      v-if="isImageZoomed && selectedImage"
      class="zoom-layer"
      @click="closeImageZoom"
    >
      <div class="app-panel app-panel--strong zoom-dialog" @click.stop>
        <header class="zoom-dialog__header">
          <div>
            <p class="app-kicker">Preview</p>
            <h2 class="app-heading">{{ selectedStyleLabel }}</h2>
          </div>

          <button
            type="button"
            class="app-button-ghost"
            @click="closeImageZoom"
          >
            Закрыть
          </button>
        </header>

        <div class="zoom-dialog__media">
          <button type="button" class="zoom-dialog__nav" @click="selectPreviousImage">←</button>
          <img :src="selectedImage.url" alt="Увеличенный просмотр">
          <button type="button" class="zoom-dialog__nav" @click="selectNextImage">→</button>
        </div>

        <footer class="zoom-dialog__footer">
          <span class="app-chip">{{ selectedImageIndex + 1 }} / {{ imageVariants.length }}</span>
          <span class="app-chip app-chip--blue">{{ selectedStyleMeta.code }}</span>
        </footer>
      </div>
    </div>

    <div
      v-if="isGameRevealOpen"
      class="secret-layer"
      @click="closeGameReveal"
    >
      <div class="app-panel app-panel--strong secret-dialog" @click.stop>
        <p class="app-kicker">P4.0 Easter Egg</p>
        <h2 class="app-heading">Tap the P4.0</h2>
        <p class="app-subtle">
          25 секунд, один знак P4.0 и много ложных плиток. Если пальцы быстрые, можно залететь в рейтинг.
        </p>

        <div class="secret-dialog__actions">
          <button type="button" class="app-button" @click="openTapP40Game">
            <span class="material-symbols-outlined" aria-hidden="true">joystick</span>
            Играть
          </button>

          <button type="button" class="app-button-ghost" @click="closeGameReveal">
            Не сейчас
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.studio-page {
  display: grid;
  gap: 1.5rem;
}

.studio-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  padding: 0 0 1rem;
  border-bottom: 2px solid var(--black);
}

.studio-header__brand,
.studio-header__actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.studio-header__title-wrap {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.studio-header__title-trigger {
  display: grid;
  gap: 0.2rem;
  min-width: 0;
  padding: 0.1rem 0.2rem;
  border-radius: 0.5rem;
  transition: transform 120ms ease, color 120ms ease, background 120ms ease;
  -webkit-user-select: none;
  user-select: none;
  -webkit-touch-callout: none;
  touch-action: manipulation;
}

.studio-header__title-trigger:active {
  transform: scale(0.985);
}

.studio-header__title-trigger:focus-visible {
  outline: 2px solid var(--digital-blue);
  outline-offset: 3px;
}

.studio-header__title-trigger--armed {
  background: rgba(175, 195, 255, 0.18);
}

.studio-header__mark {
  position: relative;
  display: grid;
  place-items: center;
  width: 3.25rem;
  height: 3.25rem;
  border: 2px solid var(--black);
  border-radius: 1rem;
  background: var(--white);
  transition: transform 120ms ease, box-shadow 120ms ease, background 120ms ease;
  flex-shrink: 0;
  pointer-events: none;
}

.studio-header__mark--armed {
  background: linear-gradient(180deg, var(--white) 0%, rgba(175, 195, 255, 0.88) 100%);
  box-shadow: 4px 4px 0 var(--black);
  animation: studio-mark-pulse 2.8s ease-in-out infinite;
}

.studio-header__mark-image {
  width: 72%;
  aspect-ratio: 1;
  pointer-events: none;
  -webkit-user-drag: none;
  -webkit-touch-callout: none;
}

.studio-header__title,
.studio-header__summary,
.studio-header__subtitle {
  margin: 0;
}

.studio-header__title {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.05em;
  text-transform: uppercase;
}

.studio-header__subtitle {
  margin-top: 0.2rem;
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--digital-blue);
}

.studio-header__divider {
  width: 2px;
  height: 2.5rem;
  background: var(--black);
}

.studio-header__summary {
  max-width: 13rem;
  font-size: 0.7rem;
  line-height: 1.45;
  color: var(--text-soft);
}

.studio-header__archive-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  transition: color 0.18s ease;
}

.studio-header__archive-link:hover {
  color: var(--digital-blue);
}

.studio-grid {
  display: grid;
  gap: 1.5rem;
}

.studio-sidebar,
.studio-main {
  display: grid;
  gap: 1.25rem;
  align-content: start;
}

.creator-card,
.preview-card,
.zoom-dialog {
  padding: 1.25rem;
}

.creator-card {
  gap: 1.2rem;
}

.creator-card__head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding-bottom: 0.85rem;
  border-bottom: 2px solid var(--black);
}

.creator-card__head h2 {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.creator-card__actions {
  display: grid;
  gap: 0.75rem;
}

.style-rack {
  display: grid;
  gap: 1rem;
}

.style-card {
  position: relative;
  display: grid;
  gap: 0.8rem;
  padding: 0.85rem;
  border: 1.5px solid var(--line);
  background: var(--white);
  text-align: left;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.style-card:hover:not(:disabled) {
  transform: translate(-1px, -1px);
  box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.12);
}

.style-card:disabled {
  cursor: default;
}

.style-card--active {
  border-color: var(--digital-blue);
  border-width: 2px;
  box-shadow: 4px 4px 0 var(--digital-blue);
}

.style-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  font-size: 0.56rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.style-card--active .style-card__header {
  color: var(--digital-blue);
}

.style-card__preview {
  display: grid;
  place-items: center;
  min-height: 7.5rem;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: var(--surface-subtle);
  overflow: hidden;
}

.style-card__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.style-card__placeholder {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
}

.style-card__placeholder-bento {
  display: grid;
  grid-template-columns: repeat(3, 1rem);
  gap: 0.2rem;
}

.style-card__placeholder-bento span {
  width: 1rem;
  height: 1rem;
  background: rgba(0, 0, 0, 0.08);
}

.style-card__placeholder-bento span:first-child,
.style-card__placeholder-bento span:last-child {
  grid-column: span 2;
}

.style-card__placeholder-line {
  display: grid;
  place-items: center;
  width: 4rem;
  height: 4rem;
  border: 1.5px solid var(--digital-blue);
  background: rgba(51, 130, 255, 0.05);
}

.style-card__placeholder-line div {
  width: 1rem;
  height: 1rem;
  border: 1.5px solid var(--digital-blue);
  background: var(--white);
}

.style-card__placeholder-quirky {
  font-size: 2rem;
  color: rgba(0, 0, 0, 0.28);
}

.style-card__body {
  display: grid;
  gap: 0.35rem;
}

.style-card__eyebrow,
.style-card__body h3,
.style-card__body p {
  margin: 0;
}

.style-card__eyebrow {
  font-size: 0.54rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.style-card__body h3 {
  font-size: 0.82rem;
  font-weight: 800;
  line-height: 1.35;
  text-transform: uppercase;
}

.style-card__body p {
  font-size: 0.72rem;
  line-height: 1.6;
  color: var(--text-soft);
}

.style-card__active-tag {
  position: absolute;
  top: -0.8rem;
  left: 50%;
  padding: 0.18rem 0.48rem;
  border: 1.5px solid var(--black);
  background: var(--digital-blue);
  color: var(--white);
  font-size: 0.48rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  transform: translateX(-50%);
  box-shadow: 2px 2px 0 var(--black);
}

.preview-card {
  position: relative;
  display: grid;
  gap: 1rem;
}

.preview-card__live {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.preview-card__live-dot {
  width: 0.6rem;
  height: 0.6rem;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 999px;
  background: var(--digital-blue);
}

.preview-card__stage {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 34rem;
  padding: 3.25rem 1rem 4rem;
  border: 1.5px solid var(--black);
  background:
    linear-gradient(rgba(185, 205, 255, 0.35) 1px, transparent 1px),
    linear-gradient(90deg, rgba(185, 205, 255, 0.35) 1px, transparent 1px),
    #fcfdff;
  background-size: 1.15rem 1.15rem;
  overflow: hidden;
}

.preview-card__corner {
  position: absolute;
  width: 5.5rem;
  height: 5.5rem;
  pointer-events: none;
}

.preview-card__corner--top {
  top: 1rem;
  right: 1rem;
  border-top: 2px solid rgba(0, 0, 0, 0.16);
  border-right: 2px solid rgba(0, 0, 0, 0.16);
}

.preview-card__corner--bottom {
  left: 1rem;
  bottom: 1rem;
  border-bottom: 2px solid rgba(0, 0, 0, 0.16);
  border-left: 2px solid rgba(0, 0, 0, 0.16);
}

.preview-card__frame,
.preview-card__placeholder-frame {
  position: relative;
  display: grid;
  place-items: center;
  width: min(100%, 19rem);
  aspect-ratio: 1;
  border: 2px solid var(--black);
  background: var(--white);
  box-shadow: 8px 8px 0 rgba(0, 0, 0, 0.8);
}

.preview-card__frame {
  padding: 0;
}

.preview-card__frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-card__frame-zoom {
  position: absolute;
  right: 0.75rem;
  bottom: 0.75rem;
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border: 1.5px solid var(--black);
  background: rgba(255, 255, 255, 0.94);
}

.preview-card__frame-accent {
  position: absolute;
  width: 0.8rem;
  height: 0.8rem;
  border: 1.5px solid var(--black);
}

.preview-card__frame-accent--top {
  top: -2px;
  right: -2px;
  background: var(--accent-yellow);
}

.preview-card__frame-accent--bottom {
  left: -2px;
  bottom: -2px;
  background: var(--soft-lavender);
}

.preview-card__placeholder {
  display: grid;
  gap: 1rem;
  justify-items: center;
}

.preview-card__placeholder-frame {
  background: rgba(255, 255, 255, 0.92);
}

.preview-card__placeholder-frame .material-symbols-outlined {
  font-size: 7rem;
}

.preview-card__placeholder-copy {
  display: grid;
  gap: 0.35rem;
  max-width: 24rem;
  text-align: center;
}

.preview-card__placeholder-copy strong,
.preview-card__placeholder-copy p {
  margin: 0;
}

.preview-card__placeholder-copy strong {
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.preview-card__placeholder-copy p {
  font-size: 0.8rem;
  line-height: 1.6;
  color: var(--text-soft);
}

.preview-card__hud {
  position: absolute;
  left: 1rem;
  bottom: 1rem;
  display: grid;
  gap: 0.2rem;
  font-size: 0.56rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-soft);
}

.preview-loading {
  display: grid;
  gap: 1rem;
  justify-items: center;
  width: min(100%, 32rem);
}

.preview-loading__cards {
  display: grid;
  width: 100%;
  gap: 0.75rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.preview-loading__card {
  min-height: 11rem;
  border: 1.5px solid var(--black);
  background:
    linear-gradient(120deg, rgba(175, 195, 255, 0.3), rgba(255, 255, 255, 1), rgba(130, 255, 240, 0.26));
  background-size: 200% 100%;
  animation: preview-shimmer 1.5s linear infinite;
}

.preview-loading p {
  margin: 0;
  max-width: 24rem;
  font-size: 0.8rem;
  line-height: 1.6;
  text-align: center;
  color: var(--text-soft);
}

.preview-card__details {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.preview-card__identity {
  display: grid;
  gap: 0.45rem;
  max-width: 36rem;
}

.preview-card__primitive-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.preview-card__primitive {
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  border: 1.5px solid var(--black);
  background: var(--white);
}

.preview-card__primitive--bento {
  background: var(--digital-blue);
  color: var(--white);
}

.preview-card__primitive--line {
  background: var(--digital-mint);
}

.preview-card__primitive--quirky {
  background: var(--deep-violet);
  color: var(--white);
}

.preview-card__primitive--active {
  transform: translateY(-2px);
  box-shadow: 0 4px 0 rgba(0, 0, 0, 0.18);
}

.preview-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 2px solid var(--black);
}

.preview-card__footer-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
}

.zoom-layer {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: grid;
  place-items: center;
  padding: 1.25rem;
  background: rgba(248, 251, 255, 0.94);
}

.secret-layer {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  align-items: end;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.28);
}

.secret-dialog {
  display: grid;
  gap: 0.9rem;
  width: min(100%, 28rem);
  margin: 0 auto;
  padding: 1.1rem;
}

.secret-dialog__actions {
  display: grid;
  gap: 0.65rem;
}

.zoom-dialog {
  display: grid;
  gap: 1rem;
  width: min(100%, 56rem);
}

.zoom-dialog__header,
.zoom-dialog__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.zoom-dialog__media {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 1rem;
}

.zoom-dialog__media img {
  width: 100%;
  max-height: min(72vh, 42rem);
  aspect-ratio: 1;
  object-fit: contain;
  border: 1.5px solid var(--black);
  background: var(--white);
}

.zoom-dialog__nav {
  width: 3rem;
  height: 3rem;
  border: 1.5px solid var(--black);
  background: var(--white);
  font-size: 1.25rem;
  font-weight: 700;
}

@keyframes preview-shimmer {
  to {
    background-position: -200% 0;
  }
}

@keyframes studio-mark-pulse {
  0%, 100% {
    transform: translateY(0);
    box-shadow: 4px 4px 0 var(--black);
  }

  50% {
    transform: translateY(-1px);
    box-shadow: 6px 6px 0 var(--black);
  }
}

@media (min-width: 1080px) {
  .studio-grid {
    grid-template-columns: minmax(18rem, 20rem) minmax(0, 1fr);
  }

  .style-rack {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

}

@media (max-width: 1079px) {
  .studio-header,
  .studio-header__brand,
  .studio-header__actions,
  .preview-card__details,
  .preview-card__footer {
    flex-direction: column;
    align-items: stretch;
  }

  .studio-header__divider {
    display: none;
  }

  .studio-header__summary {
    max-width: none;
  }

  .preview-card__stage {
    min-height: 28rem;
  }
}

@media (max-width: 767px) {
  .studio-page {
    gap: 1rem;
  }

  .studio-header__title-wrap {
    align-items: flex-start;
  }

  .studio-header__mark {
    width: 2.9rem;
    height: 2.9rem;
  }

  .studio-header__title {
    font-size: 1.4rem;
  }

  .creator-card,
  .preview-card,
  .zoom-dialog {
    padding: 1rem;
  }

  .style-rack,
  .studio-sidebar,
  .studio-main,
  .studio-grid,
  .preview-loading__cards,
  .zoom-dialog__media {
    grid-template-columns: 1fr;
  }

  .preview-card__stage {
    min-height: 22rem;
    padding-top: 3rem;
  }

  .preview-card__frame,
  .preview-card__placeholder-frame {
    width: min(100%, 15rem);
  }

  .preview-card__footer-left,
  .zoom-dialog__header,
  .zoom-dialog__footer {
    flex-direction: column;
    align-items: stretch;
  }

  .zoom-dialog__nav {
    width: 100%;
  }
}
</style>
