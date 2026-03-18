<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const centeredRoutes = new Set(['login', 'success'])

const shellClass = computed(() => {
  if (route.name === 'print-assets') {
    return 'app-shell--archive'
  }
  if (route.name === 'success') {
    return 'app-shell--success'
  }
  if (route.name === 'login') {
    return 'app-shell--login'
  }
  return 'app-shell--studio'
})

const isCentered = computed(() => centeredRoutes.has(String(route.name ?? '')))
</script>

<template>
  <div class="app-shell" :class="shellClass">
    <div class="app-shell__wash"></div>
    <div class="app-shell__grid"></div>
    <div class="app-shell__beam app-shell__beam--left"></div>
    <div class="app-shell__beam app-shell__beam--right"></div>
    <div class="app-shell__corner app-shell__corner--top"></div>
    <div class="app-shell__corner app-shell__corner--bottom"></div>

    <main class="app-shell__viewport" :class="{ 'app-shell__viewport--centered': isCentered }">
      <div class="app-shell__container">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.app-shell__viewport {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  padding: 1rem;
}

.app-shell__viewport--centered {
  display: grid;
  align-items: center;
}

.app-shell__container {
  width: min(100%, 84rem);
  margin: 0 auto;
}

.app-shell--login .app-shell__container,
.app-shell--success .app-shell__container {
  width: min(100%, 78rem);
}

.app-shell__wash,
.app-shell__grid,
.app-shell__beam,
.app-shell__corner {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.app-shell__wash {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 251, 255, 0.98)),
    #f8fbff;
}

.app-shell__grid {
  background-image:
    linear-gradient(rgba(185, 205, 255, 0.26) 1px, transparent 1px),
    linear-gradient(90deg, rgba(185, 205, 255, 0.26) 1px, transparent 1px);
  background-size: 4rem 4rem;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.22), transparent 94%);
}

.app-shell__beam {
  filter: blur(88px);
  opacity: 0.34;
}

.app-shell__beam--left {
  background: radial-gradient(circle, rgba(175, 195, 255, 0.34) 0%, transparent 65%);
  transform: translate(-38%, 2%);
}

.app-shell__beam--right {
  background: radial-gradient(circle, rgba(130, 255, 240, 0.26) 0%, transparent 64%);
  transform: translate(38%, -12%);
}

.app-shell__corner::before,
.app-shell__corner::after {
  content: '';
  position: absolute;
  width: 0.7rem;
  height: 0.7rem;
  border: 1px solid rgba(0, 0, 0, 0.26);
  background: #ffffff;
}

.app-shell__corner--top::before {
  top: 1.35rem;
  left: 1.35rem;
  background: #3382ff;
}

.app-shell__corner--top::after {
  top: 1.35rem;
  left: 2.25rem;
  background: #afc3ff;
}

.app-shell__corner--bottom::before {
  right: 1.35rem;
  bottom: 1.35rem;
  background: #82fff0;
}

.app-shell__corner--bottom::after {
  right: 2.25rem;
  bottom: 1.35rem;
  background: #ffeb14;
}

@media (min-width: 768px) {
  .app-shell__viewport {
    padding: 1.5rem 1.75rem 2rem;
  }
}
</style>
