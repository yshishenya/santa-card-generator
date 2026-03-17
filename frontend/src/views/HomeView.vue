<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, APIError } from '@/api/client'
import {
  IMAGE_STYLE_LABELS,
  type ImageStyle,
  type PhotocardImageVariant,
  type Employee,
} from '@/types'

const router = useRouter()

const fullName = ref('')
const alterEgo = ref('')
const employees = ref<Employee[]>([])
const selectedEmployeeId = ref('')
const employeesLoading = ref(false)
const sessionId = ref<string | null>(null)
const imageVariants = ref<PhotocardImageVariant[]>([])
const selectedImageIndex = ref(0)
const confirmSend = ref(false)
const isGenerating = ref(false)
const isSending = ref(false)
const error = ref<string | null>(null)
const isImageZoomed = ref(false)

const hasEmployees = computed(() => employees.value.length > 0)
const hasGenerated = computed(() => imageVariants.value.length === 3 && sessionId.value !== null)
const selectedImage = computed(() => imageVariants.value[selectedImageIndex.value] ?? null)
const selectedEmployee = computed(() => employees.value.find((employee) => employee.id === selectedEmployeeId.value))
const resolvedFullName = computed(() => {
  if (selectedEmployee.value) {
    return selectedEmployee.value.name
  }
  return fullName.value.trim()
})

function getSelectedEmployeeName(): string {
  if (selectedEmployee.value) {
    return selectedEmployee.value.name
  }
  return fullName.value.trim()
}

function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof APIError) {
    return err.getUserMessage()
  }
  if (err instanceof Error) {
    return err.message
  }
  return fallback
}

function resetGeneratedState(): void {
  sessionId.value = null
  imageVariants.value = []
  selectedImageIndex.value = 0
  confirmSend.value = false
}

function resetAll(): void {
  fullName.value = ''
  alterEgo.value = ''
  selectedEmployeeId.value = ''
  error.value = null
  resetGeneratedState()
}

function openImageZoom(index: number): void {
  selectedImageIndex.value = index
  confirmSend.value = false
  isImageZoomed.value = true
}

function closeImageZoom(): void {
  isImageZoomed.value = false
}

function selectPreviousImage(): void {
  if (imageVariants.value.length === 0) {
    return
  }
  const nextIndex = selectedImageIndex.value === 0
    ? imageVariants.value.length - 1
    : selectedImageIndex.value - 1
  selectedImageIndex.value = nextIndex
  confirmSend.value = false
}

function selectNextImage(): void {
  if (imageVariants.value.length === 0) {
    return
  }
  const nextIndex = (selectedImageIndex.value + 1) % imageVariants.value.length
  selectedImageIndex.value = nextIndex
  confirmSend.value = false
}

async function loadEmployees(): Promise<void> {
  employeesLoading.value = true
  try {
    employees.value = await apiClient.fetchEmployees()
  } catch {
    // Keep UI usable via manual input if employee list cannot be loaded.
    employees.value = []
  } finally {
    employeesLoading.value = false
  }
}

function onEmployeeSelect(): void {
  fullName.value = selectedEmployee.value?.name ?? ''
}

function getStyleLabel(style: ImageStyle): string {
  return IMAGE_STYLE_LABELS[style] ?? style
}

async function handleGenerate(): Promise<void> {
  const recipient = getSelectedEmployeeName().trim()
  if (!recipient || !alterEgo.value.trim()) {
    return
  }
  fullName.value = recipient

  try {
    isGenerating.value = true
    error.value = null
    resetGeneratedState()

    const response = await apiClient.generatePhotocard({
      full_name: recipient,
      alter_ego: alterEgo.value.trim(),
    })

    sessionId.value = response.session_id
    imageVariants.value = response.image_variants
  } catch (err) {
    error.value = getErrorMessage(err, 'Не удалось сгенерировать варианты открытки.')
  } finally {
    isGenerating.value = false
  }
}

onMounted(() => {
  loadEmployees()
})

