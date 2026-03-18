<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiClient, APIError } from '@/api/client'
import type { PrintArchiveAsset } from '@/types'

const authChecked = ref(false)
const isAuthenticated = ref(false)
const isLoading = ref(false)
const isSubmitting = ref(false)
const password = ref('')
const showPassword = ref(false)
const error = ref<string | null>(null)
const assets = ref<PrintArchiveAsset[]>([])

const archiveFacts = [
  'Исходные PNG для печати',
  'Скачивание по одному и ZIP целиком',
  'Отдельный пароль от основного входа',
] as const

const downloadAllUrl = computed(() => apiClient.getPrintArchiveDownloadAllUrl())
const assetCountLabel = computed(() => {
  const count = assets.value.length
  if (count === 1) {
    return '1 оригинал'
  }
  if (count >= 2 && count <= 4) {
    return `${count} оригинала`
  }
  return `${count} оригиналов`
})

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof APIError) {
    return err.getUserMessage()
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
}

function formatDate(value: string): string {
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed)
}

async function loadAssets(): Promise<void> {
  assets.value = await apiClient.fetchPrintArchiveAssets()
}

async function bootstrap(): Promise<void> {
  try {
    isLoading.value = true
    error.value = null
    isAuthenticated.value = await apiClient.getPrintArchiveAuthStatus()
    if (isAuthenticated.value) {
      await loadAssets()
    }
  } catch (err) {
    error.value = getErrorMessage(err, 'Не удалось открыть архив для печати.')
  } finally {
    authChecked.value = true
    isLoading.value = false
  }
}

async function handleLogin(): Promise<void> {
  if (!password.value.trim()) {
    return
  }

  try {
    isSubmitting.value = true
    error.value = null
    const success = await apiClient.verifyPrintArchivePassword(password.value)
    if (!success) {
      error.value = 'Неверный пароль'
      return
    }

    isAuthenticated.value = true
    password.value = ''
    await loadAssets()
  } catch (err) {
    if (err instanceof APIError && err.statusCode === 401) {
      error.value = 'Неверный пароль'
    } else {
      error.value = getErrorMessage(err, 'Не удалось открыть архив для печати.')
    }
  } finally {
    isSubmitting.value = false
    authChecked.value = true
  }
}

async function handleLogout(): Promise<void> {
  try {
    await apiClient.logoutPrintArchive()
  } finally {
    isAuthenticated.value = false
    assets.value = []
    password.value = ''
    error.value = null
  }
}

onMounted(() => {
  bootstrap()
})
</script>

