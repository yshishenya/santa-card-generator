const PLAYER_NAME_STORAGE_KEY = 'p40_player_name'

export function loadPlayerName(): string {
  return localStorage.getItem(PLAYER_NAME_STORAGE_KEY)?.trim() ?? ''
}

export function savePlayerName(value: string): void {
  const normalizedValue = value.trim()
  if (normalizedValue) {
    localStorage.setItem(PLAYER_NAME_STORAGE_KEY, normalizedValue)
    return
  }

  localStorage.removeItem(PLAYER_NAME_STORAGE_KEY)
}

export { PLAYER_NAME_STORAGE_KEY }
