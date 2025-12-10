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
  <div class="login-container">
    <!-- Blue ambient glow background -->
    <div class="login-bg">
      <div class="ambient-glow ambient-glow-1"></div>
      <div class="ambient-glow ambient-glow-2"></div>
      <div class="ambient-glow ambient-glow-3"></div>
    </div>

    <!-- Twinkling stars -->
    <div class="stars">
      <span class="star star-1">&#10022;</span>
      <span class="star star-2">&#10022;</span>
      <span class="star star-3">&#10022;</span>
      <span class="star star-4">&#10022;</span>
      <span class="star star-5">&#10022;</span>
    </div>

    <!-- Login card -->
    <div class="login-card">
      <!-- Header -->
      <div class="text-center mb-10">
        <div class="icon-container">
          <span class="text-6xl animate-float">🎅</span>
          <div class="sparkles">
            <span class="sparkle-item">✨</span>
            <span class="sparkle-item delay-1">✨</span>
            <span class="sparkle-item delay-2">✨</span>
          </div>
        </div>
        <h1 class="text-3xl font-bold text-gradient mb-3">
          Новогодняя открытка
        </h1>
        <p class="text-winter-secondary text-lg">
          Введите пароль для доступа
        </p>
      </div>

      <!-- Login form -->
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Password input -->
        <div class="form-control">
          <label class="label">
            <span class="label-text text-winter-secondary font-medium">Пароль</span>
          </label>
          <div class="relative group">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Введите пароль"
              class="input-field"
              :disabled="authStore.isLoading"
              autofocus
            />
            <button
              type="button"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-winter-muted hover:text-winter-snow transition-colors text-xl"
              @click="showPassword = !showPassword"
            >
              <span v-if="showPassword">👁️</span>
              <span v-else>👁️‍🗨️</span>
            </button>
            <!-- Input glow effect on focus -->
            <div class="input-glow"></div>
          </div>
        </div>

        <!-- Error message -->
        <div v-if="authStore.error" class="error-message">
          <span class="text-lg">⚠️</span>
          <span>{{ authStore.error }}</span>
        </div>

        <!-- Submit button -->
        <button
          type="submit"
          class="submit-btn"
          :class="{ 'loading': authStore.isLoading }"
          :disabled="authStore.isLoading || !password.trim()"
        >
          <span v-if="!authStore.isLoading" class="btn-content">
            <span>Войти</span>
            <span class="btn-icon">→</span>
          </span>
          <span v-else class="btn-content">
            <span class="loading-spinner"></span>
            <span>Проверка...</span>
          </span>
        </button>
      </form>

      <!-- Footer decoration -->
      <div class="mt-8 text-center">
        <div class="flex items-center justify-center gap-3 text-winter-muted text-sm">
          <span>❄️</span>
          <span>С Новым Годом 2025!</span>
          <span>❄️</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/*
 * LoginView.vue - Standalone login page styles
 *
 * Global utilities used from main.css:
 * - .text-gradient (blue gradient text)
 * - CSS variables (--color-*)
 *
 * This page has its own background/glow effects separate from App.vue
 * to provide a unique first-impression experience.
 */

.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #050D18 0%, #0B1929 30%, #122640 60%, #1A3355 100%);
}

.login-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

/* Blue ambient glow orbs - consistent naming with App.vue */
.ambient-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  animation: ambientPulse 8s ease-in-out infinite;
}

.ambient-glow-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(51, 130, 254, 0.25) 0%, transparent 70%);
  bottom: -100px;
  left: -100px;
}

.ambient-glow-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(77, 154, 255, 0.2) 0%, transparent 70%);
  bottom: 20%;
  right: -50px;
  animation-delay: -3s;
}

.ambient-glow-3 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(122, 180, 255, 0.15) 0%, transparent 70%);
  top: 20%;
  left: 10%;
  animation-delay: -5s;
}

