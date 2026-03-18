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
  <div class="print-archive">
    <section class="archive-hero">
      <div class="space-y-3">
        <p class="section-kicker">
          Print Archive
        </p>
        <h1 class="text-3xl font-bold leading-tight text-platform-light sm:text-[2.35rem]">
          Архив оригиналов для печати
        </h1>
        <p class="max-w-3xl text-sm leading-6 text-platform-text-secondary sm:text-[15px]">
          Здесь сохраняются исходные PNG-файлы финально подтвержденных карточек. Можно скачать каждый отдельно или забрать весь архив одним ZIP.
        </p>
      </div>

      <div v-if="isAuthenticated" class="archive-hero__actions">
        <a
          :href="downloadAllUrl"
          class="btn-magic rounded-xl px-5 py-3 font-semibold"
        >
          Скачать всё ZIP
        </a>
        <button
          type="button"
          class="archive-logout rounded-xl border border-platform-line/30 bg-platform-bg-secondary/85 px-5 py-3 font-semibold text-platform-text-primary transition hover:border-platform-accent/30 hover:bg-platform-line/20"
          @click="handleLogout"
        >
          Выйти
        </button>
      </div>
    </section>

    <section v-if="isLoading && !authChecked" class="archive-state">
      <div class="archive-state__icon" aria-hidden="true">⏳</div>
      <p class="text-platform-text-secondary">
        Проверяем доступ к архиву...
      </p>
    </section>

    <section v-else-if="!isAuthenticated" class="archive-login">
      <div class="archive-login__card">
        <div class="space-y-3 text-center">
          <div class="archive-login__icon" aria-hidden="true">🗂️</div>
          <div class="space-y-2">
            <p class="section-kicker">
              Separate Access
            </p>
            <h2 class="text-2xl font-semibold text-platform-light">
              Доступ к архиву печати
            </h2>
            <p class="text-sm leading-6 text-platform-text-secondary">
              Этот раздел защищён отдельным паролем и не зависит от основного входа в генератор.
            </p>
          </div>
        </div>

        <form class="mt-8 space-y-5" @submit.prevent="handleLogin">
          <label class="block space-y-2">
            <span class="text-sm font-semibold text-platform-text-secondary">Пароль</span>

            <div class="relative">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Введите пароль для архива"
                class="archive-input"
                :disabled="isSubmitting"
                autofocus
                @input="error = null"
              />

              <button
                type="button"
                class="archive-toggle"
                :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <span v-if="showPassword">🙈</span>
                <span v-else>👁️</span>
              </button>
            </div>
          </label>

          <div v-if="error" class="archive-error">
            {{ error }}
          </div>

          <button
            type="submit"
            class="btn-magic w-full rounded-xl px-6 py-4 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="isSubmitting || !password.trim()"
          >
            <span class="flex items-center justify-center gap-2">
              <span v-if="isSubmitting" class="loading loading-spinner loading-sm"></span>
              <span>{{ isSubmitting ? 'Проверяем пароль...' : 'Открыть архив' }}</span>
            </span>
          </button>
        </form>
      </div>
    </section>

    <template v-else>
      <div class="archive-summary">
        <div>
          <p class="text-xs uppercase tracking-[0.18em] text-platform-text-muted">
            Сохранено
          </p>
          <p class="mt-2 text-2xl font-semibold text-platform-light">
            {{ assetCountLabel }}
          </p>
        </div>

        <div class="archive-summary__note">
          В ZIP архив дополнительно вкладывается `manifest.csv` с подписями.
        </div>
      </div>

      <section v-if="error" class="archive-error archive-error--full">
        {{ error }}
      </section>

      <section v-if="assets.length === 0" class="archive-state">
        <div class="archive-state__icon" aria-hidden="true">🖨️</div>
        <div class="space-y-2 text-center">
          <p class="text-lg font-semibold text-platform-text-primary">
            Архив пока пуст
          </p>
          <p class="max-w-md text-sm leading-6 text-platform-text-secondary">
            Здесь появятся исходные PNG после того, как карточка будет финально подтверждена и отправлена в Telegram.
          </p>
        </div>
      </section>

      <section v-else class="archive-grid">
        <article
          v-for="asset in assets"
          :key="asset.asset_id"
          class="archive-card"
        >
          <div class="archive-card__media">
            <img
              :src="apiClient.getPrintArchiveAssetImageUrl(asset.asset_id)"
              :alt="`Оригинал ${asset.full_name}`"
              class="h-full w-full object-cover"
            />
          </div>

          <div class="archive-card__body">
            <div class="space-y-2">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-platform-text-muted">
                    Имя
                  </p>
                  <h2 class="mt-1 text-xl font-semibold text-platform-light">
                    {{ asset.full_name }}
                  </h2>
                </div>

                <span class="archive-badge">
                  {{ asset.delivery_env ?? 'pending' }}
                </span>
              </div>

              <div>
                <p class="text-xs uppercase tracking-[0.18em] text-platform-text-muted">
                  Альтер-эго
                </p>
                <p class="mt-1 whitespace-pre-wrap text-platform-text-secondary">
                  {{ asset.alter_ego }}
                </p>
              </div>
            </div>

            <dl class="archive-meta">
              <div>
                <dt>Сохранено</dt>
                <dd>{{ formatDate(asset.created_at) }}</dd>
              </div>
              <div>
                <dt>Файл</dt>
                <dd>{{ asset.filename }}</dd>
              </div>
              <div>
                <dt>Telegram</dt>
                <dd>{{ asset.telegram_message_id ? `message_id ${asset.telegram_message_id}` : 'ещё не отправлено' }}</dd>
              </div>
            </dl>

            <div class="archive-card__actions">
              <a
                :href="apiClient.getPrintArchiveAssetDownloadUrl(asset.asset_id)"
                class="btn-magic rounded-xl px-5 py-3 text-center font-semibold"
              >
                Скачать PNG
              </a>
            </div>
          </div>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.print-archive {
  display: grid;
  gap: 1.5rem;
}

