import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient, APIError } from '@/api/client'
import type {
  CardGenerationRequest,
  TextVariant,
  ImageVariant,
  ImageStyle
} from '@/types'

/**
 * Extract user-friendly error message from error
 */
function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof APIError) {
    return err.getUserMessage()
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
}

export const useCardStore = defineStore('card', () => {
  // State
  const generationId = ref<string | null>(null)
  const recipient = ref<string | null>(null)
  const sender = ref<string | null>(null)  // Sender name (От кого)
  const reason = ref<string | null>(null)  // Reason for gratitude (За что)
  const originalText = ref<string | null>(null)  // User's original message
  const textVariants = ref<TextVariant[]>([])  // 5 AI variants (one per style)
  const imageVariants = ref<ImageVariant[]>([])  // 4 variants (one per style)
  const selectedTextIndex = ref<number>(0)  // Index-based selection
  const selectedImageIndex = ref<number>(0)  // Index-based selection
  const useOriginalText = ref<boolean>(false)  // When true, use original text instead of AI variant
  const includeOriginalText = ref<boolean>(true)  // When true, include original text alongside AI text (default: true)
  const remainingTextRegenerations = ref<number>(3)
  const remainingImageRegenerations = ref<number>(3)
  const selectedImageStyles = ref<ImageStyle[]>([])  // User-selected image styles for generation

  // Loading states
  const isGenerating = ref(false)
  const isGeneratingImages = ref(false)  // For initial image generation
  const isRegeneratingText = ref(false)
  const isRegeneratingImages = ref(false)
  const isSending = ref(false)

  // Error state
  const error = ref<string | null>(null)

  // Computed
  const hasGeneration = computed(() => generationId.value !== null)
  const hasImages = computed(() => imageVariants.value.length > 0)
  const canGenerateImages = computed(() => selectedImageStyles.value.length > 0 && selectedImageStyles.value.length <= 4)
  const canRegenerateText = computed(() => remainingTextRegenerations.value > 0)
  const canRegenerateImages = computed(() => remainingImageRegenerations.value > 0 && hasImages.value)
  const hasOriginalText = computed(() => originalText.value !== null && originalText.value.length > 0)

  const canSend = computed(() => {
    // Can send if we have either original text selected or a valid AI text index
    const hasValidText = useOriginalText.value
      ? hasOriginalText.value
      : (textVariants.value.length > 0 && selectedTextIndex.value >= 0)
    const hasValidImage = imageVariants.value.length > 0 && selectedImageIndex.value >= 0
    return hasValidText && hasValidImage
  })

  const selectedText = computed(() => {
    if (useOriginalText.value) {
      return originalText.value
    }
    return textVariants.value[selectedTextIndex.value]?.content ?? null
  })

  const selectedTextVariant = computed(() =>
    textVariants.value[selectedTextIndex.value]
  )

  const selectedImageVariant = computed(() =>
    imageVariants.value[selectedImageIndex.value]
  )

  // Actions

  /**
   * Generate new card with text and image variants (5 text + 4 image)
   */
  async function generate(request: CardGenerationRequest): Promise<void> {
    try {
      isGenerating.value = true
      error.value = null
      const response = await apiClient.generateCard(request)

      generationId.value = response.generation_id
      recipient.value = request.recipient
      sender.value = request.sender ?? null
      reason.value = request.reason ?? null
      originalText.value = response.original_text
      textVariants.value = response.text_variants
      imageVariants.value = response.image_variants
      remainingTextRegenerations.value = response.remaining_text_regenerations
      remainingImageRegenerations.value = response.remaining_image_regenerations

      // Auto-select first variants
      selectedTextIndex.value = 0
      selectedImageIndex.value = 0
      useOriginalText.value = false
      includeOriginalText.value = true  // Default to including original text with AI variant
    } catch (err) {
      error.value = getErrorMessage(err, 'Не удалось создать открытку. Попробуйте ещё раз.')
      throw err
    } finally {
      isGenerating.value = false
    }
  }

  /**
   * Regenerate ALL text variants (5 new variants, one per style)
   */
  async function regenerateText(): Promise<void> {
    if (!generationId.value || !canRegenerateText.value) return

    try {
      isRegeneratingText.value = true
      error.value = null

      const response = await apiClient.regenerate(
        { generation_id: generationId.value, type: 'text' },
        generationId.value
      )

      // Replace all text variants
      if (response.text_variants) {
        textVariants.value = response.text_variants
        // Keep selection at first variant
        selectedTextIndex.value = 0
      }

      remainingTextRegenerations.value = response.remaining_regenerations
    } catch (err) {
      error.value = getErrorMessage(err, 'Не удалось перегенерировать текст. Попробуйте ещё раз.')
      throw err
    } finally {
      isRegeneratingText.value = false
    }
  }

  /**
   * Toggle image style selection (for initial generation)
   */
  function toggleImageStyle(style: ImageStyle): void {
    const index = selectedImageStyles.value.indexOf(style)
    if (index === -1) {
      // Only allow up to 4 styles
      if (selectedImageStyles.value.length < 4) {
        selectedImageStyles.value.push(style)
      }
    } else {
      selectedImageStyles.value.splice(index, 1)
    }
  }

  /**
   * Check if an image style is selected
   */
  function isImageStyleSelected(style: ImageStyle): boolean {
    return selectedImageStyles.value.includes(style)
  }

  /**
   * Generate images for selected styles (initial generation)
   */
  async function generateImages(): Promise<void> {
    if (!generationId.value || !canGenerateImages.value) return

    try {
      isGeneratingImages.value = true
      error.value = null

      const response = await apiClient.generateImages(
        generationId.value,
        selectedImageStyles.value
      )

      imageVariants.value = response.image_variants
      remainingImageRegenerations.value = response.remaining_image_regenerations
      selectedImageIndex.value = 0
    } catch (err) {
      error.value = getErrorMessage(err, 'Не удалось сгенерировать изображения. Попробуйте ещё раз.')
      throw err
    } finally {
      isGeneratingImages.value = false
    }
  }

  /**
   * Regenerate ALL image variants (new variants for the same styles)
   */
  async function regenerateImages(): Promise<void> {
    if (!generationId.value || !canRegenerateImages.value) return

    try {
      isRegeneratingImages.value = true
      error.value = null

      const response = await apiClient.regenerate(
        { generation_id: generationId.value, type: 'image' },
        generationId.value
      )

      // Replace all image variants
      if (response.image_variants) {
        imageVariants.value = response.image_variants
        // Keep selection at first variant
        selectedImageIndex.value = 0
      }

      remainingImageRegenerations.value = response.remaining_regenerations
    } catch (err) {
      error.value = getErrorMessage(err, 'Не удалось перегенерировать изображения. Попробуйте ещё раз.')
      throw err
    } finally {
      isRegeneratingImages.value = false
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

      await apiClient.sendCard({
        generation_id: generationId.value,
        recipient: recipient.value,
        selected_text_index: selectedTextIndex.value,
        selected_image_index: selectedImageIndex.value,
        use_original_text: useOriginalText.value,
        include_original_text: includeOriginalText.value
      })
    } catch (err) {
      error.value = getErrorMessage(err, 'Не удалось отправить открытку. Попробуйте ещё раз.')
      throw err
    } finally {
      isSending.value = false
    }
  }

  /**
   * Select text variant by index
   */
  function selectTextVariant(index: number): void {
    if (index >= 0 && index < textVariants.value.length) {
      selectedTextIndex.value = index
      useOriginalText.value = false  // Switching to AI text
    }
  }

  /**
   * Select image variant by index
   */
  function selectImageVariant(index: number): void {
    if (index >= 0 && index < imageVariants.value.length) {
      selectedImageIndex.value = index
    }
  }

  /**
   * Set whether to use original text instead of AI variant
   */
  function setUseOriginalText(value: boolean): void {
    useOriginalText.value = value
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
    sender.value = null
    reason.value = null
    originalText.value = null
    textVariants.value = []
    imageVariants.value = []
    selectedTextIndex.value = 0
    selectedImageIndex.value = 0
    useOriginalText.value = false
    includeOriginalText.value = true  // Default to including original text with AI variant
    remainingTextRegenerations.value = 3
    remainingImageRegenerations.value = 3
    selectedImageStyles.value = []  // Clear selected styles
    isGenerating.value = false
    isGeneratingImages.value = false
    isRegeneratingText.value = false
    isRegeneratingImages.value = false
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
    sender,
    reason,
    originalText,
    textVariants,
    imageVariants,
    selectedTextIndex,
    selectedImageIndex,
    useOriginalText,
    includeOriginalText,
    remainingTextRegenerations,
    remainingImageRegenerations,
    selectedImageStyles,
    isGenerating,
    isGeneratingImages,
    isRegeneratingText,
    isRegeneratingImages,
    isSending,
    error,

    // Computed
    hasGeneration,
    hasImages,
    canGenerateImages,
    canRegenerateText,
    canRegenerateImages,
    hasOriginalText,
    canSend,
    selectedText,
    selectedTextVariant,
    selectedImageVariant,

    // Actions
    generate,
    generateImages,
    toggleImageStyle,
    isImageStyleSelected,
    regenerateText,
    regenerateImages,
    send,
    selectTextVariant,
    selectImageVariant,
    setUseOriginalText,
    setIncludeOriginalText,
    reset,
    clearError
  }
})
