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
            <h2 class="text-2xl font-bold text-gradient flex items-center gap-2">
              <i class="pi pi-eye text-aurora-cyan"></i>
              Предпросмотр открытки
            </h2>
            <button
              @click="handleClose"
              class="btn btn-sm btn-circle btn-ghost text-winter-snow hover:bg-aurora-purple/20 hover:text-aurora-purple transition-all"
            >
              <i class="pi pi-times text-xl"></i>
            </button>
          </div>

          <!-- Content -->
          <div class="p-6 space-y-6">
            <!-- Recipient -->
            <div class="text-center">
              <span class="text-winter-snow/60">Для:</span>
              <span class="text-aurora-cyan font-bold ml-2 text-lg">{{ cardStore.recipient }}</span>
            </div>

            <!-- Selected image -->
            <div v-if="selectedImage" class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="badge badge-lg bg-aurora-pink/20 text-aurora-pink border-aurora-pink/30">
                  <i class="pi pi-image mr-1"></i>
                  {{ imageLabel }}
                </span>
              </div>
              <div class="aspect-[3/2] bg-slate-800 rounded-xl overflow-hidden ring-1 ring-white/10">
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
                <span class="badge badge-lg bg-aurora-purple/20 text-aurora-purple border-aurora-purple/30">
                  <i class="pi pi-align-left mr-1"></i>
                  {{ textLabel }}
                </span>
              </div>
              <div class="bg-white/5 p-4 rounded-xl border border-white/5">
                <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap">
                  {{ displayText }}
                </p>
              </div>

              <!-- Original text addition indicator -->
              <div
                v-if="!cardStore.useOriginalText && cardStore.includeOriginalText && cardStore.originalText"
                class="bg-aurora-cyan/10 p-3 rounded-lg border border-aurora-cyan/20"
              >
                <p class="text-aurora-cyan/80 text-sm mb-2">
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
              class="flex-1 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 border border-white/20 text-winter-snow font-semibold transition-all duration-300 hover:border-white/30 flex items-center justify-center gap-2"
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
