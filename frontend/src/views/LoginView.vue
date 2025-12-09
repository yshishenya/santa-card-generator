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
    <!-- Animated background -->
    <div class="login-bg">
      <div class="aurora-orb aurora-orb-1"></div>
      <div class="aurora-orb aurora-orb-2"></div>
      <div class="aurora-orb aurora-orb-3"></div>
    </div>

    <!-- Login card -->
    <div class="login-card">
      <!-- Decorative elements -->
      <div class="card-glow"></div>

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
        <p class="text-winter-snow/60 text-lg">
          Введите пароль для доступа
        </p>
      </div>

      <!-- Login form -->
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Password input -->
        <div class="form-control">
          <label class="label">
            <span class="label-text text-winter-snow/80 font-medium">Пароль</span>
          </label>
          <div class="relative group">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Введите пароль"
              class="input-magic w-full h-14 px-5 pr-14 text-lg"
              :disabled="authStore.isLoading"
              autofocus
            />
            <button
              type="button"
              class="absolute right-4 top-1/2 -translate-y-1/2 text-winter-snow/40 hover:text-winter-snow transition-colors text-xl"
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
        <div class="flex items-center justify-center gap-3 text-winter-snow/30 text-sm">
          <span>❄️</span>
          <span>С Новым Годом 2025!</span>
          <span>❄️</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #0A0E1A 0%, #0F1629 50%, #141B2D 100%);
}

.login-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.aurora-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  animation: floatOrb 25s ease-in-out infinite;
}

.aurora-orb-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.5) 0%, transparent 70%);
  top: -150px;
  left: -150px;
}

.aurora-orb-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(34, 211, 238, 0.4) 0%, transparent 70%);
  bottom: -100px;
  right: -100px;
  animation-delay: -8s;
}

.aurora-orb-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(236, 72, 153, 0.3) 0%, transparent 70%);
  top: 50%;
  right: 20%;
  animation-delay: -16s;
}

@keyframes floatOrb {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(50px, -50px) scale(1.1); }
  66% { transform: translate(-30px, 30px) scale(0.9); }
}

.login-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  padding: 3rem;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.12) 0%,
    rgba(255, 255, 255, 0.05) 100%
  );
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 32px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 100px rgba(168, 85, 247, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.card-glow {
  position: absolute;
  inset: -1px;
  border-radius: 33px;
  background: linear-gradient(
    135deg,
    rgba(168, 85, 247, 0.3) 0%,
    rgba(34, 211, 238, 0.2) 50%,
    rgba(236, 72, 153, 0.3) 100%
  );
  z-index: -1;
  opacity: 0.5;
  filter: blur(20px);
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

.text-gradient {
  background: linear-gradient(135deg, #A855F7 0%, #22D3EE 50%, #EC4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.input-magic {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  color: #F8FAFC;
  transition: all 0.3s ease;
  font-size: 1rem;
}

.input-magic:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(168, 85, 247, 0.5);
  outline: none;
}

.input-magic::placeholder {
  color: rgba(248, 250, 252, 0.35);
}

.input-magic:disabled {
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
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.3), rgba(34, 211, 238, 0.3));
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
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  color: #FCA5A5;
  font-size: 0.95rem;
}

.submit-btn {
  width: 100%;
  height: 56px;
  background: linear-gradient(135deg, #A855F7 0%, #EC4899 100%);
  border: none;
  border-radius: 16px;
  color: white;
  font-weight: 600;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 15px 40px rgba(168, 85, 247, 0.4);
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
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
