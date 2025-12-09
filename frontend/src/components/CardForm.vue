<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCardStore } from '@/stores/card'
import { apiClient } from '@/api/client'
import type { Employee } from '@/types'

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

// Employees for autocomplete
const employees = ref<Employee[]>([])
const filteredEmployees = ref<Employee[]>([])

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

// Submit form - generates 5 text variants + 4 image variants automatically
const handleSubmit = async (): Promise<void> => {
  if (!recipientName.value) {
    return
  }

  try {
    await cardStore.generate({
      recipient: recipientName.value,
      sender: sender.value || undefined,
      reason: reason.value || undefined,
      message: message.value || undefined
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
        <span class="label-text text-winter-snow text-lg font-medium">Кому <span class="text-aurora-pink">*</span></span>
      </label>
      <AutoComplete
        v-model="recipient"
        :suggestions="filteredEmployees"
        @complete="searchEmployees"
        optionLabel="name"
        placeholder="Начните вводить имя сотрудника"
        class="w-full"
        inputClass="input-magic w-full px-4 py-3 text-base"
        required
      />
    </div>

    <!-- Sender field -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg font-medium">От кого <span class="text-winter-snow/40">(необязательно)</span></span>
      </label>
      <input
        v-model="sender"
        type="text"
        placeholder="Ваше имя"
        class="input-magic w-full px-4 py-3 text-base"
      />
    </div>

    <!-- Reason field -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg font-medium">За что <span class="text-winter-snow/40">(необязательно)</span></span>
        <span class="label-text-alt text-winter-snow/50 text-sm">Макс. 150 символов</span>
      </label>
      <input
        v-model="reason"
        type="text"
        placeholder="За вклад в проект, за помощь..."
        maxlength="150"
        class="input-magic w-full px-4 py-3 text-base"
      />
    </div>

    <!-- Message field -->
    <div class="form-control">
      <label class="label">
        <span class="label-text text-winter-snow text-lg font-medium">Сообщение <span class="text-winter-snow/40">(необязательно)</span></span>
        <span class="label-text-alt text-winter-snow/50 text-sm">Макс. 1000 символов</span>
      </label>
      <textarea
        v-model="message"
        placeholder="Ваше пожелание или благодарность..."
        maxlength="1000"
        rows="4"
        class="input-magic w-full px-4 py-3 text-base resize-none"
      ></textarea>
    </div>

    <!-- Error message -->
    <div v-if="cardStore.error" class="glass-card bg-red-500/20 border-red-500/30 p-4 flex items-center gap-3">
      <i class="pi pi-exclamation-triangle text-red-400 text-xl"></i>
      <span class="flex-1 text-red-200">{{ cardStore.error }}</span>
      <button type="button" class="text-red-300 hover:text-red-100 transition-colors" @click="cardStore.clearError()">
        <i class="pi pi-times"></i>
      </button>
    </div>

    <!-- Submit button -->
    <div class="pt-4">
      <button
        type="submit"
        :disabled="cardStore.isGenerating || !recipientName"
        class="btn-magic w-full px-6 py-4 text-lg font-semibold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none group"
      >
        <span class="flex items-center justify-center gap-2">
          <span v-if="cardStore.isGenerating" class="loading loading-spinner"></span>
          <i v-else class="pi pi-sparkles group-hover:animate-sparkle"></i>
          <span>{{ cardStore.isGenerating ? 'Создаём волшебство...' : 'Сгенерировать открытку' }}</span>
        </span>
      </button>
    </div>
  </form>
</template>
