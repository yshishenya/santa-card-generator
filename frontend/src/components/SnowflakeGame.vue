<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let animationId: number = 0

// Mouse state
const mouse = { x: -1000, y: -1000, active: false }

// Performance: reduced particle count, simpler shapes
const SNOWFLAKE_COUNT = 50
const ATTRACTION_RADIUS = 250
const ATTRACTION_STRENGTH = 0.8  // Much stronger!
const MAX_SPEED = 12
const FRICTION = 0.96

// Click explosion settings
const EXPLOSION_FORCE = 15
const CLICK_SPARKLE_COUNT = 20

// Snowflake interface (simplified)
interface Snowflake {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  opacity: number
  glow: number
}

// Sparkle for effects
interface Sparkle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  radius: number
  hue: number
}

// Pools
const snowflakes: Snowflake[] = []
const sparkles: Sparkle[] = []

// Create snowflake
function createSnowflake(w: number, h: number, randomPos = true): Snowflake {
  return {
    x: randomPos ? Math.random() * w : Math.random() * w,
    y: randomPos ? Math.random() * h : -10,
    vx: (Math.random() - 0.5) * 0.3,
    vy: Math.random() * 0.5 + 0.3,
    radius: 2 + Math.random() * 4,
    opacity: 0.4 + Math.random() * 0.5,
    glow: 0
  }
}

// Create sparkle at position
function createSparkle(x: number, y: number, hue: number): Sparkle {
  const angle = Math.random() * Math.PI * 2
  const speed = 2 + Math.random() * 6
  return {
    x,
    y,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    life: 1,
    radius: 1 + Math.random() * 3,
    hue
  }
}

// Handle click - explosion effect
function handleClick(e: MouseEvent): void {
  const x = e.clientX
  const y = e.clientY

  // Push all nearby snowflakes away
  for (const flake of snowflakes) {
    const dx = flake.x - x
    const dy = flake.y - y
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < ATTRACTION_RADIUS * 1.5 && dist > 0) {
      const force = (1 - dist / (ATTRACTION_RADIUS * 1.5)) * EXPLOSION_FORCE
      flake.vx += (dx / dist) * force
      flake.vy += (dy / dist) * force
      flake.glow = 1
    }
  }

  // Create sparkle burst
  for (let i = 0; i < CLICK_SPARKLE_COUNT; i++) {
    const hue = Math.random() > 0.5 ? 270 : 185 // purple or cyan
    sparkles.push(createSparkle(x, y, hue))
  }
}

// Update physics
function update(w: number, h: number): void {
  // Update snowflakes
  for (const flake of snowflakes) {
    // Gentle gravity
    flake.vy += 0.02

    // Mouse attraction (STRONG)
    if (mouse.active) {
      const dx = mouse.x - flake.x
      const dy = mouse.y - flake.y
      const distSq = dx * dx + dy * dy
      const dist = Math.sqrt(distSq)

      if (dist < ATTRACTION_RADIUS && dist > 5) {
        // Quadratic falloff for snappier feel
        const force = Math.pow(1 - dist / ATTRACTION_RADIUS, 2) * ATTRACTION_STRENGTH
        flake.vx += (dx / dist) * force
        flake.vy += (dy / dist) * force

        // Glow when close
        if (dist < 80) {
          flake.glow = Math.min(1, flake.glow + 0.15)
          // Occasional sparkle
          if (Math.random() < 0.08) {
            sparkles.push(createSparkle(flake.x, flake.y, Math.random() > 0.5 ? 270 : 185))
          }
        }
      }
    }

    // Decay glow
    flake.glow *= 0.92

    // Apply friction
    flake.vx *= FRICTION
    flake.vy *= FRICTION

    // Cap speed
    const speed = Math.sqrt(flake.vx * flake.vx + flake.vy * flake.vy)
    if (speed > MAX_SPEED) {
      flake.vx = (flake.vx / speed) * MAX_SPEED
      flake.vy = (flake.vy / speed) * MAX_SPEED
    }

    // Update position
    flake.x += flake.vx
    flake.y += flake.vy

    // Wrap around
    if (flake.x < -20) flake.x = w + 20
    if (flake.x > w + 20) flake.x = -20
    if (flake.y > h + 20) {
      flake.y = -20
      flake.x = Math.random() * w
    }
    if (flake.y < -30) flake.y = h + 20
  }

  // Update sparkles
  for (let i = sparkles.length - 1; i >= 0; i--) {
    const s = sparkles[i]
    s.x += s.vx
    s.y += s.vy
    s.vx *= 0.94
    s.vy *= 0.94
    s.life -= 0.04

    if (s.life <= 0) {
      sparkles.splice(i, 1)
    }
  }
}

