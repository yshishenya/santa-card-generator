<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCardStore } from '@/stores/card'
import { TEXT_STYLE_LABELS } from '@/types'
import GlassCard from './GlassCard.vue'

const cardStore = useCardStore()
const carouselRef = ref<HTMLElement | null>(null)
const currentSlide = ref(0)

const selectVariant = (index: number) => {
  cardStore.selectTextVariant(index)
}

const scrollToSlide = (index: number) => {
  if (!carouselRef.value) return
  const slideWidth = carouselRef.value.offsetWidth
  carouselRef.value.scrollTo({
    left: slideWidth * index,
    behavior: 'smooth'
  })
  currentSlide.value = index
}

const nextSlide = () => {
  const next = (currentSlide.value + 1) % cardStore.textVariants.length
  scrollToSlide(next)
}

const prevSlide = () => {
  const prev = (currentSlide.value - 1 + cardStore.textVariants.length) % cardStore.textVariants.length
  scrollToSlide(prev)
}

// Detect scroll position to update current slide indicator
const handleScroll = () => {
  if (!carouselRef.value) return
  const slideWidth = carouselRef.value.offsetWidth
  const scrollLeft = carouselRef.value.scrollLeft
  const newIndex = Math.round(scrollLeft / slideWidth)
  currentSlide.value = newIndex
}

const canGoPrev = computed(() => cardStore.textVariants.length > 1)
const canGoNext = computed(() => cardStore.textVariants.length > 1)
</script>

<template>
  <div class="space-y-4 relative">
    <!-- Pure CSS Carousel -->
    <div v-if="cardStore.textVariants.length > 0" class="carousel-container">
      <!-- Navigation Buttons -->
      <button
        v-if="canGoPrev"
        type="button"
        class="carousel-nav carousel-nav-prev"
        @click="prevSlide"
        aria-label="Previous slide"
      >
        <svg class="carousel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>

      <!-- Slides Container -->
      <div
        ref="carouselRef"
        class="carousel-viewport"
        @scroll="handleScroll"
      >
        <div
          v-for="(variant, index) in cardStore.textVariants"
          :key="variant.id"
          class="carousel-slide"
        >
          <div class="carousel-slide-content">
            <GlassCard
              padding="p-6"
              class="cursor-pointer transition-all card-inner"
              :class="{
                'ring-2 ring-christmas-green': cardStore.selectedTextIndex === index,
                'opacity-70 hover:opacity-100': cardStore.selectedTextIndex !== index
              }"
              @click="selectVariant(index)"
            >
              <div class="space-y-4">
                <!-- Style badge -->
                <div class="flex items-center justify-between">
                  <span class="badge badge-lg bg-christmas-green/20 text-christmas-green border-christmas-green/30">
                    <i class="pi pi-sparkles mr-1"></i>
                    {{ TEXT_STYLE_LABELS[variant.style] }}
                  </span>
                  <span class="text-winter-snow/60 text-sm">{{ index + 1 }} / {{ cardStore.textVariants.length }}</span>
                </div>

                <!-- Text content -->
                <div class="text-content-area">
                  <p class="text-winter-snow text-lg leading-relaxed whitespace-pre-wrap break-words">
                    {{ variant.content }}
                  </p>
                </div>

                <!-- Selection button -->
                <div class="flex justify-center pt-3 border-t border-white/10">
                  <button
                    type="button"
                    class="btn btn-sm px-6"
                    :class="cardStore.selectedTextIndex === index
                      ? 'btn-success'
                      : 'btn-ghost bg-white/5 hover:bg-white/10 text-winter-snow'"
                    @click.stop="selectVariant(index)"
                  >
                    <i v-if="cardStore.selectedTextIndex === index" class="pi pi-check mr-2"></i>
                    {{ cardStore.selectedTextIndex === index ? 'Выбрано' : 'Выбрать' }}
                  </button>
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>

      <!-- Next Button -->
      <button
        v-if="canGoNext"
        type="button"
        class="carousel-nav carousel-nav-next"
        @click="nextSlide"
        aria-label="Next slide"
      >
        <svg class="carousel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </button>

      <!-- Pagination Dots -->
      <div v-if="cardStore.textVariants.length > 1" class="carousel-pagination">
        <button
          v-for="(_, index) in cardStore.textVariants"
          :key="index"
          type="button"
          class="carousel-dot"
          :class="{ 'carousel-dot-active': currentSlide === index }"
          @click="scrollToSlide(index)"
          :aria-label="`Go to slide ${index + 1}`"
        ></button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-8 text-winter-snow/60">
      <i class="pi pi-info-circle text-2xl mb-2"></i>
      <p>Нет вариантов текста</p>
    </div>

    <!-- Loading overlay for regeneration -->
    <div
      v-if="cardStore.isRegeneratingText"
      class="absolute inset-0 bg-black/50 flex items-center justify-center rounded-xl z-10"
    >
      <div class="text-center">
        <span class="loading loading-spinner loading-lg text-christmas-gold"></span>
        <p class="text-winter-snow mt-2">Генерируем новые варианты...</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== CAROUSEL CONTAINER ===== */
.carousel-container {
  position: relative;
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

/* ===== CAROUSEL VIEWPORT (Scroll Container) ===== */
.carousel-viewport {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
  gap: 0; /* No gap between slides */
}

/* Hide scrollbar for Chrome, Safari, and Opera */
.carousel-viewport::-webkit-scrollbar {
  display: none;
}

/* ===== INDIVIDUAL SLIDE ===== */
.carousel-slide {
  flex: 0 0 100%; /* Each slide takes exactly 100% of viewport width */
  min-width: 100%;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

/* ===== SLIDE CONTENT WRAPPER ===== */
.carousel-slide-content {
  width: 100%;
  max-width: 600px;
  padding: 0 12px; /* Breathing room, doesn't affect slide width calculation */
  box-sizing: border-box;
}

/* ===== CARD STYLING ===== */
.card-inner {
  width: 100%;
}

/* ===== TEXT CONTENT AREA ===== */
.text-content-area {
  min-height: 180px;
  max-height: 350px;
  overflow-y: auto;
  padding-right: 4px;
}

/* Custom scrollbar for text area */
.text-content-area::-webkit-scrollbar {
  width: 6px;
}

.text-content-area::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.text-content-area::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.text-content-area::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* ===== NAVIGATION BUTTONS ===== */
.carousel-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 0;
}

.carousel-nav:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-50%) scale(1.05);
}

.carousel-nav:active {
  transform: translateY(-50%) scale(0.95);
}

.carousel-nav-prev {
  left: -22px;
}

.carousel-nav-next {
  right: -22px;
}

.carousel-icon {
  width: 24px;
  height: 24px;
}

/* ===== PAGINATION DOTS ===== */
.carousel-pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding-top: 16px;
}

.carousel-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  border: none;
  cursor: pointer;
  padding: 0;
  transition: all 0.2s ease;
}

.carousel-dot:hover {
  background: rgba(255, 255, 255, 0.5);
}

.carousel-dot-active {
  background: #FFD700;
  transform: scale(1.2);
}

/* ===== RESPONSIVE ADJUSTMENTS ===== */
@media (max-width: 768px) {
  .carousel-nav-prev {
    left: 4px;
  }

  .carousel-nav-next {
    right: 4px;
  }

  .carousel-slide-content {
    padding: 0 8px;
  }
}
</style>
