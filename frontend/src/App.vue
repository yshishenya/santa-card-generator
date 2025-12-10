<script setup lang="ts">
import { ref } from 'vue'
import SnowGlobe from './components/SnowGlobe.vue'

// Reward messages for discovered objects
const REWARD_MESSAGES: Record<string, { emoji: string; title: string; hint: string }> = {
  gift: {
    emoji: '🎁',
    title: 'Секрет найден!',
    hint: 'Попробуй стиль "Гиперреализм" — твоя благодарность станет осязаемой, как хрустальный шар со снегом внутри ✨',
  },
  star: {
    emoji: '⭐',
    title: 'Звезда желаний!',
    hint: 'Стиль "Космос" превратит твои слова в созвездие — пусть благодарность сияет как галактика 🌌',
  },
  tree: {
    emoji: '🎄',
    title: 'Новогоднее чудо!',
    hint: 'Попробуй "Пиксель-арт" — ретро-магия 16-бит для тех, кто ценит классику 🎮',
  },
  snowman: {
    emoji: '⛄',
    title: 'Снеговик-советник!',
    hint: 'Стиль "Кино" сделает открытку эпичной — представь кадр из блокбастера о благодарности 🎬',
  },
}

// Toast state
const showToast = ref(false)
const toastData = ref<{ emoji: string; title: string; hint: string } | null>(null)

function handleObjectClicked(type: string, _reward: string) {
  const message = REWARD_MESSAGES[type]
  if (message) {
    toastData.value = message
    showToast.value = true

    // Auto-hide after 6 seconds
    setTimeout(() => {
      showToast.value = false
    }, 6000)
  }
}

function closeToast() {
  showToast.value = false
}
</script>

<template>
  <div class="min-h-screen bg-christmas relative overflow-hidden">
    <!-- Blue ambient glow orbs -->
    <div class="ambient-orbs">
      <div class="ambient-orb orb-bottom-left"></div>
      <div class="ambient-orb orb-bottom-right"></div>
      <div class="ambient-orb orb-mid-left"></div>
      <div class="ambient-orb orb-top-right"></div>
    </div>

    <!-- Decorative stars -->
    <div class="stars">
      <div class="star star-1">&#10022;</div>
      <div class="star star-2">&#10022;</div>
      <div class="star star-3">&#10022;</div>
      <div class="star star-4">&#10022;</div>
      <div class="star star-5">&#10022;</div>
    </div>

    <!-- Interactive snow globe background -->
    <SnowGlobe @object-clicked="handleObjectClicked" />

    <!-- Reward Toast Notification -->
    <Transition name="toast">
      <div v-if="showToast && toastData" class="reward-toast">
        <button class="toast-close" @click="closeToast">×</button>
        <div class="toast-emoji">{{ toastData.emoji }}</div>
        <div class="toast-content">
          <div class="toast-title">{{ toastData.title }}</div>
          <div class="toast-hint">{{ toastData.hint }}</div>
        </div>
      </div>
    </Transition>

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
/* Magical Winter Night Background */
.bg-christmas {
  background:
    radial-gradient(ellipse at 50% 100%, rgba(42, 74, 111, 0.8) 0%, transparent 50%),
    linear-gradient(180deg, #050D18 0%, #0B1929 30%, #122640 60%, #1A3355 100%);
}

/* Blue ambient glow orbs - create depth and atmosphere */
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

/* Bottom-left: Main blue glow - strongest presence */
.orb-bottom-left {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(51, 130, 254, 0.25) 0%, rgba(33, 112, 232, 0.1) 50%, transparent 70%);
  bottom: 10%;
  left: 5%;
  animation-delay: 0s;
}

/* Bottom-right: Secondary blue glow */
.orb-bottom-right {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(77, 154, 255, 0.2) 0%, rgba(51, 130, 254, 0.08) 50%, transparent 70%);
  bottom: 20%;
  right: 10%;
  animation-delay: -3s;
}

/* Mid-left: Soft cyan-blue accent */
.orb-mid-left {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(122, 180, 255, 0.18) 0%, transparent 70%);
  top: 30%;
  left: 15%;
  animation-delay: -5s;
}

/* Top-right: Distant subtle glow */
.orb-top-right {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(153, 200, 255, 0.15) 0%, transparent 70%);
  top: 15%;
  right: 20%;
  animation-delay: -7s;
}

