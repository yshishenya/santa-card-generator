<script setup lang="ts">
import { loadSlim } from 'tsparticles-slim'
import type { Engine, Container } from 'tsparticles-engine'
import { useParticlesConfig } from '@/composables/useParticles'

const particlesConfig = useParticlesConfig()

const particlesInit = async (engine: Engine): Promise<void> => {
  await loadSlim(engine)
}

const particlesLoaded = async (_container: Container): Promise<void> => {
  // Particles loaded successfully
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
