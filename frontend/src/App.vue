<script setup lang="ts">
import SnowBackground from './components/SnowBackground.vue'
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-winter-bg-primary via-slate-900 to-winter-bg-secondary relative overflow-hidden">
    <!-- Snow effect background -->
    <SnowBackground />

    <!-- Main content -->
    <div class="relative z-10 container mx-auto px-4 py-8">
      <div class="max-w-5xl mx-auto">
        <!-- Glass card container -->
        <div class="glass-card p-8 mb-8">
          <RouterView />
        </div>
      </div>
    </div>
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
