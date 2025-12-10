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
    <!-- Page title with festive styling -->
    <div class="text-center">
      <h2 class="text-3xl md:text-4xl font-bold text-gradient mb-3">
        Выберите текст и изображение
      </h2>
      <p class="text-winter-text-secondary text-lg">
        Получатель: <span class="font-semibold text-christmas-gold">{{ cardStore.recipient }}</span>
      </p>
    </div>

    <!-- Section 1: Original text (if available) -->
    <div v-if="cardStore.hasOriginalText" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-christmas-gold flex items-center gap-2">
          <i class="pi pi-pencil text-christmas-gold"></i>
          Ваш текст
        </h3>
      </div>
      <div class="bg-winter-bg-secondary/50 p-4 rounded-xl text-winter-text-primary whitespace-pre-wrap border border-winter-frost/30">
        {{ cardStore.originalText }}
      </div>

      <!-- Include original alongside AI option - prominent checkbox -->
      <label class="label cursor-pointer justify-start gap-3 mt-4 p-3 rounded-lg bg-christmas-gold/10 border border-christmas-gold/30 hover:bg-christmas-gold/15 transition-colors">
        <input
          type="checkbox"
          :checked="cardStore.includeOriginalText"
          @change="cardStore.setIncludeOriginalText(($event.target as HTMLInputElement).checked)"
          class="checkbox checkbox-md border-christmas-gold/60 checked:border-christmas-gold checked:bg-christmas-gold [--chkbg:theme(colors.christmas.gold)] [--chkfg:theme(colors.winter.bg-primary)]"
        />
        <span class="label-text text-winter-text-primary font-medium">Добавить ваш текст к AI-варианту</span>
      </label>
    </div>

    <!-- Section 2: AI text variants carousel -->
    <div class="glass-card p-6">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <h3 class="text-xl font-semibold text-christmas-gold flex items-center gap-2">
          <i class="pi pi-sparkles text-christmas-gold"></i>
          AI варианты текста
          <span class="text-sm font-normal text-winter-text-muted">(5 стилей)</span>
        </h3>
        <div class="flex items-center gap-3">
          <span class="text-sm text-winter-text-secondary">
            Регенераций: <span class="font-bold text-christmas-green-light">{{ cardStore.remainingTextRegenerations }}</span>
          </span>
          <button
            @click="cardStore.regenerateText()"
            :disabled="!cardStore.canRegenerateText || cardStore.isRegeneratingText"
            class="btn btn-sm bg-christmas-gold/15 hover:bg-christmas-gold/25 border-christmas-gold/40 text-christmas-gold hover:text-christmas-gold-light transition-all disabled:opacity-40"
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
    <div class="glass-card p-6">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <h3 class="text-xl font-semibold text-christmas-gold flex items-center gap-2">
          <i class="pi pi-image text-christmas-red-light"></i>
          Варианты изображения
          <span class="text-sm font-normal text-winter-text-muted">(5 стилей)</span>
        </h3>
        <div class="flex items-center gap-3">
          <span class="text-sm text-winter-text-secondary">
            Регенераций: <span class="font-bold text-christmas-green-light">{{ cardStore.remainingImageRegenerations }}</span>
          </span>
          <button
            @click="cardStore.regenerateImages()"
            :disabled="!cardStore.canRegenerateImages || cardStore.isRegeneratingImages"
            class="btn btn-sm bg-christmas-red/15 hover:bg-christmas-red/25 border-christmas-red/40 text-christmas-red-light hover:text-christmas-red-light transition-all disabled:opacity-40"
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
    <div v-if="cardStore.error" class="glass-card bg-christmas-red/10 border-christmas-red/30 p-4 flex items-center gap-3">
      <i class="pi pi-exclamation-triangle text-christmas-red-light text-xl"></i>
      <span class="flex-1 text-christmas-red-light">{{ cardStore.error }}</span>
      <button type="button" class="text-christmas-red/60 hover:text-christmas-red-light transition-colors" @click="cardStore.clearError()">
        <i class="pi pi-times"></i>
      </button>
    </div>

    <!-- Action buttons -->
    <div class="flex gap-4 pt-4">
      <button
        @click="handleStartOver"
        class="flex-1 px-6 py-4 rounded-xl bg-winter-bg-secondary hover:bg-winter-frost/30 border border-winter-frost/30 text-winter-text-primary font-semibold transition-all duration-300 hover:border-christmas-gold/30 flex items-center justify-center gap-2"
      >
        <i class="pi pi-arrow-left"></i>
        Начать заново
      </button>
      <button
        @click="openPreview"
        :disabled="!cardStore.canSend"
        class="btn-magic flex-1 px-6 py-4 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        <i class="pi pi-eye"></i>
        <span>Предпросмотр</span>
      </button>
    </div>

    <!-- Preview Modal -->
    <PreviewModal
      :show="showPreview"
      @close="closePreview"
    />
  </div>
</template>
