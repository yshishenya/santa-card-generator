<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCardStore } from '@/stores/card'
import { TEXT_STYLE_LABELS, IMAGE_STYLE_LABELS } from '@/types'
import GlassCard from './GlassCard.vue'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const cardStore = useCardStore()

// Get display text - either original or AI variant
const displayText = computed(() => {
  if (cardStore.useOriginalText) {
    return cardStore.originalText
  }
  return cardStore.selectedTextVariant?.content ?? null
})

// Get text label
const textLabel = computed(() => {
  if (cardStore.useOriginalText) {
    return 'Ваш текст'
  }
  const variant = cardStore.selectedTextVariant
  return variant ? TEXT_STYLE_LABELS[variant.style] : ''
})

// Get image URL and label
const selectedImage = computed(() => cardStore.selectedImageVariant)
const imageLabel = computed(() => {
  return selectedImage.value ? IMAGE_STYLE_LABELS[selectedImage.value.style] : ''
})

// Handle send
const handleSend = async () => {
  try {
    await cardStore.send()
    emit('close')
    router.push('/success')
  } catch {
    // Error is handled by the store
  }
}

// Handle close
const handleClose = () => {
  emit('close')
}

// Handle backdrop click
const handleBackdropClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget) {
    handleClose()
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm"
        @click="handleBackdropClick"
      >
        <GlassCard
          class="w-full max-w-2xl max-h-[90vh] overflow-y-auto"
          padding="p-0"
        >
          <!-- Header -->
          <div class="sticky top-0 z-10 bg-winter-bg-card/95 backdrop-blur p-4 border-b border-christmas-gold/20 flex items-center justify-between">
            <h2 class="text-2xl font-bold text-gradient flex items-center gap-2">
              <i class="pi pi-eye text-christmas-gold"></i>
              Предпросмотр открытки
            </h2>
            <button
              @click="handleClose"
              class="btn btn-sm btn-circle btn-ghost text-winter-text-muted hover:bg-christmas-gold/10 hover:text-christmas-gold transition-all"
            >
              <i class="pi pi-times text-xl"></i>
            </button>
          </div>

          <!-- Content -->
          <div class="p-6 space-y-6">
            <!-- Recipient -->
            <div class="text-center">
              <span class="text-winter-text-muted">Для:</span>
              <span class="text-christmas-gold font-bold ml-2 text-lg">{{ cardStore.recipient }}</span>
            </div>

            <!-- Selected image -->
            <div v-if="selectedImage" class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="badge badge-lg bg-christmas-red/15 text-christmas-red-light border-christmas-red/30">
                  <i class="pi pi-image mr-1"></i>
                  {{ imageLabel }}
                </span>
              </div>
              <div class="aspect-[3/2] bg-winter-bg-secondary rounded-xl overflow-hidden ring-1 ring-christmas-gold/20">
                <img
                  :src="selectedImage.url"
                  :alt="imageLabel"
                  class="w-full h-full object-cover"
                />
              </div>
            </div>

            <!-- Selected text -->
            <div v-if="displayText" class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="badge badge-lg bg-christmas-gold/15 text-christmas-gold border-christmas-gold/30">
                  <i class="pi pi-align-left mr-1"></i>
                  {{ textLabel }}
                </span>
              </div>
              <div class="bg-winter-bg-secondary/50 p-4 rounded-xl border border-winter-frost/30">
                <p class="text-winter-text-primary text-lg leading-relaxed whitespace-pre-wrap">
                  {{ displayText }}
                </p>
              </div>

              <!-- Original text addition indicator -->
              <div
                v-if="!cardStore.useOriginalText && cardStore.includeOriginalText && cardStore.originalText"
                class="bg-christmas-green/10 p-3 rounded-lg border border-christmas-green/20"
              >
                <p class="text-christmas-green-light text-sm mb-2">
                  <i class="pi pi-plus-circle mr-1"></i>
                  Также будет добавлен ваш текст:
                </p>
                <p class="text-winter-text-secondary text-sm whitespace-pre-wrap">
                  {{ cardStore.originalText }}
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="sticky bottom-0 bg-winter-bg-card/95 backdrop-blur p-4 border-t border-christmas-gold/20 flex gap-4">
            <button
              @click="handleClose"
              class="flex-1 px-6 py-3 rounded-xl bg-winter-bg-secondary hover:bg-winter-frost/30 border border-winter-frost/30 text-winter-text-primary font-semibold transition-all duration-300 hover:border-christmas-gold/30 flex items-center justify-center gap-2"
            >
              <i class="pi pi-arrow-left"></i>
              Назад
            </button>
            <button
              @click="handleSend"
              :disabled="cardStore.isSending"
              class="btn-magic flex-1 px-6 py-3 rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="cardStore.isSending" class="loading loading-spinner"></span>
              <i v-else class="pi pi-send"></i>
              <span>{{ cardStore.isSending ? 'Отправляем...' : 'Отправить в Telegram' }}</span>
            </button>
          </div>
        </GlassCard>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .glass-card,
.modal-leave-to .glass-card {
  transform: scale(0.9);
}
</style>
