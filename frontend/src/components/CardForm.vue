<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCardStore } from '@/stores/card'
import { apiClient } from '@/api/client'
import { TextStyle, ImageStyle, type Employee } from '@/types'
// AutoComplete is registered globally in main.ts

const cardStore = useCardStore()

// Form data - recipient can be Employee object or string (when typing)
const recipient = ref<Employee | string>('')
const sender = ref<string>('')

// Extract recipient name - handles both Employee object and string
const recipientName = computed(() => {
  if (!recipient.value) return ''
  if (typeof recipient.value === 'string') return recipient.value
  return recipient.value.name
})
const reason = ref<string>('')
const message = ref<string>('')
const enhanceText = ref<boolean>(false)
const textStyle = ref<TextStyle>(TextStyle.ODE)
const imageStyle = ref<ImageStyle>(ImageStyle.DIGITAL_ART)

// Employees for autocomplete
const employees = ref<Employee[]>([])
const filteredEmployees = ref<Employee[]>([])

// Text style options
const textStyleOptions = [
  { value: TextStyle.ODE, label: 'Торжественная ода' },
  { value: TextStyle.FUTURE, label: 'Отчет из будущего' },
  { value: TextStyle.HAIKU, label: 'Хайку' },
  { value: TextStyle.NEWSPAPER, label: 'Заметка в газете' },
  { value: TextStyle.STANDUP, label: 'Дружеский стендап' }
]

// Image style options
const imageStyleOptions = [
  { value: ImageStyle.DIGITAL_ART, label: 'Цифровая живопись' },
  { value: ImageStyle.PIXEL_ART, label: 'Пиксель-арт' },
  { value: ImageStyle.SPACE, label: 'Космическая фантастика' },
  { value: ImageStyle.MOVIE, label: 'Кадр из фильма' }
]

// Load employees on mount
onMounted(async () => {
  try {
    employees.value = await apiClient.getEmployees()
  } catch {
    // Employee loading failed, autocomplete won't work but form is still usable
  }
})

// Autocomplete search event type
interface AutoCompleteSearchEvent {
  query: string
}

// Autocomplete search
const searchEmployees = (event: AutoCompleteSearchEvent): void => {
  const query = event.query.toLowerCase()
  filteredEmployees.value = employees.value.filter(emp =>
    emp.name.toLowerCase().includes(query)
  )
}

// Submit form
const handleSubmit = async (): Promise<void> => {
  if (!recipientName.value) {
    return
  }

  try {
    await cardStore.generate({
      recipient: recipientName.value,
      sender: sender.value || undefined,
      reason: reason.value || undefined,
      message: message.value || undefined,
      enhance_text: enhanceText.value,
      text_style: enhanceText.value ? textStyle.value : undefined,
      image_style: imageStyle.value
    })
  } catch {
    // Error is handled by the store and displayed in the UI
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <!-- Recipient field with autocomplete -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg">Кому <span class="text-christmas-red">*</span></span>
      </label>
      <AutoComplete
        v-model="recipient"
        :suggestions="filteredEmployees"
        @complete="searchEmployees"
        optionLabel="name"
        placeholder="Начните вводить имя сотрудника"
        class="w-full"
        inputClass="input input-bordered w-full bg-white/10 text-winter-snow border-white/20"
        required
      />
    </div>

    <!-- Sender field -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg">От кого (необязательно)</span>
      </label>
      <input
        v-model="sender"
        type="text"
        placeholder="Ваше имя"
        class="input input-bordered w-full bg-white/10 text-winter-snow border-white/20 placeholder:text-winter-snow/50"
      />
    </div>

    <!-- Reason field -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg">За что (необязательно)</span>
        <span class="label-text-alt text-winter-snow/60">Макс. 150 символов</span>
      </label>
      <input
        v-model="reason"
        type="text"
        placeholder="За вклад в проект, за помощь..."
        maxlength="150"
        class="input input-bordered w-full bg-white/10 text-winter-snow border-white/20 placeholder:text-winter-snow/50"
      />
    </div>

    <!-- Message field -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg">Сообщение (необязательно)</span>
        <span class="label-text-alt text-winter-snow/60">Макс. 1000 символов</span>
      </label>
      <textarea
        v-model="message"
        placeholder="Ваше пожелание или благодарность..."
        maxlength="1000"
        rows="4"
        class="textarea textarea-bordered w-full bg-white/10 text-winter-snow border-white/20 placeholder:text-winter-snow/50"
      ></textarea>
    </div>

    <!-- Enhance text checkbox -->
    <div class="form-control">
      <label class="label cursor-pointer justify-start gap-3">
        <input
          v-model="enhanceText"
          type="checkbox"
          class="checkbox checkbox-primary"
        />
        <span class="label-text text-winter-snow text-lg">Улучшить текст с помощью AI</span>
      </label>
    </div>

    <!-- Text style selection (visible when enhance is checked) -->
    <div v-if="enhanceText" class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg">Стиль текста</span>
      </label>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label
          v-for="option in textStyleOptions"
          :key="option.value"
          class="label cursor-pointer bg-white/5 p-4 rounded-lg border border-white/10 hover:bg-white/10 transition-colors"
          :class="{ 'bg-christmas-green/30 border-christmas-green': textStyle === option.value }"
        >
          <span class="label-text text-winter-snow">{{ option.label }}</span>
          <input
            v-model="textStyle"
            type="radio"
            :value="option.value"
            class="radio radio-primary"
          />
        </label>
      </div>
    </div>

    <!-- Image style selection -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg">Стиль изображения <span class="text-christmas-red">*</span></span>
      </label>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label
          v-for="option in imageStyleOptions"
          :key="option.value"
          class="label cursor-pointer bg-white/5 p-4 rounded-lg border border-white/10 hover:bg-white/10 transition-colors"
          :class="{ 'bg-christmas-green/30 border-christmas-green': imageStyle === option.value }"
        >
          <span class="label-text text-winter-snow">{{ option.label }}</span>
          <input
            v-model="imageStyle"
            type="radio"
            :value="option.value"
            class="radio radio-primary"
            required
          />
        </label>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="cardStore.error" class="alert alert-error">
      <i class="pi pi-exclamation-triangle"></i>
      <span>{{ cardStore.error }}</span>
      <button type="button" class="btn btn-sm btn-ghost" @click="cardStore.clearError()">
        <i class="pi pi-times"></i>
      </button>
    </div>

    <!-- Submit button -->
    <div class="pt-4">
      <button
        type="submit"
        :disabled="cardStore.isGenerating || !recipientName"
        class="btn btn-lg w-full bg-christmas-red hover:bg-christmas-red-dark border-0 text-white text-lg"
      >
        <span v-if="cardStore.isGenerating" class="loading loading-spinner"></span>
        <i v-else class="pi pi-sparkles mr-2"></i>
        {{ cardStore.isGenerating ? 'Создаём волшебство...' : 'Сгенерировать открытку' }}
      </button>
    </div>
  </form>
</template>
