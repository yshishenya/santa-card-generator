<script setup lang="ts">
import { useCardStore } from '@/stores/card'
import { IMAGE_STYLE_LABELS } from '@/types'
import GlassCard from './GlassCard.vue'

const cardStore = useCardStore()

const selectVariant = (index: number) => {
  cardStore.selectImageVariant(index)
}
</script>

<template>
  <div class="relative">
    <!-- 2x2 Grid for instant comparison of all 4 images -->
    <div v-if="cardStore.imageVariants.length > 0" class="image-grid-wrapper">
      <div class="image-grid">
        <GlassCard
          v-for="(variant, index) in cardStore.imageVariants"
          :key="variant.id"
          padding="p-3"
          class="image-card"
          :class="{
            'selected': cardStore.selectedImageIndex === index,
            'unselected': cardStore.selectedImageIndex !== index
          }"
          @click="selectVariant(index)"
        >
          <!-- Selection badge -->
          <div v-if="cardStore.selectedImageIndex === index" class="selection-badge">
            <i class="pi pi-check"></i>
          </div>

          <!-- Style badge -->
          <div class="mb-2">
            <span class="badge badge-sm bg-christmas-green/20 text-christmas-green border-christmas-green/30">
              <i class="pi pi-image mr-1 text-xs"></i>
              {{ IMAGE_STYLE_LABELS[variant.style] }}
            </span>
          </div>

          <!-- Image -->
          <div class="image-container">
            <img
              :src="variant.url"
              :alt="`${IMAGE_STYLE_LABELS[variant.style]} - вариант ${index + 1}`"
              class="grid-image"
              loading="lazy"
            />
          </div>

          <!-- Click hint -->
          <div class="text-center mt-2 text-winter-snow/50 text-xs">
            {{ cardStore.selectedImageIndex === index ? '✓ Выбрано' : 'Нажмите для выбора' }}
          </div>
        </GlassCard>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-8 text-winter-snow/60">
      <i class="pi pi-info-circle text-2xl mb-2"></i>
      <p>Нет вариантов изображения</p>
    </div>

    <!-- Loading overlay -->
    <div
      v-if="cardStore.isRegeneratingImages"
      class="loading-overlay"
    >
      <div class="text-center">
        <span class="loading loading-spinner loading-lg text-christmas-gold"></span>
        <p class="text-winter-snow mt-2">Генерируем новые изображения...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Grid wrapper */
.image-grid-wrapper {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 8px;
}

/* 2x2 Grid layout */
.image-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

/* Individual card */
.image-card {
  position: relative;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Selected state */
.image-card.selected {
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 0 3px rgba(22, 163, 74, 0.5),
    0 0 20px rgba(22, 163, 74, 0.3);
  transform: scale(1.02);
  z-index: 10;
}

/* Unselected state */
.image-card.unselected {
  opacity: 0.65;
  filter: grayscale(0.15);
}

.image-card.unselected:hover {
  opacity: 0.85;
  filter: grayscale(0);
  transform: scale(1.01);
}

/* Selection badge */
.selection-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  z-index: 20;
  width: 32px;
  height: 32px;
  background: #16A34A;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.4),
    0 0 0 3px #0F172A;
}

.selection-badge i {
  color: white;
  font-size: 14px;
  font-weight: bold;
}

/* Image container */
.image-container {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #1E293B;
  border-radius: 10px;
  overflow: hidden;
}

/* Image styling */
.grid-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 10px;
  display: block;
}

/* Loading overlay */
.loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  z-index: 30;
}

/* Responsive: single column on mobile */
@media (max-width: 600px) {
  .image-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .image-card.selected {
    transform: scale(1.01);
  }

  .image-container {
    max-width: 350px;
    margin: 0 auto;
  }
}
</style>
