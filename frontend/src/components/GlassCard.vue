<script setup lang="ts">
interface Props {
  padding?: string
}

withDefaults(defineProps<Props>(), {
  padding: 'p-6'
})
</script>

<template>
  <div class="glass-card" :class="padding">
    <slot />
  </div>
</template>

<!-- Uses global .glass-card utility class from main.css -->
