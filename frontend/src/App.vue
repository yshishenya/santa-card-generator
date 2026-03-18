<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const isLoginPage = computed(() => route.name === 'login')
</script>

<template>
  <div class="min-h-screen overflow-x-hidden bg-platform relative overflow-hidden">
    <div class="ambient-orbs">
      <div class="ambient-orb orb-bottom-left"></div>
      <div class="ambient-orb orb-bottom-right"></div>
      <div class="ambient-orb orb-mid-left"></div>
      <div class="ambient-orb orb-top-right"></div>
    </div>

    <div
      class="relative z-10"
      :class="isLoginPage ? 'flex min-h-screen items-center justify-center px-4 py-6 sm:px-6' : 'container mx-auto px-3 py-4 sm:px-4 sm:py-8'"
    >
      <div :class="isLoginPage ? 'w-full max-w-md' : 'mx-auto w-full max-w-5xl'">
        <RouterView v-if="isLoginPage" />

        <div v-else class="main-card mb-4 p-4 sm:mb-8 sm:p-8">
          <RouterView />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bg-platform {
  background:
    radial-gradient(ellipse at 50% 100%, rgba(30, 64, 175, 0.18) 0%, transparent 50%),
    linear-gradient(180deg, #060c1a 0%, #0b1222 30%, #101a34 60%, #16213a 100%);
}

.ambient-orbs {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.ambient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  animation: ambientPulse 8s ease-in-out infinite;
}

.orb-bottom-left {
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(79, 70, 229, 0.16) 0%, transparent 72%);
  bottom: -120px;
  left: -120px;
}

.orb-bottom-right {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.14) 0%, transparent 70%);
  right: -100px;
  bottom: 14%;
  animation-delay: -3s;
}

.orb-mid-left {
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, transparent 72%);
  left: 14%;
  top: 32%;
  animation-delay: -5s;
}

.orb-top-right {
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.14) 0%, transparent 70%);
  top: 12%;
  right: 20%;
  animation-delay: -7s;
}

@keyframes ambientPulse {
  0%, 100% {
    opacity: 0.65;
    transform: scale(1);
  }

  50% {
    opacity: 1;
    transform: scale(1.08);
  }
}

.main-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 28px;
  background: linear-gradient(
    135deg,
    rgba(20, 32, 58, 0.95) 0%,
    rgba(16, 26, 48, 0.9) 100%
  );
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow:
    0 4px 40px rgba(0, 0, 0, 0.4),
    0 0 70px rgba(99, 102, 241, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.main-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 28px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(56, 189, 248, 0.28) 0%,
    rgba(99, 102, 241, 0.35) 50%,
    rgba(56, 189, 248, 0.28) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

@media (max-width: 640px) {
  .ambient-orb {
    filter: blur(60px);
  }

  .main-card,
  .main-card::before {
    border-radius: 24px;
  }
}
</style>
