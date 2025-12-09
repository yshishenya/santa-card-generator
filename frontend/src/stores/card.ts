import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api/client'
import type {
  CardGenerationRequest,
  TextVariant,
  ImageVariant,
  RegenerateRequest,
  SendCardRequest,
  TextStyle,
  ImageStyle
} from '@/types'

export const useCardStore = defineStore('card', () => {
  // State
  const generationId = ref<string | null>(null)
  const recipient = ref<string | null>(null)
  const textVariants = ref<TextVariant[]>([])
  const imageVariants = ref<ImageVariant[]>([])
  const selectedTextId = ref<string | null>(null)
  const selectedImageId = ref<string | null>(null)
  const remainingRegenerations = ref<number>(3)
  const includeOriginalText = ref<boolean>(false)  // When true, send both original and AI text

  // Loading states
  const isGenerating = ref(false)
  const isRegenerating = ref(false)
  const isSending = ref(false)

  // Error state
  const error = ref<string | null>(null)

  // Computed
  const hasGeneration = computed(() => generationId.value !== null)
  const canRegenerate = computed(() => remainingRegenerations.value > 0)
  const canSend = computed(() => selectedTextId.value !== null && selectedImageId.value !== null)

  const selectedText = computed(() =>
    textVariants.value.find(v => v.id === selectedTextId.value)
  )

  const selectedImage = computed(() =>
    imageVariants.value.find(v => v.id === selectedImageId.value)
  )

  // Actions

  /**
   * Generate new card with text and image variants
   */
  async function generate(request: CardGenerationRequest): Promise<void> {
    try {
      isGenerating.value = true
      error.value = null
      const response = await apiClient.generateCard(request)

      generationId.value = response.generation_id
      recipient.value = request.recipient
      textVariants.value = response.text_variants
      imageVariants.value = response.image_variants
      remainingRegenerations.value = response.remaining_regenerations

      // Auto-select first variants
      if (textVariants.value.length > 0) {
        selectedTextId.value = textVariants.value[0].id
      }
      if (imageVariants.value.length > 0) {
        selectedImageId.value = imageVariants.value[0].id
      }
    } catch (err) {
      error.value = 'Не удалось создать открытку. Попробуйте ещё раз.'
      throw err
    } finally {
      isGenerating.value = false
    }
  }

  /**
   * Regenerate text variant with new style
   */
  async function regenerateText(style?: TextStyle): Promise<void> {
    if (!generationId.value || !canRegenerate.value) return

    try {
      isRegenerating.value = true
      error.value = null
      const request: RegenerateRequest = {
        generation_id: generationId.value,
        type: 'text',
        style
      }

      const response = await apiClient.regenerate(request)

      // Add new variant to the list
      const newVariant = response.variant as TextVariant
      textVariants.value.push(newVariant)

      // Auto-select the new variant
      selectedTextId.value = newVariant.id

      remainingRegenerations.value = response.remaining_regenerations
    } catch (err) {
      error.value = 'Не удалось перегенерировать текст. Попробуйте ещё раз.'
      throw err
    } finally {
      isRegenerating.value = false
    }
  }

  /**
   * Regenerate image variant with new style
   */
  async function regenerateImage(style?: ImageStyle): Promise<void> {
    if (!generationId.value || !canRegenerate.value) return

    try {
      isRegenerating.value = true
      error.value = null
      const request: RegenerateRequest = {
        generation_id: generationId.value,
        type: 'image',
        style
      }

      const response = await apiClient.regenerate(request)

      // Add new variant to the list
      const newVariant = response.variant as ImageVariant
      imageVariants.value.push(newVariant)

      // Auto-select the new variant
      selectedImageId.value = newVariant.id

      remainingRegenerations.value = response.remaining_regenerations
    } catch (err) {
      error.value = 'Не удалось перегенерировать изображение. Попробуйте ещё раз.'
      throw err
    } finally {
      isRegenerating.value = false
    }
  }

  /**
   * Send selected card to Telegram
   */
  async function send(): Promise<void> {
    if (!generationId.value || !canSend.value || !recipient.value) return

    try {
      isSending.value = true
      error.value = null
      const request: SendCardRequest = {
        generation_id: generationId.value,
        recipient: recipient.value,
        text_variant_id: selectedTextId.value!,
        image_variant_id: selectedImageId.value!,
        include_original_text: includeOriginalText.value
      }

      await apiClient.sendCard(request)
    } catch (err) {
      error.value = 'Не удалось отправить открытку. Попробуйте ещё раз.'
      throw err
    } finally {
      isSending.value = false
    }
  }

  /**
   * Set whether to include original text alongside AI text
   */
  function setIncludeOriginalText(value: boolean): void {
    includeOriginalText.value = value
  }

  /**
   * Reset store to initial state
   */
  function reset(): void {
    generationId.value = null
    recipient.value = null
    textVariants.value = []
    imageVariants.value = []
    selectedTextId.value = null
    selectedImageId.value = null
    remainingRegenerations.value = 3
    includeOriginalText.value = false
    isGenerating.value = false
    isRegenerating.value = false
    isSending.value = false
    error.value = null
  }

  function clearError(): void {
    error.value = null
  }

  return {
    // State
    generationId,
    recipient,
    textVariants,
    imageVariants,
    selectedTextId,
    selectedImageId,
    remainingRegenerations,
    includeOriginalText,
    isGenerating,
    isRegenerating,
    isSending,
    error,

    // Computed
    hasGeneration,
    canRegenerate,
    canSend,
    selectedText,
    selectedImage,

    // Actions
    generate,
    regenerateText,
    regenerateImage,
    send,
    setIncludeOriginalText,
    reset,
    clearError
  }
})
