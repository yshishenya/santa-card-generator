<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCardStore } from '@/stores/card'
import GlassCard from './GlassCard.vue'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const router = useRouter()
const cardStore = useCardStore()

// Get selected image
const selectedImage = computed(() => cardStore.selectedImageVariant)

// Determine what text to show
const showBothTexts = computed(() => {
  // Show both texts when: using AI text AND including original text AND have original text
  return !cardStore.useOriginalText && cardStore.includeOriginalText && cardStore.originalText
})

const showOnlyOriginal = computed(() => {
  // Show only original when: using original text (user chose to not use AI)
  return cardStore.useOriginalText
})

const showOnlyAI = computed(() => {
  // Show only AI text when: using AI text AND NOT including original
  return !cardStore.useOriginalText && !cardStore.includeOriginalText
})

// Get display texts
const originalTextDisplay = computed(() => cardStore.originalText)
const aiTextDisplay = computed(() => cardStore.selectedTextVariant?.content ?? null)

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
              Предпросмотр
            </h2>
            <button
              @click="handleClose"
              class="btn btn-sm btn-circle btn-ghost text-winter-text-muted hover:bg-christmas-gold/10 hover:text-christmas-gold transition-all"
            >
              <i class="pi pi-times text-xl"></i>
            </button>
          </div>

          <!-- Telegram-style preview -->
          <div class="p-4">
            <div class="bg-[#0e1621] rounded-2xl overflow-hidden shadow-xl max-w-md mx-auto">
              <!-- Image -->
              <div v-if="selectedImage" class="aspect-[3/2]">
                <img
                  :src="selectedImage.url"
                  alt="Открытка"
                  class="w-full h-full object-cover"
                />
              </div>

              <!-- Caption (Telegram style) -->
              <div class="p-4 text-[15px] leading-relaxed text-white/90 space-y-3">
                <!-- Кому -->
                <p>
                  <span class="font-semibold">Кому:</span>
                  {{ cardStore.recipient }}
                </p>

                <!-- За что -->
                <p v-if="cardStore.reason">
                  <span class="font-semibold">За что:</span>
                  {{ cardStore.reason }}
                </p>

                <!-- Text content -->
                <template v-if="showBothTexts">
                  <!-- Both original and AI text -->
                  <div>
                    <p class="font-semibold mb-1">Слова благодарности:</p>
                    <p class="whitespace-pre-wrap">{{ originalTextDisplay }}</p>
                  </div>
                  <div>
                    <p class="font-semibold mb-1">ИИ-креатив:</p>
                    <p class="whitespace-pre-wrap">{{ aiTextDisplay }}</p>
                  </div>
                </template>

                <template v-else-if="showOnlyOriginal">
                  <!-- Only original text (no header) -->
                  <p class="whitespace-pre-wrap">{{ originalTextDisplay }}</p>
                </template>

                <template v-else-if="showOnlyAI">
                  <!-- Only AI text (no header) -->
                  <p class="whitespace-pre-wrap">{{ aiTextDisplay }}</p>
                </template>

                <!-- От кого -->
                <p v-if="cardStore.sender">
                  <span class="font-semibold">От кого:</span>
                  {{ cardStore.sender }}
                </p>
              </div>
            </div>

            <!-- Telegram hint -->
            <p class="text-center text-winter-text-muted text-sm mt-3">
              <i class="pi pi-info-circle mr-1"></i>
              Так открытка будет выглядеть в Telegram
            </p>
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
              <span>{{ cardStore.isSending ? 'Отправляем...' : 'Отправить' }}</span>
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
