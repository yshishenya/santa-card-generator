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
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="glass-card p-8 w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="text-6xl mb-4">🎅</div>
        <h1 class="text-2xl font-bold text-winter-snow mb-2">
          Новогодняя открытка
        </h1>
        <p class="text-winter-snow/70">
          Введите пароль для доступа
        </p>
      </div>

      <!-- Login form -->
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Password input -->
        <div class="form-control">
          <label class="label">
            <span class="label-text text-winter-snow">Пароль</span>
          </label>
          <div class="relative">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Введите пароль"
              class="input input-bordered w-full bg-white/10 border-white/20 text-winter-snow placeholder:text-winter-snow/50 pr-12"
              :disabled="authStore.isLoading"
              autofocus
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-winter-snow/60 hover:text-winter-snow"
              @click="showPassword = !showPassword"
            >
              <span v-if="showPassword">👁️</span>
              <span v-else>👁️‍🗨️</span>
            </button>
          </div>
        </div>

        <!-- Error message -->
        <div v-if="authStore.error" class="alert alert-error">
          <span>{{ authStore.error }}</span>
        </div>

        <!-- Submit button -->
        <button
          type="submit"
          class="btn btn-primary w-full"
          :class="{ 'loading': authStore.isLoading }"
          :disabled="authStore.isLoading || !password.trim()"
        >
          <span v-if="!authStore.isLoading">Войти</span>
          <span v-else>Проверка...</span>
        </button>
      </form>
    </div>
  </div>
</template>
