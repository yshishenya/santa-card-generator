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

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
</style>