@keyframes ambientPulse {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

/* Twinkling stars */
.stars {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.star {
  position: absolute;
  color: #FFFEF0;
  animation: twinkleStar 3s ease-in-out infinite;
  filter: drop-shadow(0 0 6px rgba(255, 255, 240, 0.9));
}

.star-1 {
  top: 10%;
  left: 15%;
  font-size: 14px;
  animation-delay: 0s;
}

.star-2 {
  top: 15%;
  right: 20%;
  font-size: 18px;
  animation-delay: 0.7s;
}

.star-3 {
  top: 5%;
  left: 40%;
  font-size: 12px;
  animation-delay: 1.4s;
}

.star-4 {
  top: 25%;
  right: 35%;
  font-size: 16px;
  animation-delay: 0.3s;
}

.star-5 {
  top: 8%;
  right: 10%;
  font-size: 14px;
  animation-delay: 1s;
}

@keyframes twinkleStar {
  0%, 100% {
    opacity: 0.4;
    transform: scale(0.8);
    filter: drop-shadow(0 0 3px rgba(255, 255, 240, 0.5));
  }
  50% {
    opacity: 1;
    transform: scale(1);
    filter: drop-shadow(0 0 8px rgba(255, 255, 240, 1));
  }
}

.login-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: 3rem;
  background: linear-gradient(
    135deg,
    rgba(26, 51, 85, 0.92) 0%,
    rgba(18, 38, 64, 0.88) 100%
  );
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(51, 130, 254, 0.2);
  border-radius: 32px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 80px rgba(51, 130, 254, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Blue gradient border */
.login-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 32px;
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

.icon-container {
  position: relative;
  display: inline-block;
  margin-bottom: 1.5rem;
}

.animate-float {
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.sparkles {
  position: absolute;
  inset: -20px;
  pointer-events: none;
}

.sparkle-item {
  position: absolute;
  font-size: 14px;
  animation: sparkleAnim 2s ease-in-out infinite;
}

.sparkle-item:nth-child(1) { top: 0; right: 0; }
.sparkle-item:nth-child(2) { bottom: 10px; left: 0; animation-delay: 0.5s; }
.sparkle-item:nth-child(3) { top: 50%; right: -15px; animation-delay: 1s; }

.delay-1 { animation-delay: 0.5s; }
.delay-2 { animation-delay: 1s; }

@keyframes sparkleAnim {
  0%, 100% { opacity: 0; transform: scale(0.5); }
  50% { opacity: 1; transform: scale(1); }
}

/* NOTE: .text-gradient is defined globally in main.css */

/* Page-specific text color utilities (shortcuts for tailwind classes) */
.text-winter-secondary {
  color: #B8D4F0;  /* Same as var(--color-text-secondary) */
}

.text-winter-muted {
  color: #7BA3CC;  /* Same as var(--color-text-muted) */
}

.input-field {
  width: 100%;
  height: 56px;
  padding: 0 1.25rem;
  padding-right: 3.5rem;
  background: rgba(26, 51, 85, 0.8);
  border: 1px solid rgba(51, 130, 254, 0.2);
  border-radius: 16px;
  color: #F0F8FF;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.input-field:focus {
  background: rgba(30, 58, 95, 0.9);
  border-color: rgba(51, 130, 254, 0.5);
  outline: none;
  box-shadow: 0 0 20px rgba(51, 130, 254, 0.2);
}

.input-field::placeholder {
  color: #7BA3CC;
}

.input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.group:focus-within .input-glow {
  opacity: 1;
}

.input-glow {
  position: absolute;
  inset: -2px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(51, 130, 254, 0.2), rgba(77, 154, 255, 0.15));
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
  filter: blur(8px);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: rgba(226, 85, 85, 0.15);
  border: 1px solid rgba(226, 85, 85, 0.3);
  border-radius: 12px;
  color: #FF9999;
  font-size: 0.95rem;
}

.submit-btn {
  width: 100%;
  height: 56px;
  background: linear-gradient(135deg, #4D9AFF 0%, #3382FE 100%);
  border: none;
  border-radius: 16px;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 15px 40px rgba(51, 130, 254, 0.4),
    0 0 20px rgba(51, 130, 254, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
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
  width: 20px;
  height: 20px;
  border: 2px solid rgba(11, 25, 41, 0.3);
  border-top-color: #0B1929;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