// Render - optimized
function render(): void {
  if (!ctx || !canvasRef.value) return
  const canvas = canvasRef.value

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // Draw attraction field (subtle)
  if (mouse.active) {
    const gradient = ctx.createRadialGradient(
      mouse.x, mouse.y, 0,
      mouse.x, mouse.y, ATTRACTION_RADIUS
    )
    gradient.addColorStop(0, 'rgba(168, 85, 247, 0.15)')
    gradient.addColorStop(0.4, 'rgba(34, 211, 238, 0.08)')
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(mouse.x, mouse.y, ATTRACTION_RADIUS, 0, Math.PI * 2)
    ctx.fill()
  }

  // Draw sparkles (simple circles)
  for (const s of sparkles) {
    const alpha = s.life * 0.8
    ctx.fillStyle = `hsla(${s.hue}, 80%, 70%, ${alpha})`
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.radius * s.life, 0, Math.PI * 2)
    ctx.fill()
  }

  // Draw snowflakes (optimized - simple circles with glow)
  for (const flake of snowflakes) {
    const alpha = flake.opacity + flake.glow * 0.3

    // Glow effect only when active
    if (flake.glow > 0.1) {
      ctx.fillStyle = `rgba(168, 85, 247, ${flake.glow * 0.4})`
      ctx.beginPath()
      ctx.arc(flake.x, flake.y, flake.radius * 2.5, 0, Math.PI * 2)
      ctx.fill()
    }

    // Main snowflake (simple gradient circle)
    const grad = ctx.createRadialGradient(
      flake.x, flake.y, 0,
      flake.x, flake.y, flake.radius
    )
    grad.addColorStop(0, `rgba(255, 255, 255, ${alpha})`)
    grad.addColorStop(0.6, `rgba(200, 230, 255, ${alpha * 0.7})`)
    grad.addColorStop(1, `rgba(150, 200, 255, 0)`)

    ctx.fillStyle = grad
    ctx.beginPath()
    ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2)
    ctx.fill()
  }
}

// Animation loop
function animate(): void {
  if (!canvasRef.value) return
  update(canvasRef.value.width, canvasRef.value.height)
  render()
  animationId = requestAnimationFrame(animate)
}

// Resize handler
function handleResize(): void {
  if (!canvasRef.value) return
  canvasRef.value.width = window.innerWidth
  canvasRef.value.height = window.innerHeight
}

// Mouse handlers
function handleMouseMove(e: MouseEvent): void {
  mouse.x = e.clientX
  mouse.y = e.clientY
  mouse.active = true
}

function handleMouseLeave(): void {
  mouse.active = false
}

// Touch handlers
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
    handleClick({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY } as MouseEvent)
  }
}

// Init
onMounted(() => {
  if (!canvasRef.value) return
  ctx = canvasRef.value.getContext('2d')
  if (!ctx) return

  handleResize()

  // Create snowflakes
  for (let i = 0; i < SNOWFLAKE_COUNT; i++) {
    snowflakes.push(createSnowflake(canvasRef.value.width, canvasRef.value.height))
  }

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
  <canvas ref="canvasRef" class="fixed inset-0 z-0" />
</template>
