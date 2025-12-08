<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCardStore } from '@/stores/card'

const router = useRouter()
const cardStore = useCardStore()

onMounted(() => {
  // Auto redirect to home after 5 seconds
  setTimeout(() => {
    cardStore.reset()
    router.push('/')
  }, 5000)
})

const createAnother = () => {
  cardStore.reset()
  router.push('/')
}
</script>

<template>
  <div class="text-center space-y-8 py-12">
    <!-- Success icon -->
    <div class="flex justify-center">
      <div class="w-24 h-24 bg-christmas-green rounded-full flex items-center justify-center animate-twinkle">
        <i class="pi pi-check text-5xl text-white"></i>
      </div>
    </div>

    <!-- Success message -->
    <div class="space-y-4">
      <h1 class="text-4xl font-bold text-winter-snow">
        Открытка отправлена!
      </h1>
      <p class="text-xl text-winter-snow/80">
        Ваше новогоднее поздравление успешно доставлено в Telegram
      </p>
    </div>

    <!-- Decorative elements -->
    <div class="flex justify-center gap-4 text-3xl">
      <span class="animate-twinkle">🎄</span>
      <span class="animate-twinkle" style="animation-delay: 0.3s">✨</span>
      <span class="animate-twinkle" style="animation-delay: 0.6s">🎁</span>
      <span class="animate-twinkle" style="animation-delay: 0.9s">❄️</span>
    </div>

    <!-- Action button -->
    <div class="pt-8">
      <button
        @click="createAnother"
        class="btn btn-lg bg-christmas-red hover:bg-christmas-red-dark border-0 text-white px-8"
      >
        <i class="pi pi-plus mr-2"></i>
        Создать ещё одну открытку
      </button>
    </div>

    <!-- Auto redirect message -->
    <p class="text-sm text-winter-snow/60">
      Автоматический переход на главную через 5 секунд...
    </p>
  </div>
</template>
