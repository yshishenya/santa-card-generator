<script setup lang="ts">
import { useCardStore } from '@/stores/card'
import { ALL_IMAGE_STYLES, IMAGE_STYLE_LABELS, ImageStyle } from '@/types'
import GlassCard from './GlassCard.vue'

const cardStore = useCardStore()

// Style icons for visual representation (all 15 styles)
const styleIcons: Record<ImageStyle, string> = {
  [ImageStyle.KNITTED]: '🧶',
  [ImageStyle.MAGIC_REALISM]: '✨',
  [ImageStyle.PIXEL_ART]: '👾',
  [ImageStyle.VINTAGE_RUSSIAN]: '📜',
  [ImageStyle.SOVIET_POSTER]: '⭐',
  [ImageStyle.HYPERREALISM]: '📸',
  [ImageStyle.DIGITAL_3D]: '🎲',
  [ImageStyle.FANTASY]: '🐉',
  [ImageStyle.COMIC_BOOK]: '💥',
  [ImageStyle.WATERCOLOR]: '🎨',
  [ImageStyle.CYBERPUNK]: '🌃',
  [ImageStyle.PAPER_CUTOUT]: '✂️',
  [ImageStyle.POP_ART]: '🎭',
  [ImageStyle.LEGO]: '🧱',
  [ImageStyle.LINOCUT]: '🪵',
}

// Style descriptions (all 15 styles)
const styleDescriptions: Record<ImageStyle, string> = {
  [ImageStyle.KNITTED]: 'Уютная вязаная текстура',
  [ImageStyle.MAGIC_REALISM]: 'Волшебные элементы в реальном мире',
  [ImageStyle.PIXEL_ART]: 'Ретро 16-бит игровая графика',
  [ImageStyle.VINTAGE_RUSSIAN]: 'Дореволюционная открытка',
  [ImageStyle.SOVIET_POSTER]: 'Конструктивизм и геометрия',
  [ImageStyle.HYPERREALISM]: 'Фотореалистичная макросъёмка',
  [ImageStyle.DIGITAL_3D]: 'Современная 3D-графика',
  [ImageStyle.FANTASY]: 'Эпическое фэнтези',
  [ImageStyle.COMIC_BOOK]: 'Динамичный комикс',
  [ImageStyle.WATERCOLOR]: 'Нежная акварельная живопись',
  [ImageStyle.CYBERPUNK]: 'Неоновый футуризм',
  [ImageStyle.PAPER_CUTOUT]: 'Бумажная аппликация',
  [ImageStyle.POP_ART]: 'Яркий поп-арт 60-х',
  [ImageStyle.LEGO]: 'Конструктор из кубиков',
  [ImageStyle.LINOCUT]: 'Народная гравюра',
}

const handleToggle = (style: ImageStyle) => {
  cardStore.toggleImageStyle(style)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Selection info -->
    <div class="flex items-center justify-between">
      <p class="text-winter-text-secondary">
        Выбрано: <span class="font-bold text-christmas-gold">{{ cardStore.selectedImageStyles.length }}</span> / 4 стилей
      </p>
      <p v-if="cardStore.selectedImageStyles.length === 0" class="text-christmas-red-light text-sm">
        Выберите хотя бы один стиль
      </p>
      <p v-else-if="cardStore.selectedImageStyles.length === 4" class="text-christmas-green-light text-sm">
        Максимум выбрано
      </p>
    </div>

    <!-- Style grid -->
    <div class="style-grid">
      <GlassCard
        v-for="style in ALL_IMAGE_STYLES"
        :key="style"
        padding="p-4"
        class="style-card cursor-pointer transition-all duration-300"
        :class="{
          'selected': cardStore.isImageStyleSelected(style),
          'disabled': !cardStore.isImageStyleSelected(style) && cardStore.selectedImageStyles.length >= 4
        }"
        @click="handleToggle(style)"
      >
        <!-- Checkbox indicator -->
        <div class="absolute top-3 right-3">
          <div
            class="w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all"
            :class="cardStore.isImageStyleSelected(style)
              ? 'bg-christmas-gold border-christmas-gold'
              : 'border-winter-frost/50 bg-transparent'"
          >
            <i
              v-if="cardStore.isImageStyleSelected(style)"
              class="pi pi-check text-white text-sm"
            ></i>
          </div>
        </div>

        <!-- Icon -->
        <div class="text-4xl mb-3">{{ styleIcons[style] }}</div>

        <!-- Label -->
        <h4 class="font-semibold text-winter-text-primary mb-1">
          {{ IMAGE_STYLE_LABELS[style] }}
        </h4>

        <!-- Description -->
        <p class="text-sm text-winter-text-muted">
          {{ styleDescriptions[style] }}
        </p>
      </GlassCard>
    </div>

    <!-- Generate button -->
    <div class="pt-4">
      <button
        @click="cardStore.generateImages()"
        :disabled="!cardStore.canGenerateImages || cardStore.isGeneratingImages"
        class="btn-magic w-full px-6 py-4 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
      >
        <span v-if="cardStore.isGeneratingImages" class="loading loading-spinner loading-md"></span>
        <i v-else class="pi pi-image text-xl"></i>
        <span v-if="cardStore.isGeneratingImages">
          Генерируем {{ cardStore.selectedImageStyles.length }} изображений...
        </span>
        <span v-else>
          Сгенерировать {{ cardStore.selectedImageStyles.length > 0 ? cardStore.selectedImageStyles.length : '' }} картинок
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.style-card {
  position: relative;
  text-align: center;
}

.style-card.selected {
  box-shadow:
    0 0 0 2px rgba(212, 175, 55, 0.6),
    0 0 20px rgba(212, 175, 55, 0.2);
  transform: scale(1.02);
}

.style-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.style-card:not(.disabled):not(.selected):hover {
  transform: scale(1.01);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

@media (max-width: 600px) {
  .style-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .style-card {
    padding: 12px;
  }

  .style-card .text-4xl {
    font-size: 2rem;
  }
}
</style>