.archive-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.5rem;
  border: 1px solid rgba(77, 154, 255, 0.18);
  border-radius: 1.75rem;
  background:
    radial-gradient(circle at top right, rgba(77, 154, 255, 0.16), transparent 34%),
    linear-gradient(135deg, rgba(19, 35, 61, 0.95) 0%, rgba(12, 25, 46, 0.92) 100%);
}

.archive-hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.archive-logout {
  min-width: 9rem;
}

.archive-login {
  display: grid;
  place-items: center;
}

.archive-login__card {
  width: min(100%, 32rem);
  padding: clamp(1.5rem, 4vw, 2.5rem);
  border: 1px solid rgba(77, 154, 255, 0.2);
  border-radius: 1.75rem;
  background:
    radial-gradient(circle at top center, rgba(77, 154, 255, 0.16), transparent 32%),
    linear-gradient(135deg, rgba(17, 31, 56, 0.96) 0%, rgba(10, 22, 40, 0.94) 100%);
  box-shadow:
    0 30px 80px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.archive-login__icon,
.archive-state__icon {
  display: grid;
  place-items: center;
  width: 4rem;
  height: 4rem;
  margin: 0 auto;
  border-radius: 999px;
  background: rgba(77, 154, 255, 0.16);
  font-size: 1.8rem;
}

.archive-input {
  width: 100%;
  min-height: 3.5rem;
  padding: 0 3.5rem 0 1rem;
  border: 1px solid rgba(77, 154, 255, 0.24);
  border-radius: 1rem;
  background: rgba(15, 31, 56, 0.88);
  color: #f0f8ff;
}

.archive-input:focus {
  outline: none;
  border-color: rgba(77, 154, 255, 0.5);
  box-shadow: 0 0 0 4px rgba(77, 154, 255, 0.08);
}

.archive-toggle {
  position: absolute;
  top: 50%;
  right: 0.875rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-muted);
  transform: translateY(-50%);
}

.archive-error {
  padding: 0.875rem 1rem;
  border: 1px solid rgba(241, 90, 90, 0.28);
  border-radius: 1rem;
  background: rgba(241, 90, 90, 0.1);
  color: #ffd1d1;
}

.archive-error--full {
  margin-top: -0.5rem;
}

.archive-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 1.5rem;
  background: rgba(15, 24, 42, 0.72);
}

.archive-summary__note {
  max-width: 28rem;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  line-height: 1.55;
}

.archive-state {
  display: grid;
  gap: 1rem;
  place-items: center;
  min-height: 18rem;
  padding: 1.5rem;
  border: 1px dashed rgba(255, 255, 255, 0.14);
  border-radius: 1.5rem;
  background: rgba(13, 23, 42, 0.5);
}

.archive-grid {
  display: grid;
  gap: 1.25rem;
}

.archive-card {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1.5rem;
  background:
    linear-gradient(135deg, rgba(20, 33, 58, 0.94) 0%, rgba(12, 22, 40, 0.9) 100%);
}

.archive-card__media {
  overflow: hidden;
  border-radius: 1.2rem;
  aspect-ratio: 1 / 1;
  background: rgba(255, 255, 255, 0.04);
}

.archive-card__body {
  display: grid;
  gap: 1rem;
}

.archive-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 5.5rem;
  padding: 0.35rem 0.7rem;
  border: 1px solid rgba(77, 154, 255, 0.22);
  border-radius: 999px;
  color: #c7ddff;
  background: rgba(77, 154, 255, 0.12);
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.archive-meta {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 1rem;
  background: rgba(9, 17, 31, 0.5);
}

.archive-meta div {
  display: grid;
  gap: 0.2rem;
}

.archive-meta dt {
  color: var(--color-text-muted);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

.archive-meta dd {
  margin: 0;
  color: var(--color-text-secondary);
  word-break: break-word;
}

.archive-card__actions {
  display: flex;
}

.archive-card__actions > a {
  width: 100%;
}

@media (min-width: 900px) {
  .archive-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .archive-card {
    grid-template-columns: minmax(0, 18rem) minmax(0, 1fr);
    align-items: start;
  }

  .archive-card__media {
    aspect-ratio: 4 / 5;
  }
}
</style>
