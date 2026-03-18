<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const password = ref('')
const showPassword = ref(false)

const processSteps = [
  {
    index: '1',
    accentClass: 'login-guide__step-index--lavender',
    title: 'Пара слов о себе',
    body: 'Хобби, роль или вайб вне работы.',
  },
  {
    index: '2',
    accentClass: 'login-guide__step-index--mint',
    title: 'Выберите лучшую',
    body: 'Из 3 картинок берёте ту самую.',
  },
  {
    index: '3',
    accentClass: 'login-guide__step-index--yellow',
    title: 'Отправьте в чат',
    body: 'Улетят картинка и имя. Без лишней драмы.',
  },
] as const

async function handleSubmit() {
  if (!password.value.trim()) {
    return
  }

  const success = await authStore.login(password.value)
  if (success) {
    router.push('/')
  }
}
</script>

<template>
  <section class="login-page">
    <header class="login-bar">
      <div class="login-bar__brand">
        <span class="login-bar__title">P4.0 Alter Ego</span>
        <div class="login-bar__divider"></div>
        <span class="login-bar__subtitle">Генератор портретов</span>
      </div>

      <div class="login-bar__colors" aria-hidden="true">
        <span class="login-bar__swatch login-bar__swatch--blue"></span>
        <span class="login-bar__swatch login-bar__swatch--lavender"></span>
        <span class="login-bar__swatch login-bar__swatch--mint"></span>
        <span class="login-bar__swatch login-bar__swatch--yellow"></span>
      </div>
    </header>

    <article class="app-panel app-panel--strong login-bento">
      <section class="login-bento__auth">
        <div class="login-bento__badge">Доступ ограничен</div>

        <div class="login-bento__heading">
          <h1 class="login-bento__title">Вход в систему</h1>
          <p class="app-subtle">
            Защищённый доступ в студию alter ego для команды и приглашённых гостей.
          </p>
        </div>

        <form class="login-bento__form" @submit.prevent="handleSubmit">
          <label class="app-field">
            <span class="app-label">Пароль</span>

            <div class="login-bento__password-wrap">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                class="app-input"
                :disabled="authStore.isLoading"
                autofocus
                @input="authStore.clearError()"
              >

              <button
                type="button"
                class="login-bento__toggle"
                :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
                @click="showPassword = !showPassword"
              >
                <span class="material-symbols-outlined" aria-hidden="true">
                  {{ showPassword ? 'visibility' : 'visibility_off' }}
                </span>
              </button>
            </div>
          </label>

          <div v-if="authStore.error" class="app-error">
            {{ authStore.error }}
          </div>

          <button
            type="submit"
            class="app-button login-bento__submit"
            :disabled="authStore.isLoading || !password.trim()"
          >
            <span v-if="authStore.isLoading" class="app-spinner" aria-hidden="true"></span>
            <span v-else class="material-symbols-outlined" aria-hidden="true">arrow_forward</span>
            <span>{{ authStore.isLoading ? 'Проверяем пароль...' : 'Войти' }}</span>
          </button>
        </form>

        <div class="login-bento__micro">
          <span class="login-bento__micro-box"></span>
          <span class="login-bento__micro-box login-bento__micro-box--muted"></span>
        </div>
      </section>

      <section class="login-guide">
        <div class="login-guide__top">
          <h2 class="app-heading">Как это работает</h2>

          <div class="login-guide__steps">
            <article
              v-for="step in processSteps"
              :key="step.title"
              class="login-guide__step"
            >
              <div class="login-guide__step-index" :class="step.accentClass">
                {{ step.index }}
              </div>
              <h3>{{ step.title }}</h3>
              <p>{{ step.body }}</p>
            </article>
          </div>
        </div>

        <div class="login-guide__bottom">
          <div class="login-guide__mosaic">
            <div class="login-guide__mosaic-grid">
              <span></span>
              <span class="login-guide__mosaic-grid-cell--blue"></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span class="login-guide__mosaic-grid-cell--lavender"></span>
              <span></span>
              <span class="login-guide__mosaic-grid-cell--mint"></span>
              <span></span>
              <span></span>
              <span class="login-guide__mosaic-grid-cell--yellow"></span>
              <span></span>
              <span class="login-guide__mosaic-grid-cell--black"></span>
              <span></span>
              <span></span>
            </div>
          </div>

          <div class="login-guide__status">
            <div>
              <p>SYSTEM_STATUS: ACTIVE</p>
              <p>CORE_LOAD: 12%</p>
              <p>GEN_READY: TRUE</p>
            </div>

            <strong>4.0</strong>
          </div>
        </div>
      </section>
    </article>

  </section>
</template>

<style scoped>
.login-page {
  display: grid;
  gap: 1.5rem;
}

.login-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1.5px solid var(--black);
}

