import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient, APIError } from '@/api/client'

const AUTH_STORAGE_KEY = 'santa_authenticated'

export const useAuthStore = defineStore('auth', () => {
  // State
  const isAuthenticated = ref<boolean>(false)
  const isLoading = ref<boolean>(false)
  const error = ref<string | null>(null)

  // Initialize from localStorage
  function init(): void {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY)
    isAuthenticated.value = stored === 'true'
  }

  // Computed
  const needsAuth = computed(() => !isAuthenticated.value)

  // Actions

  /**
   * Verify password and authenticate user
   */
  async function login(password: string): Promise<boolean> {
    try {
      isLoading.value = true
      error.value = null

      const success = await apiClient.verifyPassword(password)

      if (success) {
        isAuthenticated.value = true
        localStorage.setItem(AUTH_STORAGE_KEY, 'true')
        return true
      }

      return false
    } catch (err) {
      if (err instanceof APIError && err.statusCode === 401) {
        error.value = 'Неверный пароль'
      } else if (err instanceof Error) {
        error.value = err.message
      } else {
        error.value = 'Ошибка авторизации'
      }
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Log out and clear authentication
   */
  function logout(): void {
    isAuthenticated.value = false
    localStorage.removeItem(AUTH_STORAGE_KEY)
  }

  /**
   * Clear error message
   */
  function clearError(): void {
    error.value = null
  }

  // Initialize on store creation
  init()

  return {
    // State
    isAuthenticated,
    isLoading,
    error,

    // Computed
    needsAuth,

    // Actions
    login,
    logout,
    clearError,
    init
  }
})
