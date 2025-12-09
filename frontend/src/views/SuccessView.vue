<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCardStore } from '@/stores/card'

const router = useRouter()
const cardStore = useCardStore()

let redirectTimeout: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  // Auto redirect to home after 5 seconds
  redirectTimeout = setTimeout(() => {
    cardStore.reset()
    router.push('/')
  }, 5000)
})

onUnmounted(() => {
  // Clear timeout to prevent memory leak
  if (redirectTimeout) {
    clearTimeout(redirectTimeout)
  }
})

const createAnother = (): void => {
  if (redirectTimeout) {
    clearTimeout(redirectTimeout)
  }
  cardStore.reset()
  router.push('/')
}
</script>

<template>
  <div class="text-center space-y-8 py-12">
    <!-- Success icon -->
    <div class="flex justify-center">
      <div class="w-24 h-24 bg-gradient-to-br from-aurora-purple to-aurora-cyan rounded-full flex items-center justify-center animate-glow-pulse shadow-lg shadow-aurora-purple/30">
        <i class="pi pi-check text-5xl text-white"></i>
      </div>
    </div>

    <!-- Success message -->
    <div class="space-y-4">
      <h1 class="text-4xl md:text-5xl font-bold text-gradient">
        Открытка отправлена!
      </h1>
      <p class="text-xl text-winter-snow/70">
        Ваше новогоднее поздравление успешно доставлено в Telegram
      </p>
    </div>

    <!-- Decorative elements -->
    <div class="flex justify-center gap-4 text-3xl">
      <span class="animate-float">🎄</span>
      <span class="animate-sparkle" style="animation-delay: 0.3s">✨</span>
      <span class="animate-float" style="animation-delay: 0.6s">🎁</span>
      <span class="animate-sparkle" style="animation-delay: 0.9s">❄️</span>
    </div>

    <!-- Action button -->
    <div class="pt-8">
      <button
        @click="createAnother"
        class="btn-magic px-8 py-4 text-lg font-semibold rounded-xl group"
      >
        <span class="flex items-center gap-2">
          <i class="pi pi-plus group-hover:rotate-90 transition-transform"></i>
          <span>Создать ещё одну открытку</span>
        </span>
      </button>
    </div>

    <!-- Auto redirect message -->
    <p class="text-sm text-winter-snow/50">
      Автоматический переход на главную через 5 секунд...
    </p>
  </div>
</template>
