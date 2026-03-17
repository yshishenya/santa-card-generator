<template>
  <div class="min-h-screen bg-platform relative overflow-hidden">
    <!-- Ambient glow orbs -->
    <div class="ambient-orbs">
      <div class="ambient-orb orb-bottom-left"></div>
      <div class="ambient-orb orb-bottom-right"></div>
      <div class="ambient-orb orb-mid-left"></div>
      <div class="ambient-orb orb-top-right"></div>
    </div>

    <!-- Main content -->
    <div class="relative z-10 container mx-auto px-4 py-8">
      <div class="max-w-5xl mx-auto">
        <div class="main-card p-8 mb-8">
          <RouterView />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Premium platform studio background */
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
  background: radial-gradient(circle, rgba(79, 70, 229, 0.24) 0%, rgba(55, 48, 163, 0.1) 50%, transparent 70%);
  bottom: 10%;
  left: 5%;
  animation-delay: 0s;
}

.orb-bottom-right {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.22) 0%, rgba(30, 64, 175, 0.1) 50%, transparent 70%);
  bottom: 20%;
  right: 8%;
  animation-delay: -3s;
}

.orb-mid-left {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.17) 0%, transparent 70%);
  top: 30%;
  left: 15%;
  animation-delay: -5s;
}

.orb-top-right {
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, transparent 70%);
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
  background: linear-gradient(
    135deg,
    rgba(20, 32, 58, 0.95) 0%,
    rgba(16, 26, 48, 0.9) 100%
  );
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 32px;
  box-shadow:
    0 4px 40px rgba(0, 0, 0, 0.4),
    0 0 70px rgba(99, 102, 241, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  position: relative;
  overflow: hidden;
}

.main-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 32px;
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
</style>
