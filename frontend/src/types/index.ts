// Text styles for AI generation
export enum TextStyle {
  ODE = 'ode',              // Торжественная ода
  FUTURE = 'future',        // Отчет из будущего
  HAIKU = 'haiku',          // Хайку
  NEWSPAPER = 'newspaper',  // Заметка в газете
  STANDUP = 'standup'       // Дружеский стендап
}

// Human-readable labels for text styles
export const TEXT_STYLE_LABELS: Record<TextStyle, string> = {
  [TextStyle.ODE]: 'Торжественная ода',
  [TextStyle.HAIKU]: 'Хайку',
  [TextStyle.FUTURE]: 'Отчет из будущего',
  [TextStyle.STANDUP]: 'Дружеский стендап',
  [TextStyle.NEWSPAPER]: 'Заметка в газете',
}

// Image styles for AI generation
export enum ImageStyle {
  DIGITAL_ART = 'digital_art',  // Цифровая живопись
  PIXEL_ART = 'pixel_art',      // Пиксель-арт
  SPACE = 'space',              // Космическая фантастика
  MOVIE = 'movie'               // Кадр из фильма
}

// Human-readable labels for image styles
export const IMAGE_STYLE_LABELS: Record<ImageStyle, string> = {
  [ImageStyle.DIGITAL_ART]: 'Цифровая живопись',
  [ImageStyle.SPACE]: 'Космическая фантастика',
  [ImageStyle.PIXEL_ART]: 'Пиксель-арт',
  [ImageStyle.MOVIE]: 'Кадр из фильма',
}

// Employee data
export interface Employee {
  name: string
  telegram_username?: string
}

// Card generation request (simplified - all styles generated automatically)
export interface CardGenerationRequest {
  recipient: string
  sender?: string
  reason?: string
  message?: string
}

// Text variant with style info
export interface TextVariant {
  id: string
  content: string
  style: TextStyle
}

// Image variant with style info
export interface ImageVariant {
  id: string
  url: string
  style: ImageStyle
}

// Card generation response
export interface CardGenerationResponse {
  generation_id: string
  original_text: string | null  // User's original message
  text_variants: TextVariant[]  // 5 AI variants (one per style)
  image_variants: ImageVariant[]  // 4 variants (one per style)
  remaining_text_regenerations: number
  remaining_image_regenerations: number
}

// Regenerate request (regenerates ALL variants of specified type)
export interface RegenerateRequest {
  generation_id: string
  type: 'text' | 'image'
}

// Regenerate response (returns ALL new variants)
export interface RegenerateResponse {
  text_variants?: TextVariant[]  // 5 new text variants if text was regenerated
  image_variants?: ImageVariant[]  // 4 new image variants if images were regenerated
  remaining_regenerations: number
}

// Send card request
export interface SendCardRequest {
  generation_id: string
  recipient: string
  selected_text_index: number  // Index of selected AI text variant
  selected_image_index: number  // Index of selected image variant
  use_original_text: boolean  // When true, use original text instead of AI variant
  include_original_text: boolean  // When true, include original text alongside AI text
}

// Send card response
export interface SendCardResponse {
  success: boolean
  message: string
}

// API error response
export interface APIError {
  detail: string
}
