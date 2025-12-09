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
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
        @click="handleBackdropClick"
      >
        <GlassCard
          class="w-full max-w-2xl max-h-[90vh] overflow-y-auto"
          padding="p-0"
        >
          <!-- Header -->
          <div class="sticky top-0 z-10 bg-slate-900/90 backdrop-blur p-4 border-b border-white/10 flex items-center justify-between">
            <h2 class="text-2xl font-bold text-winter-snow flex items-center gap-2">
              <i class="pi pi-eye text-christmas-gold"></i>
              Предпросмотр открытки
            </h2>
            <button
              @click="handleClose"
              class="btn btn-sm btn-circle btn-ghost text-winter-snow"
            >
              <i class="pi pi-times text-xl"></i>
            </button>
          </div>

          <!-- Content -->
          <div class="p-6 space-y-6">
            <!-- Recipient -->
            <div class="text-center">
              <span class="text-winter-snow/60">Для:</span>
              <span class="text-christmas-gold font-bold ml-2 text-lg">{{ cardStore.recipient }}</span>
            </div>

            <!-- Selected image -->
            <div v-if="selectedImage" class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="badge badge-lg bg-christmas-green/20 text-christmas-green border-christmas-green/30">
                  <i class="pi pi-image mr-1"></i>
                  {{ imageLabel }}
                </span>
              </div>
              <div class="aspect-square bg-slate-800 rounded-xl overflow-hidden">
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
                <span class="badge badge-lg bg-christmas-gold/20 text-christmas-gold border-christmas-gold/30">
                  <i class="pi pi-align-left mr-1"></i>
                  {{ textLabel }}
                </span>
              </div>
              <div class="bg-white/5 p-4 rounded-xl">
                <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap">
                  {{ displayText }}
                </p>
              </div>

              <!-- Original text addition indicator -->
              <div
                v-if="!cardStore.useOriginalText && cardStore.includeOriginalText && cardStore.originalText"
                class="bg-christmas-gold/10 p-3 rounded-lg border border-christmas-gold/20"
              >
                <p class="text-christmas-gold/80 text-sm mb-2">
                  <i class="pi pi-plus-circle mr-1"></i>
                  Также будет добавлен ваш текст:
                </p>
                <p class="text-winter-snow/80 text-sm whitespace-pre-wrap">
                  {{ cardStore.originalText }}
                </p>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="sticky bottom-0 bg-slate-900/90 backdrop-blur p-4 border-t border-white/10 flex gap-4">
            <button
              @click="handleClose"
              class="btn btn-lg flex-1 bg-white/10 hover:bg-white/20 border-white/20 text-winter-snow"
            >
              <i class="pi pi-arrow-left mr-2"></i>
              Назад
            </button>
            <button
              @click="handleSend"
              :disabled="cardStore.isSending"
              class="btn btn-lg flex-1 bg-christmas-green hover:bg-christmas-green-dark border-0 text-white"
            >
              <span v-if="cardStore.isSending" class="loading loading-spinner"></span>
              <i v-else class="pi pi-send mr-2"></i>
              {{ cardStore.isSending ? 'Отправляем...' : 'Отправить в Telegram' }}
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
