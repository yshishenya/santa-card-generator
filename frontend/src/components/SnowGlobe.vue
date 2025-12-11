<script setup lang="ts">
/**
 * Snow Globe Component
 * Interactive canvas-based snow effect with hidden objects Easter egg
 *
 * Architecture:
 * - Config & Types: useSnowGlobeConfig.ts
 * - Physics: useSnowPhysics.ts
 * - Rendering: useSnowRenderer.ts
 */
import { ref, onMounted, onUnmounted } from 'vue'
import {
  CONFIG,
  OBJECT_REWARDS,
  HIDDEN_OBJECT_DEFS,
  type Snowflake,
  type Sparkle,
  type HiddenObject,
  type MouseState,
} from '@/composables/useSnowGlobeConfig'
import {
  createSnowflake,
  createSilverSparkleBurst,
  updateSnowflakes,
  updateSparkles,
  updateHiddenObjects,
} from '@/composables/useSnowPhysics'
import { render } from '@/composables/useSnowRenderer'

// Emit for communicating with parent
const emit = defineEmits<{
  'object-clicked': [type: string, reward: string]
}>()

// ============== STATE ==============
const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animationId = 0
let width = 0
let height = 0

// Mouse state
const mouse: MouseState = {
  x: -1000, y: -1000,
  prevX: 0, prevY: 0,
  vx: 0, vy: 0,
  active: false
}

// Shake state
let isShaking = false
let shakeTime = 0
const shakeOffset = { x: 0, y: 0 }

// Object pools
const snowflakes: Snowflake[] = []
const sparkles: Sparkle[] = []
const hiddenObjects: HiddenObject[] = []

// Accumulation grid
let accumulationGrid: Float32Array = new Float32Array(0)
let gridCols = 0

// Score
let score = 0

// ============== INITIALIZATION ==============
function initGrid(): void {
  gridCols = Math.ceil(width / CONFIG.gridCellSize)
  accumulationGrid = new Float32Array(gridCols)
}

function initHiddenObjects(): void {
  hiddenObjects.length = 0
  for (const obj of HIDDEN_OBJECT_DEFS) {
    hiddenObjects.push({
      x: width * obj.x,
      y: height - obj.awakeHeight - 20,
      type: obj.type,
      emoji: obj.emoji,
      awakened: 0,
      revealed: 0,
      wobble: 0,
      clicked: false,
      reward: OBJECT_REWARDS[obj.type] || '',
      awakeningSparkles: 0,
    })
  }
}

// ============== SHAKE ==============
function updateShake(): void {
  if (!isShaking) return

  shakeTime += 16

  if (shakeTime < CONFIG.shakeDuration) {
    const intensity = (1 - shakeTime / CONFIG.shakeDuration) * 6
    shakeOffset.x = (Math.random() - 0.5) * intensity
    shakeOffset.y = (Math.random() - 0.5) * intensity
  } else {
    isShaking = false
    shakeOffset.x = 0
    shakeOffset.y = 0
  }
}

// ============== GAME LOOP ==============
function update(): void {
  // Spawn new snowflakes
  const spawnCount = isShaking ? CONFIG.spawnRate * 3 : CONFIG.spawnRate
  const physicsState = {
    snowflakes,
    sparkles,
    hiddenObjects,
    accumulationGrid,
    gridCols,
    width,
    height,
    mouse,
    isShaking,
    shakeTime,
  }

  for (let i = 0; i < spawnCount; i++) {
    const flake = createSnowflake(physicsState)
    if (flake) snowflakes.push(flake)
  }

  // Update cursor velocity
  mouse.vx = (mouse.x - mouse.prevX) * 0.5
  mouse.vy = (mouse.y - mouse.prevY) * 0.5
  mouse.prevX = mouse.x
  mouse.prevY = mouse.y

  // Update physics
  score += updateSnowflakes(physicsState)
  updateSparkles(sparkles)
  updateHiddenObjects(hiddenObjects, accumulationGrid, gridCols, height, sparkles)
  updateShake()
}

function animate(): void {
  update()

  if (ctx) {
    render({
      ctx,
      width,
      height,
      snowflakes,
      sparkles,
      hiddenObjects,
      accumulationGrid,
      gridCols,
      mouse,
      shakeOffset,
      score,
    })
  }

  animationId = requestAnimationFrame(animate)
}

// ============== EVENT HANDLERS ==============
function handleResize(): void {
  if (!canvasRef.value) return
  width = window.innerWidth
  height = window.innerHeight
  canvasRef.value.width = width
  canvasRef.value.height = height
  initGrid()
  initHiddenObjects()
}

function handleMouseMove(e: MouseEvent): void {
  mouse.x = e.clientX
  mouse.y = e.clientY
  mouse.active = true
}

function handleMouseLeave(): void {
  mouse.active = false
}

function handleClick(e: MouseEvent): void {
  const clickX = e.clientX
  const clickY = e.clientY

  // Check if clicking on a revealed hidden object
  for (const obj of hiddenObjects) {
    if (obj.awakened > 0.5 && obj.revealed > 0.6 && !obj.clicked) {
      const dist = Math.sqrt(
        Math.pow(obj.x - clickX, 2) + Math.pow(obj.y - clickY, 2)
      )
      if (dist < CONFIG.objectClickRadius) {
        obj.clicked = true
        obj.wobble = 15

        // Silver sparkle burst for object click
        createSilverSparkleBurst(sparkles, obj.x, obj.y)

        // Emit event for parent to handle reward
        emit('object-clicked', obj.type, obj.reward)
        return
      }
    }
  }
  // No click effects on empty space
}

function handleTouchMove(e: TouchEvent): void {
  if (e.touches.length > 0) {
    mouse.x = e.touches[0].clientX
    mouse.y = e.touches[0].clientY
    mouse.active = true
  }
}

function handleTouchEnd(): void {
  mouse.active = false
}

function handleTouchStart(e: TouchEvent): void {
  if (e.touches.length > 0) {
    const touch = e.touches[0]
    handleClick({ clientX: touch.clientX, clientY: touch.clientY } as MouseEvent)
  }
}

// ============== LIFECYCLE ==============
onMounted(() => {
  if (!canvasRef.value) return
  ctx = canvasRef.value.getContext('2d')
  if (!ctx) return

  handleResize()
  animate()

  window.addEventListener('resize', handleResize)
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseleave', handleMouseLeave)
  window.addEventListener('click', handleClick)
  window.addEventListener('touchmove', handleTouchMove, { passive: true })
  window.addEventListener('touchend', handleTouchEnd)
  window.addEventListener('touchstart', handleTouchStart, { passive: true })
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseleave', handleMouseLeave)
  window.removeEventListener('click', handleClick)
  window.removeEventListener('touchmove', handleTouchMove)
  window.removeEventListener('touchend', handleTouchEnd)
  window.removeEventListener('touchstart', handleTouchStart)
})
</script>

<template>
  <canvas ref="canvasRef" class="fixed inset-0 z-0 pointer-events-auto" />
</template>
