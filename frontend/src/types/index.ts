export enum ImageStyle {
  KNITTED = 'knitted',
  MAGIC_REALISM = 'magic_realism',
  PIXEL_ART = 'pixel_art',
  VINTAGE_RUSSIAN = 'vintage_russian',
  SOVIET_POSTER = 'soviet_poster',
  HYPERREALISM = 'hyperrealism',
  DIGITAL_3D = 'digital_3d',
  FANTASY = 'fantasy',
  COMIC_BOOK = 'comic_book',
  WATERCOLOR = 'watercolor',
  CYBERPUNK = 'cyberpunk',
  PAPER_CUTOUT = 'paper_cutout',
  POP_ART = 'pop_art',
  LEGO = 'lego',
  LINOCUT = 'linocut',
}

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

export interface PhotocardGenerateRequest {
  full_name: string
  alter_ego: string
}

export interface PhotocardImageVariant {
  url: string
  style: ImageStyle
}

export interface PhotocardGenerateResponse {
  session_id: string
  image_variants: PhotocardImageVariant[]
}

export interface PhotocardSendRequest {
  session_id: string
  selected_image_index: number
}

export interface PhotocardSendResponse {
  success: boolean
  message: string
  telegram_message_id: number | null
  delivery_env: 'staging' | 'prod'
}

export interface APIError {
  detail: string
}
