<script setup lang="ts">
import SnowBackground from './components/SnowBackground.vue'
</script>

<template>
  <div class="min-h-screen bg-christmas relative overflow-hidden">
    <!-- Christmas gradient orbs -->
    <div class="christmas-orbs">
      <div class="christmas-orb orb-red"></div>
      <div class="christmas-orb orb-green"></div>
      <div class="christmas-orb orb-gold"></div>
      <div class="christmas-orb orb-red-2"></div>
    </div>

    <!-- Decorative stars -->
    <div class="stars">
      <div class="star star-1">&#10022;</div>
      <div class="star star-2">&#10022;</div>
      <div class="star star-3">&#10022;</div>
      <div class="star star-4">&#10022;</div>
      <div class="star star-5">&#10022;</div>
    </div>

    <!-- Snow effect background -->
    <SnowBackground />

    <!-- Main content -->
    <div class="relative z-10 container mx-auto px-4 py-8">
      <div class="max-w-5xl mx-auto">
        <!-- Glass card container with christmas glow -->
        <div class="main-card p-8 mb-8">
          <RouterView />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Christmas night background */
.bg-christmas {
  background:
    radial-gradient(ellipse at 20% 0%, rgba(139, 0, 0, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(0, 100, 0, 0.12) 0%, transparent 50%),
    linear-gradient(180deg, #0A0F14 0%, #0D1117 50%, #101820 100%);
}

/* Christmas gradient orbs */
.christmas-orbs {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.christmas-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  animation: floatOrb 25s ease-in-out infinite;
}

/* Red Christmas orb */
.orb-red {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(220, 38, 38, 0.35) 0%, transparent 70%);
  top: -150px;
  left: -100px;
  animation-delay: 0s;
}

/* Green Christmas orb */
.orb-green {
  width: 450px;
  height: 450px;
  background: radial-gradient(circle, rgba(22, 163, 74, 0.3) 0%, transparent 70%);
  bottom: -100px;
  right: -80px;
  animation-delay: -8s;
}

/* Gold Christmas orb */
.orb-gold {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(245, 158, 11, 0.25) 0%, transparent 70%);
  top: 30%;
  right: 10%;
  animation-delay: -15s;
}

/* Second red orb */
.orb-red-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(185, 28, 28, 0.2) 0%, transparent 70%);
  bottom: 20%;
  left: 5%;
  animation-delay: -20s;
}

/* Decorative stars */
.stars {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.star {
  position: absolute;
  color: rgba(255, 215, 0, 0.6);
  font-size: 20px;
  animation: twinkle 3s ease-in-out infinite;
  text-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
}

.star-1 {
  top: 10%;
  left: 15%;
  animation-delay: 0s;
  font-size: 16px;
}

.star-2 {
  top: 25%;
  right: 20%;
  animation-delay: 0.5s;
  font-size: 24px;
}

.star-3 {
  top: 60%;
  left: 8%;
  animation-delay: 1s;
  font-size: 14px;
}

.star-4 {
  top: 15%;
  right: 10%;
  animation-delay: 1.5s;
  font-size: 18px;
}

.star-5 {
  bottom: 30%;
  right: 15%;
  animation-delay: 2s;
  font-size: 20px;
}

@keyframes floatOrb {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(40px, -20px) scale(1.05);
  }
  50% {
    transform: translate(-30px, 30px) scale(0.95);
  }
  75% {
    transform: translate(20px, -10px) scale(1.02);
  }
}

@keyframes twinkle {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.main-card {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.03) 100%
  );
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 32px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.5),
    0 0 60px rgba(220, 38, 38, 0.08),
    0 0 80px rgba(22, 163, 74, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

/* Subtle Christmas gradient border effect */
.main-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 32px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(220, 38, 38, 0.25) 0%,
    rgba(245, 158, 11, 0.15) 50%,
    rgba(22, 163, 74, 0.25) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
</style>