/* Bright twinkling stars in night sky */
.stars {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.star {
  position: absolute;
  color: #FFFEF0;
  font-size: 20px;
  animation: twinkleStar 3s ease-in-out infinite;
  filter: drop-shadow(0 0 6px rgba(255, 255, 240, 0.9));
}

.star-1 {
  top: 8%;
  left: 15%;
  animation-delay: 0s;
  font-size: 14px;
}

.star-2 {
  top: 12%;
  right: 25%;
  animation-delay: 0.5s;
  font-size: 18px;
}

.star-3 {
  top: 5%;
  left: 45%;
  animation-delay: 1s;
  font-size: 12px;
}

.star-4 {
  top: 15%;
  right: 10%;
  animation-delay: 1.5s;
  font-size: 16px;
}

.star-5 {
  top: 20%;
  left: 8%;
  animation-delay: 2s;
  font-size: 14px;
}

@keyframes ambientPulse {
  0%, 100% {
    opacity: 0.6;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.1);
  }
}

@keyframes twinkleStar {
  0%, 100% {
    opacity: 0.4;
    transform: scale(0.8);
    filter: drop-shadow(0 0 3px rgba(255, 255, 240, 0.5));
  }
  50% {
    opacity: 1;
    transform: scale(1);
    filter: drop-shadow(0 0 8px rgba(255, 255, 240, 1));
  }
}

/* Legacy twinkle animation */
@keyframes twinkle {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

.main-card {
  background: linear-gradient(
    135deg,
    rgba(26, 51, 85, 0.92) 0%,
    rgba(18, 38, 64, 0.88) 100%
  );
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(51, 130, 254, 0.2);
  border-radius: 32px;
  box-shadow:
    0 4px 40px rgba(0, 0, 0, 0.4),
    0 0 60px rgba(51, 130, 254, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  position: relative;
  overflow: hidden;
}

/* Blue gradient border */
.main-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 32px;
  padding: 1px;
  background: linear-gradient(
    135deg,
    rgba(77, 154, 255, 0.3) 0%,
    rgba(51, 130, 254, 0.4) 50%,
    rgba(77, 154, 255, 0.3) 100%
  );
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

/* Reward Toast Notification - Night Theme */
.reward-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(
    135deg,
    rgba(26, 51, 85, 0.95) 0%,
    rgba(18, 38, 64, 0.95) 100%
  );
  backdrop-filter: blur(20px);
  border: 1px solid rgba(51, 130, 254, 0.4);
  border-radius: 20px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(51, 130, 254, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  max-width: 420px;
  animation: toastGlow 2s ease-in-out infinite alternate;
}

@keyframes toastGlow {
  0% {
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.35),
      0 0 30px rgba(51, 130, 254, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  100% {
    box-shadow:
      0 8px 32px rgba(0, 0, 0, 0.45),
      0 0 50px rgba(51, 130, 254, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
}

.toast-close {
  position: absolute;
  top: 8px;
  right: 12px;
  background: none;
  border: none;
  color: rgba(232, 244, 255, 0.5);
  font-size: 20px;
  cursor: pointer;
  line-height: 1;
  padding: 4px;
  transition: color 0.2s;
}

.toast-close:hover {
  color: rgba(232, 244, 255, 0.9);
}

.toast-emoji {
  font-size: 48px;
  line-height: 1;
  animation: bounceEmoji 0.6s ease-out;
}

@keyframes bounceEmoji {
  0% {
    transform: scale(0) rotate(-20deg);
  }
  50% {
    transform: scale(1.3) rotate(10deg);
  }
  100% {
    transform: scale(1) rotate(0);
  }
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-size: 18px;
  font-weight: 700;
  color: #3382FE;
  margin-bottom: 6px;
  text-shadow: 0 0 10px rgba(51, 130, 254, 0.4);
}

.toast-hint {
  font-size: 14px;
  color: rgba(232, 244, 255, 0.9);
  line-height: 1.5;
}

/* Toast transition */
.toast-enter-active {
  animation: toastIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.toast-leave-active {
  animation: toastOut 0.3s ease-in forwards;
}

@keyframes toastIn {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(100px) scale(0.8);
  }
  100% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes toastOut {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(20px) scale(0.9);
  }
}
</style>
