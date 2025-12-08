// Text styles for AI generation
export enum TextStyle {
  ODE = 'ode',              // Торжественная ода
  FUTURE = 'future',        // Отчет из будущего
  HAIKU = 'haiku',          // Хайку
  NEWSPAPER = 'newspaper',  // Заметка в газете
  STANDUP = 'standup'       // Дружеский стендап
}

// Image styles for AI generation
export enum ImageStyle {
  DIGITAL_ART = 'digital_art',  // Цифровая живопись
  PIXEL_ART = 'pixel_art',      // Пиксель-арт
  SPACE = 'space',              // Космическая фантастика
  MOVIE = 'movie'               // Кадр из фильма
}

// Employee data
export interface Employee {
  name: string
  telegram_username?: string
}

// Card generation request
export interface CardGenerationRequest {
  recipient: string
  sender?: string
  reason?: string
  message?: string
  enhance_text: boolean
  text_style?: TextStyle
  image_style: ImageStyle
}

// Text variant
export interface TextVariant {
  id: string
  content: string
}

// Image variant
export interface ImageVariant {
  id: string
  url: string
}

// Card generation response
export interface CardGenerationResponse {
  generation_id: string
  text_variants: TextVariant[]
  image_variants: ImageVariant[]
  remaining_regenerations: number
}

// Regenerate request
export interface RegenerateRequest {
  generation_id: string
  type: 'text' | 'image'
  style?: TextStyle | ImageStyle
}

// Regenerate response
export interface RegenerateResponse {
  variant: TextVariant | ImageVariant
  remaining_regenerations: number
}

// Send card request
export interface SendCardRequest {
  generation_id: string
  recipient: string
  text_variant_id: string
  image_variant_id: string
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
