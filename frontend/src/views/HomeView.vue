<script setup lang="ts">
import { computed } from 'vue'
import { useCardStore } from '@/stores/card'
import CardForm from '@/components/CardForm.vue'
import GenerationPreview from '@/components/GenerationPreview.vue'

const cardStore = useCardStore()

const showPreview = computed(() => cardStore.hasGeneration)
</script>

<template>
  <div class="space-y-8">
    <!-- Page title with festive styling -->
    <div class="text-center mb-4">
      <div class="inline-block relative mb-4">
        <span class="text-5xl">🎄</span>
        <span class="absolute -top-1 -right-3 text-2xl animate-sparkle">✨</span>
      </div>
      <h1 class="text-4xl md:text-5xl font-bold text-gradient mb-3">
        Новогодняя открытка
      </h1>
      <p class="text-lg text-winter-text-secondary max-w-md mx-auto">
        Создайте персональное поздравление с помощью <span class="text-christmas-gold font-semibold">AI</span>
      </p>
    </div>

    <!-- Card generation form -->
    <CardForm v-if="!showPreview" />

    <!-- Generation preview and selection -->
    <GenerationPreview v-else />
  </div>
</template>
