import axios, { type AxiosInstance } from 'axios'
import type {
  CardGenerationRequest,
  CardGenerationResponse,
  RegenerateRequest,
  RegenerateResponse,
  SendCardRequest,
  SendCardResponse,
  Employee,
  ImageStyle
} from '@/types'

// Backend API response wrapper
interface APIResponse<T> {
  success: boolean
  data: T
  error: string | null
}

// Backend response types (different from frontend types)
interface BackendTextVariant {
  text: string
  style: string  // 'original' or TextStyle value
}

interface BackendImageVariant {
  url: string
  style: ImageStyle
  prompt: string
}

interface BackendCardGenerationResponse {
  session_id: string
  recipient: string
  text_variants: BackendTextVariant[]
  image_variants: BackendImageVariant[]
  remaining_regenerations: number
}

interface BackendRegenerateResponse {
  variant: BackendTextVariant | BackendImageVariant
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
      timeout: 180000 // 3 minutes for AI generation
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
      text_variants: backendData.text_variants.map((tv, index) => ({
        id: `text-${index}`,
        content: tv.text,
        style: tv.style
      })),
      image_variants: backendData.image_variants.map((iv, index) => ({
        id: `image-${index}`,
        url: this.transformImageUrl(backendData.session_id, iv.url)
      })),
      remaining_regenerations: backendData.remaining_regenerations
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
   * Regenerate text or image variant
   */
  async regenerate(request: RegenerateRequest): Promise<RegenerateResponse> {
    // Transform frontend request to backend format
    const backendRequest = {
      session_id: request.generation_id,
      element_type: request.type,
      element_index: 0 // Backend regenerates and adds to list
    }

    const response = await this.client.post<APIResponse<BackendRegenerateResponse>>('/cards/regenerate', backendRequest)
    const backendData = response.data.data

    // Transform response based on type
    if (request.type === 'text') {
      const tv = backendData.variant as BackendTextVariant
      return {
        variant: {
          id: `text-regen-${Date.now()}`,
          content: tv.text,
          style: tv.style  // AI-generated variants always have a style
        },
        remaining_regenerations: backendData.remaining_regenerations
      }
    } else {
      const iv = backendData.variant as BackendImageVariant
      return {
        variant: {
          id: `image-regen-${Date.now()}`,
          url: this.transformImageUrl(request.generation_id, iv.url)
        },
        remaining_regenerations: backendData.remaining_regenerations
      }
    }
  }

  /**
   * Send selected card to Telegram
   */
  async sendCard(request: SendCardRequest): Promise<SendCardResponse> {
    // Transform frontend request to backend format
    // Extract index from id (e.g., "text-0" -> 0)
    const textIndex = parseInt(request.text_variant_id.split('-').pop() || '0', 10)
    const imageIndex = parseInt(request.image_variant_id.split('-').pop() || '0', 10)

    const backendRequest = {
      session_id: request.generation_id,
      employee_name: request.recipient,
      selected_text_index: textIndex,
      selected_image_index: imageIndex,
      include_original_text: request.include_original_text || false
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
