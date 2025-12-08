<script setup lang="ts">
import { ref } from 'vue'
import { Carousel, Slide, Navigation } from 'vue3-carousel'
import { useCardStore } from '@/stores/card'
import { ImageStyle } from '@/types'
import 'vue3-carousel/dist/carousel.css'
import GlassCard from './GlassCard.vue'

const cardStore = useCardStore()
const selectedStyle = ref<ImageStyle | undefined>(undefined)

const imageStyleOptions = [
  { value: ImageStyle.DIGITAL_ART, label: 'Живопись' },
  { value: ImageStyle.PIXEL_ART, label: 'Пиксель' },
  { value: ImageStyle.SPACE, label: 'Космос' },
  { value: ImageStyle.MOVIE, label: 'Фильм' }
]

const handleRegenerate = async () => {
  if (!cardStore.canRegenerate) return

  try {
    await cardStore.regenerateImage(selectedStyle.value)
    selectedStyle.value = undefined
  } catch (error) {
    console.error('Failed to regenerate image:', error)
    alert('Не удалось регенерировать изображение. Попробуйте ещё раз.')
  }
}

const handleSelect = (id: string) => {
  cardStore.selectedImageId = id
}
</script>

<template>
  <div class="space-y-4">
    <!-- Carousel -->
    <Carousel :items-to-show="1" :wrap-around="false" class="image-carousel">
      <Slide v-for="variant in cardStore.imageVariants" :key="variant.id">
        <GlassCard padding="p-4">
          <div class="space-y-4">
            <!-- Image display -->
            <div class="relative aspect-video bg-slate-800 rounded-lg overflow-hidden">
              <img
                :src="variant.url"
                :alt="`Вариант изображения ${variant.id}`"
                class="w-full h-full object-cover"
                loading="lazy"
              />
            </div>

            <!-- Selection checkbox -->
            <div class="flex justify-center">
              <label class="label cursor-pointer gap-3 bg-white/5 px-6 py-3 rounded-lg hover:bg-white/10 transition-colors">
                <span class="label-text text-winter-snow font-semibold">Выбрать это изображение</span>
                <input
                  type="radio"
                  :checked="cardStore.selectedImageId === variant.id"
                  @change="handleSelect(variant.id)"
                  class="radio radio-primary"
                />
              </label>
            </div>
          </div>
        </GlassCard>
      </Slide>

      <template #addons>
        <Navigation />
      </template>
    </Carousel>

    <!-- Regeneration controls -->
    <div v-if="cardStore.canRegenerate" class="space-y-3">
      <!-- Style selector -->
      <div class="flex flex-wrap gap-2 justify-center">
        <button
          v-for="option in imageStyleOptions"
          :key="option.value"
          @click="selectedStyle = option.value"
          class="btn btn-sm"
          :class="selectedStyle === option.value ? 'btn-primary' : 'btn-outline btn-ghost text-winter-snow'"
        >
          {{ option.label }}
        </button>
      </div>

      <!-- Regenerate button -->
      <div class="flex justify-center">
        <button
          @click="handleRegenerate"
          :disabled="cardStore.isRegenerating"
          class="btn bg-christmas-gold hover:bg-christmas-gold-light border-0 text-slate-900"
        >
          <span v-if="cardStore.isRegenerating" class="loading loading-spinner"></span>
          <i v-else class="pi pi-refresh mr-2"></i>
          {{ cardStore.isRegenerating ? 'Регенерация...' : 'Регенерировать изображение' }}
          <span class="ml-2 badge badge-sm">{{ cardStore.remainingRegenerations }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style>
.image-carousel .carousel__prev,
.image-carousel .carousel__next {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 48px;
  height: 48px;
}

.image-carousel .carousel__prev:hover,
.image-carousel .carousel__next:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