.login-bar__brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.login-bar__title,
.login-bar__subtitle {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.login-bar__divider {
  width: 1px;
  height: 1rem;
  background: var(--black);
}

.login-bar__subtitle {
  color: var(--text-soft);
}

.login-bar__colors {
  display: inline-flex;
  gap: 0.28rem;
}

.login-bar__swatch {
  width: 0.48rem;
  height: 0.48rem;
}

.login-bar__swatch--blue {
  background: var(--digital-blue);
}

.login-bar__swatch--lavender {
  background: var(--soft-lavender);
}

.login-bar__swatch--mint {
  background: var(--digital-mint);
}

.login-bar__swatch--yellow {
  background: var(--accent-yellow);
}

.login-bento {
  display: grid;
  background: var(--white);
}

.login-bento__auth,
.login-guide__top,
.login-guide__bottom {
  padding: 1.5rem;
}

.login-bento__auth {
  display: grid;
  gap: 1.25rem;
}

.login-bento__badge {
  display: inline-flex;
  justify-self: start;
  padding: 0.25rem 0.45rem;
  background: var(--accent-yellow);
  font-size: 0.54rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.login-bento__heading {
  display: grid;
  gap: 0.6rem;
}

.login-bento__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 0.9;
  letter-spacing: -0.08em;
  text-transform: uppercase;
}

.login-bento__form {
  display: grid;
  gap: 1rem;
}

.login-bento__password-wrap {
  position: relative;
}

.login-bento__password-wrap .app-input {
  padding-right: 3.6rem;
}

.login-bento__toggle {
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

.login-bento__submit {
  justify-content: space-between;
  width: 100%;
}

.login-bento__micro {
  display: flex;
  gap: 0.55rem;
  margin-top: auto;
  opacity: 0.45;
}

.login-bento__micro-box {
  width: 0.9rem;
  height: 0.9rem;
  background: rgba(0, 0, 0, 0.12);
}

.login-bento__micro-box--muted {
  background: rgba(0, 0, 0, 0.05);
}

.login-guide {
  display: grid;
  border-top: 1.5px solid var(--black);
}

.login-guide__top {
  display: grid;
  gap: 1rem;
}

.login-guide__steps {
  display: grid;
  gap: 1rem;
}

.login-guide__step {
  display: grid;
  gap: 0.5rem;
}

.login-guide__step-index {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border: 1.5px solid var(--black);
  font-size: 0.75rem;
  font-weight: 800;
}

.login-guide__step-index--lavender {
  background: var(--soft-lavender);
}

.login-guide__step-index--mint {
  background: var(--digital-mint);
}

.login-guide__step-index--yellow {
  background: var(--accent-yellow);
}

.login-guide__step h3,
.login-guide__step p {
  margin: 0;
}

.login-guide__step h3 {
  font-size: 0.78rem;
  font-weight: 800;
  line-height: 1.4;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.login-guide__step p {
  font-size: 0.72rem;
  line-height: 1.6;
  color: var(--text-soft);
}

.login-guide__bottom {
  display: grid;
  gap: 0;
  border-top: 1.5px solid var(--black);
}

.login-guide__mosaic {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 15rem;
  border-bottom: 1.5px solid var(--black);
  background:
    radial-gradient(rgba(0, 0, 0, 0.06) 1px, transparent 1px),
    var(--surface-page);
  background-size: 1rem 1rem;
}

.login-guide__mosaic::before {
  content: '';
  position: absolute;
  inset: 1rem;
  border: 1px dashed rgba(0, 0, 0, 0.12);
}

.login-guide__mosaic-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4, 2.35rem);
  gap: 0.3rem;
}

.login-guide__mosaic-grid span {
  width: 2.35rem;
  height: 2.35rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.78);
}

.login-guide__mosaic-grid-cell--blue {
  background: var(--digital-blue);
}

.login-guide__mosaic-grid-cell--lavender {
  background: var(--soft-lavender);
}

.login-guide__mosaic-grid-cell--mint {
  background: var(--digital-mint);
}

.login-guide__mosaic-grid-cell--yellow {
  background: var(--accent-yellow);
}

.login-guide__mosaic-grid-cell--black {
  background: var(--black);
}

.login-guide__status {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  background: var(--black);
  color: var(--white);
}

.login-guide__status p,
.login-guide__status strong {
  margin: 0;
}

.login-guide__status p {
  font-size: 0.56rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.64);
}

.login-guide__status strong {
  font-family: var(--font-display);
  font-size: 2rem;
  line-height: 1;
  letter-spacing: -0.08em;
}

@media (min-width: 980px) {
  .login-bento {
    grid-template-columns: minmax(18rem, 24rem) minmax(0, 1fr);
  }

  .login-bento__auth {
    border-right: 1.5px solid var(--black);
  }

  .login-guide__steps {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .login-guide__bottom {
    grid-template-columns: minmax(0, 1fr) 13rem;
  }

  .login-guide__mosaic {
    border-right: 1.5px solid var(--black);
    border-bottom: 0;
  }
}

@media (max-width: 979px) {
  .login-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 767px) {
  .login-page {
    gap: 1rem;
  }

  .login-bento__auth,
  .login-guide__top,
  .login-guide__bottom {
    padding: 1rem;
  }
}
</style>
