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
    <!-- Page title -->
    <div class="text-center">
      <h1 class="text-4xl font-bold text-winter-snow mb-2">
        Новогодняя открытка
      </h1>
      <p class="text-lg text-winter-snow/80">
        Создайте персональное поздравление с помощью AI
      </p>
    </div>

    <!-- Card generation form -->
    <CardForm v-if="!showPreview" />

    <!-- Generation preview and selection -->
    <GenerationPreview v-else />
  </div>
</template>
