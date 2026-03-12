import axios, { type AxiosInstance, type AxiosError } from 'axios'
import type {
  PhotocardGenerateRequest,
  PhotocardGenerateResponse,
  PhotocardSendRequest,
  PhotocardSendResponse,
} from '@/types'

const GENERATION_TIMEOUT_MS = 300000

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

interface APIResponse<T> {
  success: boolean
  data: T
  error: string | null
}

interface BackendPhotocardImageVariant {
  url: string
  style: string
}

interface BackendPhotocardGenerateResponse {
  session_id: string
  image_variants: [
    BackendPhotocardImageVariant,
    BackendPhotocardImageVariant,
    BackendPhotocardImageVariant,
  ]
}

interface BackendPhotocardSendResponse {
  success: boolean
  message: string
  telegram_message_id: number | null
  delivery_env: 'staging' | 'prod'
}

interface BackendAuthResponse {
  success: boolean
  message: string
}

class APIClient {
  private client: AxiosInstance
  private baseURL: string

  constructor() {
    // Use relative URL for production, env variable for development
    this.baseURL = import.meta.env.VITE_API_URL || ''

    this.client = axios.create({
      baseURL: `${this.baseURL}/api/v1`,
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

  private transformImageUrl(sessionId: string, url: string): string {
    if (url.startsWith('generated://')) {
      const imageId = url.replace('generated://', '')
      return `${this.baseURL}/api/v1/photocards/images/${sessionId}/${imageId}`
    }
    return url
  }

  async generatePhotocard(
    request: PhotocardGenerateRequest
  ): Promise<PhotocardGenerateResponse> {
    const response = await this.client.post<APIResponse<BackendPhotocardGenerateResponse>>(
      '/photocards/generate',
      request
    )
    const backendData = response.data.data

    return {
      session_id: backendData.session_id,
      image_variants: backendData.image_variants.map((iv) => ({
        url: this.transformImageUrl(backendData.session_id, iv.url),
        style: iv.style as PhotocardGenerateResponse['image_variants'][number]['style'],
      })) as PhotocardGenerateResponse['image_variants'],
    }
  }

  async sendPhotocard(request: PhotocardSendRequest): Promise<PhotocardSendResponse> {
    const response = await this.client.post<APIResponse<BackendPhotocardSendResponse>>(
      '/photocards/send',
      request
    )
    const backendData = response.data.data

    return {
      success: backendData.success,
      message: backendData.message,
      telegram_message_id: backendData.telegram_message_id,
      delivery_env: backendData.delivery_env,
    }
  }

  async verifyPassword(password: string): Promise<boolean> {
    const response = await this.client.post<BackendAuthResponse>('/auth/verify', { password })
    return response.data.success
  }
}

// Export singleton instance
export const apiClient = new APIClient()
