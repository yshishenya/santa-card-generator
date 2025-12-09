import axios, { type AxiosInstance } from 'axios'
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
}

// Export singleton instance
export const apiClient = new APIClient()