<template>
  <section class="archive-page">
    <header class="archive-headline">
      <div class="archive-headline__route">
        <span>Архив для печати</span>
        <span>/</span>
        <span>Local Cache</span>
      </div>

      <div class="archive-headline__facts">
        <span
          v-for="fact in archiveFacts"
          :key="fact"
          class="app-chip"
        >
          {{ fact }}
        </span>
      </div>
    </header>

    <section class="app-panel app-panel--strong archive-hero">
      <div class="archive-hero__copy">
        <p class="app-kicker">P4.0 Alter Ego Production Assets</p>
        <h1 class="app-display archive-hero__title">Архив оригиналов</h1>
        <p class="app-subtle">
          Отдельный защищённый раздел для исходных PNG после подтверждённой отправки в Telegram.
          Каждый ассет можно скачать отдельно или забрать весь пакет одним ZIP вместе с `manifest.csv`.
        </p>
      </div>

      <div class="archive-hero__aside">
        <div class="archive-hero__status">
          <span class="archive-hero__status-dot" :class="{ 'archive-hero__status-dot--active': isAuthenticated }"></span>
          <div>
            <p>Состояние</p>
            <strong>{{ isAuthenticated ? assetCountLabel : 'Нужен вход' }}</strong>
          </div>
        </div>

        <div class="archive-hero__actions">
          <a
            v-if="isAuthenticated"
            :href="downloadAllUrl"
            class="app-button"
          >
            <span class="material-symbols-outlined" aria-hidden="true">download</span>
            Скачать всё ZIP
          </a>

          <button
            v-if="isAuthenticated"
            type="button"
            class="app-button-secondary"
            @click="handleLogout"
          >
            Выйти
          </button>
        </div>
      </div>
    </section>

    <section v-if="isLoading && !authChecked" class="app-panel archive-state">
      <div class="archive-state__spinner app-spinner" aria-hidden="true"></div>
      <p>Проверяем доступ к архиву...</p>
    </section>

    <section v-else-if="!isAuthenticated" class="archive-login-layout">
      <article class="app-panel archive-explainer">
        <p class="app-kicker">Separate Access</p>
        <h2 class="app-heading">Организаторский режим</h2>
        <p class="app-subtle">
          Этот пароль открывает только print archive и не связан с основным входом в генератор.
        </p>

        <div class="archive-explainer__items">
          <article class="archive-explainer__item">
            <span>01</span>
            <p>Открывает список исходных PNG, сохранённых после подтверждённой отправки в Telegram.</p>
          </article>
          <article class="archive-explainer__item">
            <span>02</span>
            <p>Позволяет скачать любой оригинал отдельно или весь архив одним ZIP.</p>
          </article>
          <article class="archive-explainer__item">
            <span>03</span>
            <p>Хранит имя, alter ego, дату сохранения и `telegram_message_id` для каждой карточки.</p>
          </article>
        </div>
      </article>

      <article class="app-panel app-panel--strong archive-login">
        <p class="app-kicker">Archive Access</p>
        <h2 class="app-heading">Введите пароль архива</h2>
        <p class="app-subtle">
          После входа можно просматривать ассеты и скачивать production-ready PNG для печати.
        </p>

        <form class="archive-login__form" @submit.prevent="handleLogin">
          <label class="app-field">
            <span class="app-label">Пароль</span>

            <div class="archive-login__password-wrap">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Введите пароль для архива"
                class="app-input"
                :disabled="isSubmitting"
                autofocus
                @input="error = null"
              >

              <button
                type="button"
                class="archive-login__toggle"
                :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <span class="material-symbols-outlined" aria-hidden="true">
                  {{ showPassword ? 'visibility' : 'visibility_off' }}
                </span>
              </button>
            </div>
          </label>

          <div v-if="error" class="app-error">
            {{ error }}
          </div>

          <button
            type="submit"
            class="app-button archive-login__submit"
            :disabled="isSubmitting || !password.trim()"
          >
            <span v-if="isSubmitting" class="app-spinner" aria-hidden="true"></span>
            <span>{{ isSubmitting ? 'Проверяем пароль...' : 'Открыть архив' }}</span>
          </button>
        </form>
      </article>
    </section>

    <template v-else>
      <section class="archive-toolbar">
        <div class="archive-toolbar__left">
          <span class="app-chip app-chip--blue">{{ assetCountLabel }}</span>
          <span class="app-chip app-chip--accent">manifest.csv внутри ZIP</span>
        </div>

        <div class="archive-toolbar__right">
          <span class="app-chip app-chip--mint">Original PNG</span>
        </div>
      </section>

      <section v-if="error" class="app-error">
        {{ error }}
      </section>

      <section v-if="assets.length === 0" class="app-panel archive-state">
        <div class="archive-empty">
          <div class="archive-empty__grid">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div>
            <h2>Архив пока пуст</h2>
            <p>После отправки подтверждённых карточек сюда начнут складываться исходные PNG.</p>
          </div>
        </div>
      </section>

      <section v-else class="archive-grid">
        <article
          v-for="asset in assets"
          :key="asset.asset_id"
          class="app-panel archive-card"
        >
          <div class="archive-card__preview">
            <span class="archive-card__tag">Asset PNG</span>
            <img
              :src="apiClient.getPrintArchiveAssetImageUrl(asset.asset_id)"
              :alt="`Оригинал ${asset.full_name}`"
            >
          </div>

          <div class="archive-card__body">
            <div class="archive-card__header">
              <div>
                <p class="app-kicker">Saved Asset</p>
                <h2>{{ asset.full_name }}</h2>
              </div>

              <span
                class="app-chip"
                :class="asset.delivery_env === 'prod' ? 'app-chip--blue' : 'app-chip--accent'"
              >
                {{ asset.delivery_env ?? 'pending' }}
              </span>
            </div>

            <div class="app-note archive-card__alter-ego">
              {{ asset.alter_ego }}
            </div>

            <div class="app-meta-grid">
              <div class="app-meta-item">
                <p class="app-meta-term">Файл</p>
                <p class="app-meta-value">{{ asset.filename }}</p>
              </div>
              <div class="app-meta-item">
                <p class="app-meta-term">Сохранено</p>
                <p class="app-meta-value">{{ formatDate(asset.created_at) }}</p>
              </div>
              <div class="app-meta-item">
                <p class="app-meta-term">Telegram</p>
                <p class="app-meta-value">
                  {{ asset.telegram_message_id ? `message_id ${asset.telegram_message_id}` : 'ещё не отправлено' }}
                </p>
              </div>
            </div>

            <a
              :href="apiClient.getPrintArchiveAssetDownloadUrl(asset.asset_id)"
              class="app-button-secondary archive-card__download"
            >
              <span class="material-symbols-outlined" aria-hidden="true">download</span>
              Скачать PNG
            </a>
          </div>
        </article>
      </section>
    </template>
  </section>
</template>

<style scoped>
.archive-page {
  display: grid;
  gap: 1.25rem;
}

.archive-headline,
.archive-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.archive-headline__route {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.66rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-soft);
}

