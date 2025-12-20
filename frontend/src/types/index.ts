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

// Image styles for AI generation (all 15 styles matching backend)
export enum ImageStyle {
  KNITTED = 'knitted',              // Уютный трикотаж
  MAGIC_REALISM = 'magic_realism',  // Магический реализм
  PIXEL_ART = 'pixel_art',          // Пиксель-арт
  VINTAGE_RUSSIAN = 'vintage_russian', // Винтажная открытка
  SOVIET_POSTER = 'soviet_poster',  // Советский плакат
  HYPERREALISM = 'hyperrealism',    // Гиперреализм
  DIGITAL_3D = 'digital_3d',        // 3D-графика
  FANTASY = 'fantasy',              // Фэнтези
  COMIC_BOOK = 'comic_book',        // Комикс
  WATERCOLOR = 'watercolor',        // Акварель
  CYBERPUNK = 'cyberpunk',          // Киберпанк
  PAPER_CUTOUT = 'paper_cutout',    // Бумажная аппликация
  POP_ART = 'pop_art',              // Поп-арт
  LEGO = 'lego',                    // LEGO
  LINOCUT = 'linocut'               // Линогравюра
}

// Human-readable labels for image styles
export const IMAGE_STYLE_LABELS: Record<ImageStyle, string> = {
  [ImageStyle.KNITTED]: 'Уютный трикотаж',
  [ImageStyle.MAGIC_REALISM]: 'Магический реализм',
  [ImageStyle.PIXEL_ART]: 'Пиксель-арт',
  [ImageStyle.VINTAGE_RUSSIAN]: 'Винтажная открытка',
  [ImageStyle.SOVIET_POSTER]: 'Советский плакат',
  [ImageStyle.HYPERREALISM]: 'Гиперреализм',
  [ImageStyle.DIGITAL_3D]: '3D-графика',
  [ImageStyle.FANTASY]: 'Фэнтези',
  [ImageStyle.COMIC_BOOK]: 'Комикс',
  [ImageStyle.WATERCOLOR]: 'Акварель',
  [ImageStyle.CYBERPUNK]: 'Киберпанк',
  [ImageStyle.PAPER_CUTOUT]: 'Бумажная аппликация',
  [ImageStyle.POP_ART]: 'Поп-арт',
  [ImageStyle.LEGO]: 'LEGO',
  [ImageStyle.LINOCUT]: 'Линогравюра',
}

// All available image styles for selection
export const ALL_IMAGE_STYLES: ImageStyle[] = [
  ImageStyle.KNITTED,
  ImageStyle.MAGIC_REALISM,
  ImageStyle.PIXEL_ART,
  ImageStyle.VINTAGE_RUSSIAN,
  ImageStyle.SOVIET_POSTER,
  ImageStyle.HYPERREALISM,
  ImageStyle.DIGITAL_3D,
  ImageStyle.FANTASY,
  ImageStyle.COMIC_BOOK,
  ImageStyle.WATERCOLOR,
  ImageStyle.CYBERPUNK,
  ImageStyle.PAPER_CUTOUT,
  ImageStyle.POP_ART,
  ImageStyle.LEGO,
  ImageStyle.LINOCUT,
]

// Employee data
export interface Employee {
  name: string
  telegram_username?: string
}

// Card generation request (generates text variants only)
export interface CardGenerationRequest {
  recipient: string
  sender?: string
  reason?: string
  message?: string
}

// Generate images request (for selected styles)
export interface GenerateImagesRequest {
  session_id: string
  image_styles: ImageStyle[]
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
  image_variants: ImageVariant[]  // Empty until generate-images called
  remaining_text_regenerations: number
  remaining_image_regenerations: number
}

// Generate images response
export interface GenerateImagesResponse {
  image_variants: ImageVariant[]
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
