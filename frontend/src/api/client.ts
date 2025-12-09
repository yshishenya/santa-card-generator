import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  CardGenerationRequest,
  CardGenerationResponse,
  RegenerateRequest,
  RegenerateResponse,
  SendCardRequest,
  SendCardResponse,
  Employee,
  TextStyle,
  ImageStyle
} from '@/types'

// API timeout for generation requests (5 minutes for 9 parallel AI generations)
const GENERATION_TIMEOUT_MS = 300000

/**
 * Custom API error with detailed message from backend
 */
export class APIError extends Error {
  public readonly statusCode: number
  public readonly detail: string

  constructor(message: string, statusCode: number, detail: string) {
    super(message)
    this.name = 'APIError'
    this.statusCode = statusCode
    this.detail = detail
  }

  /**
   * Get user-friendly error message
   */
  getUserMessage(): string {
    if (this.statusCode === 429) {
      return 'Слишком много запросов. Пожалуйста, подождите минуту.'
    }
    if (this.statusCode === 404) {
      return this.detail || 'Ресурс не найден.'
    }
    if (this.statusCode >= 500) {
      return this.detail || 'Ошибка сервера. Попробуйте позже.'
    }
    return this.detail || this.message
  }
}

// Backend API response wrapper
interface APIResponse<T> {
  success: boolean
  data: T
  error: string | null
}

// Backend response types (different from frontend types)
interface BackendTextVariant {
  text: string
  style: string  // TextStyle value
}

interface BackendImageVariant {
  url: string
  style: string  // ImageStyle value
  prompt: string
}

interface BackendCardGenerationResponse {
  session_id: string
  recipient: string
  original_text: string | null
  text_variants: BackendTextVariant[]
  image_variants: BackendImageVariant[]
  remaining_text_regenerations: number
  remaining_image_regenerations: number
}

interface BackendRegenerateResponse {
  text_variants?: BackendTextVariant[]
  image_variants?: BackendImageVariant[]
  remaining_regenerations: number
}

interface BackendSendCardResponse {
  success: boolean
  message: string
  telegram_message_id: number | null
}

interface BackendAuthResponse {
  success: boolean
  message: string
}

class APIClient {
  private client: AxiosInstance

  constructor() {
    const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

    this.client = axios.create({
      baseURL: `${baseURL}/api/v1`,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: GENERATION_TIMEOUT_MS
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<{ detail?: string; error?: string }>) => {
        const statusCode = error.response?.status || 0
        const detail = error.response?.data?.detail
          || error.response?.data?.error
          || error.message
          || 'Неизвестная ошибка'

        throw new APIError(
          `API Error: ${statusCode}`,
          statusCode,
          detail
        )
      }
    )
  }

  /**
   * Generate new greeting card with text and image variants
   */
  async generateCard(request: CardGenerationRequest): Promise<CardGenerationResponse> {
    const response = await this.client.post<APIResponse<BackendCardGenerationResponse>>('/cards/generate', request)

    const backendData = response.data.data

    // Transform backend response to frontend format
    return {
      generation_id: backendData.session_id,
      original_text: backendData.original_text,
      text_variants: backendData.text_variants.map((tv, index) => ({
        id: `text-${index}`,
        content: tv.text,
        style: tv.style as TextStyle
      })),
      image_variants: backendData.image_variants.map((iv, index) => ({
        id: `image-${index}`,
        url: this.transformImageUrl(backendData.session_id, iv.url),
        style: iv.style as ImageStyle
      })),
      remaining_text_regenerations: backendData.remaining_text_regenerations,
      remaining_image_regenerations: backendData.remaining_image_regenerations
    }
  }

  /**
   * Transform generated:// URL to actual API URL
   */
  private transformImageUrl(sessionId: string, url: string): string {
    if (url.startsWith('generated://')) {
      const imageId = url.replace('generated://', '')
      const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      return `${baseURL}/api/v1/cards/images/${sessionId}/${imageId}`
    }
    return url
  }

  /**
   * Regenerate all text or image variants
   */
  async regenerate(request: RegenerateRequest, sessionId: string): Promise<RegenerateResponse> {
    // Transform frontend request to backend format
    const backendRequest = {
      session_id: request.generation_id,
      element_type: request.type
    }

    const response = await this.client.post<APIResponse<BackendRegenerateResponse>>('/cards/regenerate', backendRequest)
    const backendData = response.data.data

    // Transform response based on type
    const result: RegenerateResponse = {
      remaining_regenerations: backendData.remaining_regenerations
    }

    if (request.type === 'text' && backendData.text_variants) {
      result.text_variants = backendData.text_variants.map((tv, index) => ({
        id: `text-regen-${Date.now()}-${index}`,
        content: tv.text,
        style: tv.style as TextStyle
      }))
    } else if (request.type === 'image' && backendData.image_variants) {
      result.image_variants = backendData.image_variants.map((iv, index) => ({
        id: `image-regen-${Date.now()}-${index}`,
        url: this.transformImageUrl(sessionId, iv.url),
        style: iv.style as ImageStyle
      }))
    }

    return result
  }

  /**
   * Send selected card to Telegram
   */
  async sendCard(request: SendCardRequest): Promise<SendCardResponse> {
    // Transform frontend request to backend format
    const backendRequest = {
      session_id: request.generation_id,
      employee_name: request.recipient,
      selected_text_index: request.selected_text_index,
      selected_image_index: request.selected_image_index,
      use_original_text: request.use_original_text,
      include_original_text: request.include_original_text
    }

    const response = await this.client.post<APIResponse<BackendSendCardResponse>>('/cards/send', backendRequest)
    const backendData = response.data.data

    return {
      success: backendData.success,
      message: backendData.message
    }
  }

  /**
   * Get list of employees for autocomplete
   */
  async getEmployees(): Promise<Employee[]> {
    const response = await this.client.get<Employee[]>('/employees')
    return response.data
  }

  /**
   * Verify application password.
   */
  async verifyPassword(password: string): Promise<boolean> {
    const response = await this.client.post<BackendAuthResponse>('/auth/verify', { password })
    return response.data.success
  }
}

// Export singleton instance
export const apiClient = new APIClient()
