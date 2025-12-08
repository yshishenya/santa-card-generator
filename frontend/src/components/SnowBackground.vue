<script setup lang="ts">
import { loadSlim } from 'tsparticles-slim'
import { useParticlesConfig } from '@/composables/useParticles'

const particlesConfig = useParticlesConfig()

const particlesInit = async (engine: any) => {
  await loadSlim(engine)
}

const particlesLoaded = async (container: any) => {
  console.log('Particles loaded:', container)
}
</script>

<template>
  <vue-particles
    id="tsparticles"
    :particlesInit="particlesInit"
    :particlesLoaded="particlesLoaded"
    :options="particlesConfig"
    class="absolute inset-0 z-0"
  />
</template>
