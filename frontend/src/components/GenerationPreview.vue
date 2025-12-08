<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useCardStore } from '@/stores/card'
import TextCarousel from './TextCarousel.vue'
import ImageCarousel from './ImageCarousel.vue'

const router = useRouter()
const cardStore = useCardStore()

const handleSend = async () => {
  try {
    await cardStore.send()
    router.push('/success')
  } catch (error) {
    console.error('Failed to send card:', error)
    alert('Не удалось отправить открытку. Попробуйте ещё раз.')
  }
}

const handleStartOver = () => {
  cardStore.reset()
}
</script>

<template>
  <div class="space-y-8">
    <!-- Page title -->
    <div class="text-center">
      <h2 class="text-3xl font-bold text-winter-snow mb-2">
        Выберите текст и изображение
      </h2>
      <p class="text-winter-snow/80">
        Осталось регенераций: <span class="font-bold text-christmas-gold">{{ cardStore.remainingRegenerations }}</span>
      </p>
    </div>

    <!-- Text carousel -->
    <div>
      <h3 class="text-xl font-semibold text-winter-snow mb-4 flex items-center gap-2">
        <i class="pi pi-align-left text-christmas-gold"></i>
        Варианты текста
      </h3>
      <TextCarousel />
    </div>

    <!-- Image carousel -->
    <div>
      <h3 class="text-xl font-semibold text-winter-snow mb-4 flex items-center gap-2">
        <i class="pi pi-image text-christmas-gold"></i>
        Варианты изображения
      </h3>
      <ImageCarousel />
    </div>

    <!-- Action buttons -->
    <div class="flex gap-4 pt-4">
      <button
        @click="handleStartOver"
        class="btn btn-lg flex-1 bg-white/10 hover:bg-white/20 border-white/20 text-winter-snow"
      >
        <i class="pi pi-refresh mr-2"></i>
        Начать заново
      </button>
      <button
        @click="handleSend"
        :disabled="!cardStore.canSend || cardStore.isSending"
        class="btn btn-lg flex-1 bg-christmas-green hover:bg-christmas-green-dark border-0 text-white"
      >
        <span v-if="cardStore.isSending" class="loading loading-spinner"></span>
        <i v-else class="pi pi-send mr-2"></i>
        {{ cardStore.isSending ? 'Отправляем...' : 'Отправить в Telegram' }}
      </button>
    </div>
  </div>
</template>
