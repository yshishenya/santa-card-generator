<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Carousel, Slide, Navigation } from 'vue3-carousel'
import { useCardStore } from '@/stores/card'
import { TextStyle } from '@/types'
import 'vue3-carousel/dist/carousel.css'
import GlassCard from './GlassCard.vue'

const cardStore = useCardStore()
const selectedStyle = ref<TextStyle | undefined>(undefined)
const useOriginalText = ref<boolean>(true)

// Separate original text from AI variants
const originalText = computed(() =>
  cardStore.textVariants.find(v => v.style === 'original')
)

const aiVariants = computed(() =>
  cardStore.textVariants.filter(v => v.style !== 'original')
)

// Check if user chose original or AI
const isOriginalSelected = computed(() =>
  originalText.value && cardStore.selectedTextId === originalText.value.id
)

// When user unchecks "use original", auto-select first AI variant if original was selected
watch(useOriginalText, (newValue) => {
  if (!newValue && isOriginalSelected.value && aiVariants.value.length > 0) {
    cardStore.selectedTextId = aiVariants.value[0].id
  }
})

// Sync includeOriginalText with store based on checkbox and selection
// Include original if: checkbox is checked AND an AI variant is selected
watch(
  [useOriginalText, () => cardStore.selectedTextId, originalText],
  ([useOriginal, selectedId, original]) => {
    const aiVariantSelected = Boolean(original && selectedId !== original.id)
    cardStore.setIncludeOriginalText(Boolean(useOriginal) && aiVariantSelected)
  },
  { immediate: true }
)

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

const selectOriginal = () => {
  if (originalText.value) {
    cardStore.selectedTextId = originalText.value.id
  }
}

const selectAiVariant = (id: string) => {
  cardStore.selectedTextId = id
}
</script>

<template>
  <div class="space-y-6">
    <!-- Original text section (if available) -->
    <div v-if="originalText" class="space-y-3">
      <GlassCard padding="p-6" :class="{ 'opacity-50': !useOriginalText }">
        <div class="space-y-4">
          <!-- Header -->
          <div class="flex items-center">
            <span class="badge badge-lg bg-christmas-gold/20 text-christmas-gold border-christmas-gold/30">
              <i class="pi pi-user mr-1"></i>
              Ваш текст
            </span>
          </div>

          <!-- Original text content -->
          <div class="prose prose-invert max-w-none">
            <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap">
              {{ originalText.content }}
            </p>
          </div>

          <!-- Checkbox to use/exclude original text (left aligned) -->
          <div class="pt-2 border-t border-white/10">
            <label class="label cursor-pointer justify-start gap-3">
              <input
                v-model="useOriginalText"
                type="checkbox"
                class="checkbox checkbox-primary"
                @change="useOriginalText && selectOriginal()"
              />
              <span class="label-text text-winter-snow">Использовать мой текст</span>
            </label>
          </div>
        </div>
      </GlassCard>
    </div>

    <!-- AI variants section -->
    <div v-if="aiVariants.length > 0" class="space-y-3">
      <div class="flex items-center justify-between px-2">
        <span class="badge badge-lg bg-christmas-green/20 text-christmas-green border-christmas-green/30">
          <i class="pi pi-sparkles mr-1"></i>
          AI стилизация
        </span>
        <span class="text-winter-snow/60 text-sm">{{ aiVariants.length }} вариантов</span>
      </div>

      <!-- AI Carousel -->
      <Carousel :items-to-show="1" :wrap-around="false" class="text-carousel">
        <Slide v-for="variant in aiVariants" :key="variant.id">
          <GlassCard padding="p-6">
            <div class="space-y-4">
              <!-- Text content -->
              <div class="prose prose-invert max-w-none">
                <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap">
                  {{ variant.content }}
                </p>
              </div>

              <!-- Selection -->
              <div class="flex justify-center pt-2">
                <label class="label cursor-pointer gap-3 bg-white/5 px-6 py-3 rounded-lg hover:bg-white/10 transition-colors">
                  <span class="label-text text-winter-snow font-semibold">Выбрать этот вариант</span>
                  <input
                    type="radio"
                    name="text-choice"
                    :checked="cardStore.selectedTextId === variant.id"
                    @change="selectAiVariant(variant.id)"
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
      <div v-if="cardStore.canRegenerate" class="space-y-3 pt-2">
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
            {{ cardStore.isRegenerating ? 'Регенерация...' : 'Ещё вариант' }}
            <span class="ml-2 badge badge-sm">{{ cardStore.remainingRegenerations }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Fallback: only original text, no AI -->
    <div v-if="!originalText && aiVariants.length === 0">
      <Carousel :items-to-show="1" :wrap-around="false" class="text-carousel">
        <Slide v-for="variant in cardStore.textVariants" :key="variant.id">
          <GlassCard padding="p-6">
            <div class="space-y-4">
              <div class="prose prose-invert max-w-none">
                <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap">
                  {{ variant.content }}
                </p>
              </div>
              <div class="flex justify-center pt-2">
                <label class="label cursor-pointer gap-3 bg-white/5 px-6 py-3 rounded-lg hover:bg-white/10 transition-colors">
                  <span class="label-text text-winter-snow font-semibold">Выбрать</span>
                  <input
                    type="radio"
                    :checked="cardStore.selectedTextId === variant.id"
                    @change="cardStore.selectedTextId = variant.id"
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
