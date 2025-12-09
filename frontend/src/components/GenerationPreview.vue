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
    <!-- Page title with aurora styling -->
    <div class="text-center">
      <h2 class="text-3xl md:text-4xl font-bold text-gradient mb-3">
        Выберите текст и изображение
      </h2>
      <p class="text-winter-snow/70 text-lg">
        Получатель: <span class="font-semibold text-aurora-cyan">{{ cardStore.recipient }}</span>
      </p>
    </div>

    <!-- Section 1: Original text (if available) -->
    <div v-if="cardStore.hasOriginalText" class="glass-card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-xl font-semibold text-winter-snow flex items-center gap-2">
          <i class="pi pi-pencil text-aurora-pink"></i>
          Ваш текст
        </h3>
        <label class="label cursor-pointer gap-3">
          <span class="label-text text-winter-snow/80">Использовать</span>
          <input
            type="checkbox"
            :checked="cardStore.useOriginalText"
            @change="cardStore.setUseOriginalText(($event.target as HTMLInputElement).checked)"
            class="checkbox checkbox-primary border-aurora-purple/50 checked:border-aurora-purple checked:bg-aurora-purple"
          />
        </label>
      </div>
      <div
        class="bg-white/5 p-4 rounded-xl text-winter-snow/90 whitespace-pre-wrap transition-all duration-300"
        :class="{ 'ring-2 ring-aurora-cyan shadow-lg shadow-aurora-cyan/20': cardStore.useOriginalText }"
      >
        {{ cardStore.originalText }}
      </div>

      <!-- Include original alongside AI option -->
      <label v-if="!cardStore.useOriginalText" class="label cursor-pointer justify-start gap-3 mt-4">
        <input
          type="checkbox"
          :checked="cardStore.includeOriginalText"
          @change="cardStore.setIncludeOriginalText(($event.target as HTMLInputElement).checked)"
          class="checkbox checkbox-sm border-aurora-purple/50 checked:border-aurora-purple checked:bg-aurora-purple"
        />
        <span class="label-text text-winter-snow/70 text-sm">Добавить ваш текст к AI-варианту</span>
      </label>
    </div>

    <!-- Section 2: AI text variants carousel -->
    <div class="glass-card p-6">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
        <h3 class="text-xl font-semibold text-winter-snow flex items-center gap-2">
          <i class="pi pi-sparkles text-aurora-purple"></i>
          AI варианты текста
          <span class="text-sm font-normal text-winter-snow/50">(5 стилей)</span>
        </h3>
        <div class="flex items-center gap-3">
          <span class="text-sm text-winter-snow/60">
            Регенераций: <span class="font-bold text-aurora-cyan">{{ cardStore.remainingTextRegenerations }}</span>
          </span>
          <button
            @click="cardStore.regenerateText()"
            :disabled="!cardStore.canRegenerateText || cardStore.isRegeneratingText"
            class="btn btn-sm bg-aurora-purple/20 hover:bg-aurora-purple/30 border-aurora-purple/30 text-aurora-purple hover:text-white transition-all disabled:opacity-40"
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
        <h3 class="text-xl font-semibold text-winter-snow flex items-center gap-2">
          <i class="pi pi-image text-aurora-pink"></i>
          Варианты изображения
          <span class="text-sm font-normal text-winter-snow/50">(4 стиля)</span>
        </h3>
        <div class="flex items-center gap-3">
          <span class="text-sm text-winter-snow/60">
            Регенераций: <span class="font-bold text-aurora-cyan">{{ cardStore.remainingImageRegenerations }}</span>
          </span>
          <button
            @click="cardStore.regenerateImages()"
            :disabled="!cardStore.canRegenerateImages || cardStore.isRegeneratingImages"
            class="btn btn-sm bg-aurora-pink/20 hover:bg-aurora-pink/30 border-aurora-pink/30 text-aurora-pink hover:text-white transition-all disabled:opacity-40"
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
    <div v-if="cardStore.error" class="glass-card bg-red-500/20 border-red-500/30 p-4 flex items-center gap-3">
      <i class="pi pi-exclamation-triangle text-red-400 text-xl"></i>
      <span class="flex-1 text-red-200">{{ cardStore.error }}</span>
      <button type="button" class="text-red-300 hover:text-red-100 transition-colors" @click="cardStore.clearError()">
        <i class="pi pi-times"></i>
      </button>
    </div>

    <!-- Action buttons -->
    <div class="flex gap-4 pt-4">
      <button
        @click="handleStartOver"
        class="flex-1 px-6 py-4 rounded-xl bg-white/10 hover:bg-white/15 border border-white/20 text-winter-snow font-semibold transition-all duration-300 hover:border-white/30 flex items-center justify-center gap-2"
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