async function handleSend(): Promise<void> {
  if (!sessionId.value || !selectedImage.value || !confirmSend.value) {
    return
  }

  try {
    isSending.value = true
    error.value = null

    const response = await apiClient.sendPhotocard({
      session_id: sessionId.value,
      selected_image_index: selectedImageIndex.value,
    })

    await router.push({
      name: 'success',
      query: {
        env: response.delivery_env,
        message_id: response.telegram_message_id ? String(response.telegram_message_id) : '',
      },
    })
  } catch (err) {
    error.value = getErrorMessage(err, 'Не удалось отправить открытку в Telegram.')
  } finally {
    isSending.value = false
  }
}
</script>

<template>
  <div class="space-y-8">
    <div class="text-center space-y-4">
      <div class="inline-flex items-center gap-3 rounded-full border border-platform-accent/30 bg-platform-bg-secondary/60 px-4 py-2 text-sm text-platform-text-secondary">
        <span class="text-lg">📸</span>
        <span>Photocard MVP</span>
      </div>
      <div>
        <h1 class="text-4xl md:text-5xl font-bold text-gradient mb-3">
          Платформа фотокарточек Pro 4.0 · 7-летие
        </h1>
        <p class="mx-auto max-w-2xl text-lg text-platform-text-secondary">
          Введите только имя получателя и альтер-эго. Сервис сгенерирует ровно 3 варианта изображения, после чего выберите один и отдельно подтвердите отправку.
        </p>
      </div>
    </div>

    <section class="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <form class="glass-card space-y-5 p-6" @submit.prevent="handleGenerate">
        <div class="space-y-2">
          <label for="full-name" class="block text-sm font-semibold uppercase tracking-[0.18em] text-platform-accent">
            Full Name
          </label>
          <div v-if="employeesLoading" class="text-sm text-platform-text-muted">
            Загрузка списка людей...
          </div>
          <template v-else-if="hasEmployees">
            <select
              id="full-name"
              v-model="selectedEmployeeId"
              class="input-magic w-full px-4 py-3 text-base"
              :disabled="isGenerating || isSending"
              @change="onEmployeeSelect"
            >
              <option value="" disabled>Выберите получателя</option>
              <option
                v-for="employee in employees"
                :key="employee.id"
                :value="employee.id"
              >
                {{ employee.name }}{{ employee.department ? ` — ${employee.department}` : '' }}
              </option>
            </select>
            <p v-if="!selectedEmployeeId" class="text-sm text-platform-text-muted">
              Выберите сотрудника из списка.
            </p>
          </template>
          <input
            v-else
            id="full-name"
            v-model="fullName"
            type="text"
            maxlength="200"
            placeholder="Введите имя получателя вручную"
            class="input-magic w-full px-4 py-3 text-base"
            :disabled="isGenerating || isSending"
          />
        </div>

        <div class="space-y-2">
          <label for="alter-ego" class="block text-sm font-semibold uppercase tracking-[0.18em] text-platform-accent">
            Alter Ego
          </label>
          <textarea
            id="alter-ego"
            v-model="alterEgo"
            rows="5"
            maxlength="200"
            placeholder="Например, creative lead with clean minimal visual style"
            class="input-magic w-full resize-none px-4 py-3 text-base"
            :disabled="isGenerating || isSending"
          ></textarea>
          <p class="text-sm text-platform-text-muted">
            По этому описанию backend выбирает стили через эвристику и fallback.
          </p>
        </div>

        <div v-if="error" class="rounded-2xl border border-platform-primary/40 bg-platform-primary/10 px-4 py-3 text-sm text-platform-primary-light">
          {{ error }}
        </div>

        <div class="flex flex-wrap gap-3">
          <button
            type="submit"
            :disabled="isGenerating || isSending || !(hasEmployees ? selectedEmployeeId : fullName.trim()) || !alterEgo.trim()"
            class="btn-magic flex-1 rounded-xl px-6 py-4 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span class="flex items-center justify-center gap-2">
              <span v-if="isGenerating" class="loading loading-spinner loading-sm"></span>
              <i v-else class="pi pi-sparkles"></i>
              <span>{{ isGenerating ? 'Генерируем 3 варианта...' : 'Сгенерировать 3 изображения' }}</span>
            </span>
          </button>

          <button
            type="button"
            class="rounded-xl border border-platform-line/30 bg-platform-bg-secondary px-5 py-4 font-semibold text-platform-text-primary transition hover:border-platform-accent/30 hover:bg-platform-line/20"
            :disabled="isGenerating || isSending"
            @click="resetAll"
          >
            Сбросить
          </button>
        </div>
      </form>

      <section class="glass-card p-6">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h2 class="text-2xl font-semibold text-platform-accent">
              Превью карточки
            </h2>
            <p class="mt-2 text-sm text-platform-text-secondary">
              После генерации выберите один из трёх вариантов и подтвердите отправку.
            </p>
          </div>
          <p v-if="sessionId" class="rounded-full border border-platform-line/30 bg-platform-bg-secondary/70 px-3 py-1 text-xs text-platform-text-muted">
            session_id: {{ sessionId }}
          </p>
        </div>

        <div v-if="!hasGenerated" class="mt-10 rounded-3xl border border-dashed border-platform-line/30 bg-platform-bg-secondary/40 px-6 py-16 text-center text-platform-text-muted">
          Сначала запустите генерацию. Здесь появятся ровно 3 варианта фотокарточки.
        </div>

        <template v-else>
          <div class="mt-6 grid gap-6 xl:grid-cols-[minmax(0,430px)_minmax(0,1fr)]">
            <div class="space-y-3">
              <h3 class="text-sm font-semibold uppercase tracking-[0.16em] text-platform-accent">
                Варианты
              </h3>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="(variant, index) in imageVariants"
                  :key="variant.url"
                  type="button"
                  class="photocard-option photocard-option--thumb text-left"
                  :class="{ 'photocard-option--active': index === selectedImageIndex }"
                  @click="openImageZoom(index)"
                >
                  <div class="aspect-[3/4] overflow-hidden rounded-[0.95rem] bg-platform-bg-secondary">
                    <img
                      :src="variant.url"
                      :alt="`Вариант ${index + 1}`"
                      class="h-full w-full object-cover"
                    />
                  </div>
                  <div class="mt-2 flex items-center justify-between gap-3">
                    <div>
                      <p class="text-[10px] uppercase tracking-[0.16em] text-platform-text-muted">
                        Вариант {{ index + 1 }}
                      </p>
                      <p class="mt-1 text-xs font-semibold text-platform-text-primary">
                        {{ getStyleLabel(variant.style) }}
                      </p>
                    </div>
                    <span
                      class="inline-flex h-7 w-7 items-center justify-center rounded-full border text-xs"
                      :class="index === selectedImageIndex ? 'border-platform-accent bg-platform-accent/15 text-platform-accent' : 'border-platform-line/30 text-platform-text-muted'"
                    >
                      {{ index + 1 }}
                    </span>
                  </div>
                </button>
              </div>
            </div>

            <div class="rounded-[2rem] border border-platform-accent/20 bg-platform-bg-secondary/60 p-5">
              <button
                v-if="selectedImage"
                type="button"
                class="group relative block w-full overflow-hidden rounded-[1.5rem] border border-platform-line/30 bg-platform-bg-primary text-left transition"
                @click="openImageZoom(selectedImageIndex)"
              >
                <img
                  :src="selectedImage.url"
                  alt="Выбранная фотокарточка"
                  class="h-auto w-full object-cover"
                />
                <span class="pointer-events-none absolute left-3 top-3 rounded-full border border-platform-accent/35 bg-platform-accent/15 px-3 py-1 text-xs font-semibold tracking-[0.14em] text-platform-accent">
                  {{ getStyleLabel(selectedImage.style) }}
                </span>
                <span class="absolute bottom-3 right-3 rounded-full border border-platform-line/40 bg-platform-bg-primary/70 px-2 py-1 text-xs text-platform-text-secondary">
                  Нажмите для увеличения
                </span>
              </button>
              <div
                v-if="isImageZoomed && selectedImage"
                class="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-4"
                @click="closeImageZoom"
              >
                <div
                  class="relative w-full max-w-2xl rounded-[1.5rem] border border-platform-line/35 bg-platform-bg-secondary p-3"
                  @click.stop
                >
                  <button
                    type="button"
                    class="absolute right-2 top-2 z-10 inline-flex h-9 w-9 items-center justify-center rounded-full border border-platform-line/40 bg-platform-bg-primary/80 text-sm text-platform-text-secondary transition hover:bg-platform-accent/20"
                    @click="closeImageZoom"
                  >
                    ×
                  </button>

                  <div class="grid place-items-center">
                    <div class="relative w-full overflow-hidden rounded-[1.2rem] bg-platform-bg-primary">
                      <img
                        :src="selectedImage.url"
                        alt="Увеличенный вид"
                        class="mx-auto max-h-[75vh] w-full rounded-[1.2rem] object-contain"
                      />

                      <button
                        type="button"
                        class="absolute left-3 top-1/2 -translate-y-1/2 rounded-full border border-platform-line/40 bg-platform-bg-primary/80 px-3 py-2 text-sm text-platform-text-secondary transition hover:bg-platform-accent/20"
                        @click="selectPreviousImage"
                      >
                        ←
                      </button>
                      <button
                        type="button"
                        class="absolute right-3 top-1/2 -translate-y-1/2 rounded-full border border-platform-line/40 bg-platform-bg-primary/80 px-3 py-2 text-sm text-platform-text-secondary transition hover:bg-platform-accent/20"
                        @click="selectNextImage"
                      >
                        →
                      </button>
                    </div>

                    <p class="mt-3 text-sm text-platform-text-secondary">
                      {{ selectedImageIndex + 1 }} / {{ imageVariants.length }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="mt-5 space-y-4">
                <div>
                  <p class="text-xs uppercase tracking-[0.18em] text-platform-text-muted">
                    Карточка получателя
                  </p>
                  <h3 class="mt-1 text-2xl font-semibold text-platform-text-primary">
                    {{ resolvedFullName }}
                  </h3>
                  <p class="mt-2 whitespace-pre-wrap text-platform-text-secondary">
                    {{ alterEgo }}
                  </p>
                </div>

                <label class="flex cursor-pointer items-start gap-3 rounded-2xl border border-platform-accent/25 bg-platform-accent/10 px-4 py-3 text-sm text-platform-text-primary">
                  <input
                    v-model="confirmSend"
                    type="checkbox"
                    class="mt-0.5 h-4 w-4 rounded border-platform-accent/60 bg-transparent"
                  />
                  <span>
                    Подтверждаю отправку выбранного изображения в Telegram с подписью только из `full_name` и `alter_ego`.
                  </span>
                </label>

                <div class="flex flex-wrap gap-3">
                  <button
                    type="button"
                    class="btn-magic rounded-xl px-6 py-3 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="!confirmSend || isSending"
                    @click="handleSend"
                  >
                    <span class="flex items-center gap-2">
                      <span v-if="isSending" class="loading loading-spinner loading-sm"></span>
                      <i v-else class="pi pi-send"></i>
                      <span>{{ isSending ? 'Отправляем...' : 'Отправить в Telegram' }}</span>
                    </span>
                  </button>
                  <button
                    type="button"
                    class="rounded-xl border border-platform-line/30 bg-transparent px-5 py-3 font-semibold text-platform-text-primary transition hover:border-platform-accent/30 hover:bg-platform-line/20"
                    :disabled="isSending"
                    @click="handleGenerate"
                  >
                    Перегенерировать 3 варианта
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>
      </section>
    </section>
  </div>
</template>

<style scoped>
.photocard-option {
  border: 1px solid rgba(186, 200, 215, 0.18);
  background: rgba(10, 22, 35, 0.58);
  border-radius: 1.35rem;
  padding: 0.9rem;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.photocard-option:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.35);
}

.photocard-option--active {
  border-color: rgba(99, 102, 241, 0.72);
  box-shadow: 0 18px 44px rgba(6, 17, 27, 0.32);
}

.photocard-option--thumb {
  padding: 0.6rem;
  max-width: 190px;
}
</style>
