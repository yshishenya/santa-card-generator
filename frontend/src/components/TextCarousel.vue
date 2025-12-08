<script setup lang="ts">
import { ref } from 'vue'
import { Carousel, Slide, Navigation } from 'vue3-carousel'
import { useCardStore } from '@/stores/card'
import { TextStyle } from '@/types'
import 'vue3-carousel/dist/carousel.css'
import GlassCard from './GlassCard.vue'

const cardStore = useCardStore()
const selectedStyle = ref<TextStyle | undefined>(undefined)

const textStyleOptions = [
  { value: TextStyle.ODE, label: 'Ода' },
  { value: TextStyle.FUTURE, label: 'Будущее' },
  { value: TextStyle.HAIKU, label: 'Хайку' },
  { value: TextStyle.NEWSPAPER, label: 'Газета' },
  { value: TextStyle.STANDUP, label: 'Стендап' }
]

const handleRegenerate = async () => {
  if (!cardStore.canRegenerate) return

  try {
    await cardStore.regenerateText(selectedStyle.value)
    selectedStyle.value = undefined
  } catch (error) {
    console.error('Failed to regenerate text:', error)
    alert('Не удалось регенерировать текст. Попробуйте ещё раз.')
  }
}

const handleSelect = (id: string) => {
  cardStore.selectedTextId = id
}
</script>

<template>
  <div class="space-y-4">
    <!-- Carousel -->
    <Carousel :items-to-show="1" :wrap-around="false" class="text-carousel">
      <Slide v-for="variant in cardStore.textVariants" :key="variant.id">
        <GlassCard padding="p-8">
          <div class="space-y-4">
            <!-- Text content -->
            <div class="prose prose-invert max-w-none">
              <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap">
                {{ variant.content }}
              </p>
            </div>

            <!-- Selection checkbox -->
            <div class="flex justify-center pt-4">
              <label class="label cursor-pointer gap-3 bg-white/5 px-6 py-3 rounded-lg hover:bg-white/10 transition-colors">
                <span class="label-text text-winter-snow font-semibold">Выбрать этот текст</span>
                <input
                  type="radio"
                  :checked="cardStore.selectedTextId === variant.id"
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
          v-for="option in textStyleOptions"
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
          {{ cardStore.isRegenerating ? 'Регенерация...' : 'Регенерировать текст' }}
          <span class="ml-2 badge badge-sm">{{ cardStore.remainingRegenerations }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style>
.text-carousel .carousel__prev,
.text-carousel .carousel__next {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 48px;
  height: 48px;
}

.text-carousel .carousel__prev:hover,
.text-carousel .carousel__next:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
