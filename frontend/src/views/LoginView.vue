<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const password = ref('')
const showPassword = ref(false)

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
  <article class="login-card">
    <header class="space-y-6 text-center">
      <div class="login-icon" aria-hidden="true">🔐</div>

      <div class="space-y-3">
        <p class="login-eyebrow">Protected access</p>
        <h1 class="login-title text-gradient">
          Платформа фотокарточек Pro 4.0
        </h1>
        <p class="login-subtitle">
          Введите пароль для доступа к генерации и отправке фотокарточек.
        </p>
      </div>
    </header>

    <form class="mt-8 space-y-5" @submit.prevent="handleSubmit">
      <label class="block space-y-2">
        <span class="text-sm font-semibold text-platform-text-secondary">Пароль</span>

        <div class="relative">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Введите пароль"
            class="input-field"
            :disabled="authStore.isLoading"
            autofocus
            @input="authStore.clearError()"
          />

          <button
            type="button"
            class="toggle-btn"
            :aria-label="showPassword ? 'Скрыть пароль' : 'Показать пароль'"
            @click="showPassword = !showPassword"
          >
            <span v-if="showPassword">🙈</span>
            <span v-else>👁️</span>
          </button>
        </div>
      </label>

      <div v-if="authStore.error" class="error-message">
        <span aria-hidden="true">⚠️</span>
        <span>{{ authStore.error }}</span>
      </div>

      <button
        type="submit"
        class="submit-btn"
        :disabled="authStore.isLoading || !password.trim()"
      >
        <span v-if="!authStore.isLoading" class="btn-content">
          <span>Войти</span>
          <span class="btn-icon" aria-hidden="true">→</span>
        </span>

        <span v-else class="btn-content">
          <span class="loading-spinner" aria-hidden="true"></span>
          <span>Проверяем пароль...</span>
        </span>
      </button>
    </form>
  </article>
</template>

<style scoped>
.login-card {
  position: relative;
  width: 100%;
  padding: clamp(1.5rem, 5vw, 3rem);
  border: 1px solid rgba(51, 130, 254, 0.22);
  border-radius: 28px;
  background: linear-gradient(
    135deg,
    rgba(26, 51, 85, 0.92) 0%,
    rgba(18, 38, 64, 0.88) 100%
  );
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.45),
    0 0 80px rgba(51, 130, 254, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.login-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 28px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(77, 154, 255, 0.3) 0%,
    rgba(51, 130, 254, 0.4) 50%,
    rgba(77, 154, 255, 0.3) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.login-icon {
  display: grid;
  place-items: center;
  width: 4.5rem;
  height: 4.5rem;
  margin: 0 auto;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(77, 154, 255, 0.2), rgba(99, 102, 241, 0.3));
  box-shadow: 0 12px 30px rgba(51, 130, 254, 0.18);
  font-size: 2rem;
}

.login-eyebrow {
  margin: 0;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.login-title {
  margin: 0;
  font-size: clamp(2rem, 7vw, 3rem);
  line-height: 1.05;
  text-wrap: balance;
}

.login-subtitle {
  margin: 0 auto;
  max-width: 26rem;
  font-size: clamp(1rem, 3.5vw, 1.125rem);
  line-height: 1.55;
  color: var(--color-text-secondary);
}

.input-field {
  width: 100%;
  min-height: 3.5rem;
  padding: 0 3.5rem 0 1rem;
  border: 1px solid rgba(51, 130, 254, 0.24);
  border-radius: 16px;
  background: rgba(26, 51, 85, 0.8);
  color: #f0f8ff;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.input-field:focus {
  border-color: rgba(51, 130, 254, 0.5);
  outline: none;
  background: rgba(30, 58, 95, 0.9);
  box-shadow: 0 0 20px rgba(51, 130, 254, 0.2);
}

.input-field::placeholder {
  color: #94a3b8;
}

.input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.toggle-btn {
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
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease;
}

.toggle-btn:hover {
  color: var(--color-platform-light);
  background: rgba(148, 163, 184, 0.12);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border: 1px solid rgba(226, 85, 85, 0.3);
  border-radius: 14px;
  background: rgba(226, 85, 85, 0.15);
  color: #ff9999;
  font-size: 0.95rem;
}

.submit-btn {
  position: relative;
  width: 100%;
  min-height: 3.5rem;
  border: 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #4d9aff 0%, #3382fe 100%);
  color: #ffffff;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease, opacity 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 15px 40px rgba(51, 130, 254, 0.35),
    0 0 20px rgba(51, 130, 254, 0.25);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.btn-icon {
  transition: transform 0.3s ease;
}

.submit-btn:hover:not(:disabled) .btn-icon {
  transform: translateX(4px);
}

.loading-spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(11, 25, 41, 0.3);
  border-top-color: #0b1929;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .login-card,
  .login-card::before {
    border-radius: 24px;
  }

  .login-eyebrow {
    letter-spacing: 0.18em;
  }
}
</style>