.archive-headline__facts,
.archive-toolbar__left,
.archive-toolbar__right {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.archive-hero,
.archive-explainer,
.archive-login,
.archive-state,
.archive-card {
  padding: 1.25rem;
}

.archive-hero {
  display: grid;
  gap: 1rem;
}

.archive-hero__copy {
  display: grid;
  gap: 0.7rem;
}

.archive-hero__title {
  max-width: 9ch;
}

.archive-hero__aside {
  display: grid;
  gap: 1rem;
  align-content: start;
}

.archive-hero__status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border: 1.5px solid var(--black);
  background: rgba(255, 255, 255, 0.88);
}

.archive-hero__status p,
.archive-hero__status strong {
  margin: 0;
}

.archive-hero__status p {
  font-size: 0.58rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-soft);
}

.archive-hero__status strong {
  margin-top: 0.2rem;
  display: block;
  font-size: 0.92rem;
  font-weight: 800;
  text-transform: uppercase;
}

.archive-hero__status-dot {
  width: 0.7rem;
  height: 0.7rem;
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.12);
}

.archive-hero__status-dot--active {
  background: var(--digital-mint);
}

.archive-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.archive-state {
  display: grid;
  place-items: center;
  min-height: 18rem;
  text-align: center;
}

.archive-state p {
  margin: 0;
  color: var(--text-soft);
}

.archive-state__spinner {
  color: var(--digital-blue);
}

.archive-login-layout {
  display: grid;
  gap: 1rem;
}

.archive-explainer,
.archive-login {
  display: grid;
  gap: 1rem;
}

.archive-explainer__items {
  display: grid;
  gap: 0.85rem;
}

.archive-explainer__item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.8rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--line);
}

.archive-explainer__item:first-child {
  padding-top: 0;
  border-top: 0;
}

.archive-explainer__item span {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--digital-blue);
}

.archive-explainer__item p {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.65;
  color: var(--text-soft);
}

.archive-login__form {
  display: grid;
  gap: 1rem;
}

.archive-login__password-wrap {
  position: relative;
}

.archive-login__password-wrap .app-input {
  padding-right: 3.6rem;
}

.archive-login__toggle {
  position: absolute;
  top: 50%;
  right: 0.65rem;
  display: grid;
  place-items: center;
  width: 2.2rem;
  height: 2.2rem;
  border: 0;
  background: transparent;
  color: var(--text-soft);
  transform: translateY(-50%);
}

.archive-login__submit {
  width: 100%;
}

.archive-empty {
  display: grid;
  gap: 1rem;
  justify-items: center;
}

.archive-empty h2,
.archive-empty p {
  margin: 0;
}

.archive-empty h2 {
  font-family: var(--font-display);
  font-size: 1.45rem;
  text-transform: uppercase;
  letter-spacing: -0.05em;
}

.archive-empty p {
  max-width: 28rem;
  font-size: 0.82rem;
  line-height: 1.65;
  color: var(--text-soft);
}

.archive-empty__grid {
  display: grid;
  grid-template-columns: repeat(2, 3.2rem);
  gap: 0.35rem;
}

.archive-empty__grid span {
  width: 3.2rem;
  height: 3.2rem;
  border: 1.5px solid var(--black);
  background: rgba(185, 205, 255, 0.16);
}

.archive-empty__grid span:nth-child(2) {
  background: rgba(130, 255, 240, 0.2);
}

.archive-empty__grid span:nth-child(3) {
  background: rgba(255, 235, 20, 0.2);
}

.archive-empty__grid span:nth-child(4) {
  background: rgba(255, 137, 49, 0.16);
}

.archive-grid {
  display: grid;
  gap: 1rem;
}

.archive-card {
  display: grid;
  gap: 1rem;
}

.archive-card__preview {
  position: relative;
  border: 1.5px solid var(--black);
  background: var(--surface-subtle);
  overflow: hidden;
}

.archive-card__preview img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
}

.archive-card__tag {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  z-index: 1;
  padding: 0.18rem 0.45rem;
  background: var(--accent-yellow);
  font-size: 0.52rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.archive-card__body {
  display: grid;
  gap: 0.9rem;
}

.archive-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
}

.archive-card__header h2 {
  margin: 0.25rem 0 0;
  font-family: var(--font-display);
  font-size: 1.25rem;
  line-height: 1;
  letter-spacing: -0.05em;
  text-transform: uppercase;
}

.archive-card__alter-ego {
  min-height: 4.25rem;
}

.archive-card__download {
  justify-content: center;
}

@media (min-width: 980px) {
  .archive-hero {
    grid-template-columns: minmax(0, 1fr) 18rem;
  }

  .archive-login-layout {
    grid-template-columns: minmax(0, 1fr) minmax(18rem, 24rem);
  }

  .archive-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .archive-hero,
  .archive-explainer,
  .archive-login,
  .archive-state,
  .archive-card {
    padding: 1rem;
  }
}
</style>
