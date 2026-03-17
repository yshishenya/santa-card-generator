<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()

const deliveryEnv = computed(() => route.query.env === 'prod' ? 'prod' : 'staging')
const messageId = computed(() => {
  const rawValue = route.query.message_id
  return typeof rawValue === 'string' && rawValue.length > 0 ? rawValue : null
})

let redirectTimeout: ReturnType<typeof setTimeout> | null = null

function goHome(): void {
  if (redirectTimeout) {
    clearTimeout(redirectTimeout)
  }
  router.push('/')
}

onMounted(() => {
  redirectTimeout = setTimeout(() => {
    goHome()
  }, 5000)
})

onUnmounted(() => {
  if (redirectTimeout) {
    clearTimeout(redirectTimeout)
  }
})
</script>

<template>
  <div class="space-y-8 py-12 text-center">
    <div class="flex justify-center">
      <div class="flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-platform-accent to-platform-primary shadow-lg shadow-platform-accent/30">
        <i class="pi pi-check text-5xl text-white"></i>
      </div>
    </div>

    <div class="space-y-4">
      <h1 class="text-4xl md:text-5xl font-bold text-gradient">
        Фотокарточка отправлена
      </h1>
      <p class="mx-auto max-w-2xl text-xl text-platform-text-secondary">
        Telegram delivery завершён в окружении <span class="font-semibold text-platform-accent">{{ deliveryEnv }}</span>.
      </p>
      <p v-if="messageId" class="text-sm text-platform-text-muted">
        message_id: {{ messageId }}
      </p>
    </div>

    <div class="flex justify-center gap-4 text-3xl">
      <span class="animate-float">🧭</span>
      <span class="animate-float" style="animation-delay: 0.2s">📸</span>
    </div>

    <div class="pt-4">
      <button
        class="btn-magic rounded-xl px-8 py-4 text-lg font-semibold"
        @click="goHome"
      >
        Сгенерировать ещё одну
      </button>
    </div>

    <p class="text-sm text-platform-text-muted">
      Автоматический переход на главную через 5 секунд.
    </p>
  </div>
</template>
