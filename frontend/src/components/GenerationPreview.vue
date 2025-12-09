<script setup lang="ts">
import { ref } from 'vue'
import { useCardStore } from '@/stores/card'
import TextCarousel from './TextCarousel.vue'
import ImageCarousel from './ImageCarousel.vue'
import PreviewModal from './PreviewModal.vue'

const cardStore = useCardStore()

// Preview modal state
const showPreview = ref(false)

const handleStartOver = () => {
  cardStore.reset()
}

const openPreview = () => {
  showPreview.value = true
}

const closePreview = () => {
  showPreview.value = false
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
        Получатель: <span class="font-bold text-christmas-gold">{{ cardStore.recipient }}</span>
      </p>
    </div>

    <!-- Section 1: Original text (if available) -->
    <div v-if="cardStore.hasOriginalText" class="bg-white/5 rounded-xl p-6 border border-white/10">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-winter-snow flex items-center gap-2">
          <i class="pi pi-pencil text-christmas-gold"></i>
          Ваш текст
        </h3>
        <label class="label cursor-pointer gap-3">
          <span class="label-text text-winter-snow">Использовать</span>
          <input
            type="checkbox"
            :checked="cardStore.useOriginalText"
            @change="cardStore.setUseOriginalText(($event.target as HTMLInputElement).checked)"
            class="checkbox checkbox-primary"
          />
        </label>
      </div>
      <div
        class="bg-white/5 p-4 rounded-lg text-winter-snow/90 whitespace-pre-wrap"
        :class="{ 'ring-2 ring-christmas-green': cardStore.useOriginalText }"
      >
        {{ cardStore.originalText }}
      </div>

      <!-- Include original alongside AI option -->
      <label v-if="!cardStore.useOriginalText" class="label cursor-pointer justify-start gap-3 mt-4">
        <input
          type="checkbox"
          :checked="cardStore.includeOriginalText"
          @change="cardStore.setIncludeOriginalText(($event.target as HTMLInputElement).checked)"
          class="checkbox checkbox-sm checkbox-primary"
        />
        <span class="label-text text-winter-snow/80 text-sm">Добавить ваш текст к AI-варианту</span>
      </label>
    </div>

    <!-- Section 2: AI text variants carousel -->
    <div class="bg-white/5 rounded-xl p-6 border border-white/10">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-winter-snow flex items-center gap-2">
          <i class="pi pi-sparkles text-christmas-gold"></i>
          AI варианты текста
          <span class="text-sm font-normal text-winter-snow/60">(5 стилей)</span>
        </h3>
        <div class="flex items-center gap-2">
          <span class="text-sm text-winter-snow/60">
            Регенераций: <span class="font-bold text-christmas-gold">{{ cardStore.remainingTextRegenerations }}</span>
          </span>
          <button
            @click="cardStore.regenerateText()"
            :disabled="!cardStore.canRegenerateText || cardStore.isRegeneratingText"
            class="btn btn-sm bg-christmas-gold/20 hover:bg-christmas-gold/30 border-christmas-gold/30 text-christmas-gold"
          >
            <span v-if="cardStore.isRegeneratingText" class="loading loading-spinner loading-xs"></span>
            <i v-else class="pi pi-refresh"></i>
            Перегенерировать
          </button>
        </div>
      </div>
      <TextCarousel />
    </div>

    <!-- Section 3: Image variants carousel -->
    <div class="bg-white/5 rounded-xl p-6 border border-white/10">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-winter-snow flex items-center gap-2">
          <i class="pi pi-image text-christmas-gold"></i>
          Варианты изображения
          <span class="text-sm font-normal text-winter-snow/60">(4 стиля)</span>
        </h3>
        <div class="flex items-center gap-2">
          <span class="text-sm text-winter-snow/60">
            Регенераций: <span class="font-bold text-christmas-gold">{{ cardStore.remainingImageRegenerations }}</span>
          </span>
          <button
            @click="cardStore.regenerateImages()"
            :disabled="!cardStore.canRegenerateImages || cardStore.isRegeneratingImages"
            class="btn btn-sm bg-christmas-gold/20 hover:bg-christmas-gold/30 border-christmas-gold/30 text-christmas-gold"
          >
            <span v-if="cardStore.isRegeneratingImages" class="loading loading-spinner loading-xs"></span>
            <i v-else class="pi pi-refresh"></i>
            Перегенерировать
          </button>
        </div>
      </div>
      <ImageCarousel />
    </div>

    <!-- Error message -->
    <div v-if="cardStore.error" class="alert alert-error">
      <i class="pi pi-exclamation-triangle"></i>
      <span>{{ cardStore.error }}</span>
      <button type="button" class="btn btn-sm btn-ghost" @click="cardStore.clearError()">
        <i class="pi pi-times"></i>
      </button>
    </div>

    <!-- Action buttons -->
    <div class="flex gap-4 pt-4">
      <button
        @click="handleStartOver"
        class="btn btn-lg flex-1 bg-white/10 hover:bg-white/20 border-white/20 text-winter-snow"
      >
        <i class="pi pi-arrow-left mr-2"></i>
        Начать заново
      </button>
      <button
        @click="openPreview"
        :disabled="!cardStore.canSend"
        class="btn btn-lg flex-1 bg-christmas-green hover:bg-christmas-green-dark border-0 text-white"
      >
        <i class="pi pi-eye mr-2"></i>
        Предпросмотр
      </button>
    </div>

    <!-- Preview Modal -->
    <PreviewModal
      :show="showPreview"
      @close="closePreview"
    />
  </div>
</template>
