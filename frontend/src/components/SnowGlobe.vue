<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// ============== CONFIGURATION ==============
const CONFIG = {
  // Particles - increased for continuous snowfall
  maxParticles: 600,  // Active falling particles only (settled ones are removed)
  spawnRate: 12,      // Much higher - snow never stops
  maxSparkles: 100,   // Maximum sparkle particles

  // Physics
  gravity: 0.1,       // Slightly faster fall
  maxSpeed: 10,
  friction: 0.985,

  // Wind/Cursor interaction
  windRadius: 180,
  windStrength: 0.6,
  glowTriggerDistance: 80,  // Distance at which flakes start glowing near cursor
  sparkleChance: 0.06,      // Chance of spawning sparkle when flake is near cursor

  // Magnetism - attracts snow to cursor for faster accumulation
  magnetRadius: 250,        // Larger radius for magnetic attraction
  magnetStrength: 1.2,      // Strong pull towards cursor
  magnetFalloff: 2,         // Quadratic falloff (higher = sharper edge)
  cursorAccumulationBoost: 3.0,  // Multiplier for snow accumulation near cursor

  // Accumulation - faster and more visible
  gridCellSize: 4,              // Smaller cells = smoother snow surface
  maxAccumulationHeight: 300,   // Allow snow to pile up to ~1/3 of screen
  accumulationRate: 0.8,        // How much each flake adds (multiplied by radius)
  spreadRate: 0.3,              // How much spreads to neighbors

  // Snow compression (very slow settling of tall snow piles)
  compressionThreshold: 200,    // Only compress very tall piles
  compressionRate: 0.99999,     // Almost no compression (10x slower)

  // Decay rates
  glowDecay: 0.93,              // How fast glow fades
  wobbleDecay: 0.95,            // How fast wobble fades

  // Sparkle physics
  sparkleGravity: 0.1,
  sparkleFriction: 0.96,
  sparkleLifeDecay: 0.025,

  // Shake
  shakeIntensity: 18,
  shakeDuration: 600,

  // Object interaction
  objectClickRadius: 35,        // How close click must be to object
  objectWobbleRadius: 150,      // Radius for wobble effect on click
  snowClearRadius: 15,          // Grid cells cleared per click
  snowClearStrength: 30,        // How much snow is cleared
  explosionRadius: 200,         // Radius for pushing snowflakes on click

  // Hidden object awakening
  awakeningThresholdOffset: 10, // Offset for awakening calculation
  awakeningRange: 20,           // Range over which awakening progresses
  awakeningSpeedFactor: 0.03,   // How fast awakening progresses
  revealSpeedFactor: 0.08,      // How fast reveal progresses

  // Snowflake sizes
  sizes: [
    { radius: 1.5, weight: 0.6, chance: 0.25 },
    { radius: 2.5, weight: 0.8, chance: 0.35 },
    { radius: 4, weight: 1.0, chance: 0.30 },
    { radius: 6, weight: 1.2, chance: 0.10 },  // More big flakes
  ],
}

// ============== COLOR PALETTE ==============
// Extracted color values for consistency and easy theming
const ACCENT_BLUE = {
  main: '51,130,254',       // #3382FE - Main accent blue
  light: '77,154,255',      // #4D9AFF - Lighter blue
  soft: '122,180,255',      // #7AB4FF - Soft blue glow
  hsl: { h: 215, s: 99, l: 60 },  // HSL for sparkles
}

const CHRISTMAS_RED = {
  main: '196,30,58',        // Christmas red
  hsl: { h: 350, s: 75, l: 50 },
}

const FOREST_GREEN = {
  main: '34,139,34',        // Forest green
  hsl: { h: 120, s: 60, l: 35 },
}

const MAGIC_PURPLE = {
  main: '168,85,247',       // Purple for awakening glow
}

// Pre-computed colors (avoid string creation in render loop)
const COLORS = {
  snow: [
    'rgba(255,255,255,0.5)',
    'rgba(255,255,255,0.6)',
    'rgba(255,255,255,0.7)',
    'rgba(255,255,255,0.8)',
    'rgba(232,244,255,0.6)',
    'rgba(201,232,255,0.5)',
  ],
  glow: [
    `rgba(${ACCENT_BLUE.main},0.5)`,      // Blue accent
    `rgba(${CHRISTMAS_RED.main},0.4)`,    // Christmas red
    `rgba(${FOREST_GREEN.main},0.4)`,     // Forest green
  ],
  sparkle: [
    ACCENT_BLUE.hsl,
    CHRISTMAS_RED.hsl,
    FOREST_GREEN.hsl,
  ],
}

// ============== TYPES ==============
interface Snowflake {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  weight: number
  opacity: number
  glow: number
  colorIndex: number
  glowColorIndex: number  // Stable color index for glow effect (prevents flicker)
}

interface Sparkle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  radius: number
  colorIndex: number
}

interface HiddenObject {
  x: number
  y: number
  type: string
  emoji: string
  awakened: number  // 0-1: object materializes as snow reaches it
  revealed: number  // 0-1: visible above snow surface
  wobble: number
  clicked: boolean
  reward: string
  awakeningSparkles: number  // countdown for sparkle burst when awakening
}

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
const mouse = { x: -1000, y: -1000, prevX: 0, prevY: 0, vx: 0, vy: 0, active: false }

// Shake state
let isShaking = false
let shakeTime = 0
let shakeOffset = { x: 0, y: 0 }

// Object pools (pre-allocated)
const snowflakes: Snowflake[] = []
const sparkles: Sparkle[] = []
const hiddenObjects: HiddenObject[] = []

// Accumulation grid
let accumulationGrid: Float32Array
let gridCols = 0

// Stats
let score = 0
let highScore = 0

// ============== INITIALIZATION ==============
function initGrid(): void {
  gridCols = Math.ceil(width / CONFIG.gridCellSize)
  accumulationGrid = new Float32Array(gridCols)
}

// Rewards for hidden objects
const OBJECT_REWARDS = {
  gift: 'hyperrealism',  // Unlocks hyperrealism style hint
  star: 'space',         // Unlocks space style hint
  tree: 'pixel_art',     // Unlocks pixel art style hint
  snowman: 'movie',      // Unlocks movie style hint
}

function initHiddenObjects(): void {
  hiddenObjects.length = 0
  // Position objects at different heights - they awaken when snow reaches them
  // Lower awakening threshold = appears with less snow (easier to find)
  const objects = [
    { type: 'tree', emoji: '🎄', x: 0.12, awakeHeight: 25 },    // Awakens first
    { type: 'gift', emoji: '🎁', x: 0.38, awakeHeight: 45 },    // Needs more snow
    { type: 'snowman', emoji: '⛄', x: 0.62, awakeHeight: 35 }, // Medium
    { type: 'star', emoji: '⭐', x: 0.88, awakeHeight: 55 },    // Hardest to find
  ]

  for (const obj of objects) {
    hiddenObjects.push({
      x: width * obj.x,
      y: height - obj.awakeHeight - 20, // Position just above where they'll awaken
      type: obj.type,
      emoji: obj.emoji,
      awakened: 0,
      revealed: 0,
      wobble: 0,
      clicked: false,
      reward: OBJECT_REWARDS[obj.type as keyof typeof OBJECT_REWARDS] || '',
      awakeningSparkles: 0,
    })
  }
}

function createSnowflake(): Snowflake | null {
  if (snowflakes.length >= CONFIG.maxParticles) return null

  // Pick size based on probability
  let r = Math.random()
  let size = CONFIG.sizes[0]
  for (const s of CONFIG.sizes) {
    if (r < s.chance) {
      size = s
      break
    }
    r -= s.chance
  }

  return {
    x: Math.random() * width,
    y: -10 - Math.random() * 50,
    vx: (Math.random() - 0.5) * 0.5,
    vy: Math.random() * 0.5 + 0.3,
    radius: size.radius,
    weight: size.weight,
    opacity: 0.4 + Math.random() * 0.4,
    glow: 0,
    colorIndex: Math.floor(Math.random() * COLORS.snow.length),
    glowColorIndex: Math.floor(Math.random() * COLORS.glow.length),
  }
}

function createSparkle(x: number, y: number): void {
  if (sparkles.length >= CONFIG.maxSparkles) return

  const angle = Math.random() * Math.PI * 2
  const speed = 2 + Math.random() * 5
  sparkles.push({
    x,
    y,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed,
    life: 1,
    radius: 1 + Math.random() * 2.5,
    colorIndex: Math.floor(Math.random() * COLORS.sparkle.length),
  })
}

// ============== PHYSICS ==============
function updateSnowflakes(): void {
  // Ground is at height, snow accumulates UPWARD
  // accumulationGrid[i] = positive value = snow height from ground

  for (let i = snowflakes.length - 1; i >= 0; i--) {
    const flake = snowflakes[i]

    // Gravity
    flake.vy += CONFIG.gravity * flake.weight

    // Wind turbulence
    flake.vx += (Math.random() - 0.5) * 0.02

    // Cursor magnetism - attracts snowflakes to build drifts faster
    if (mouse.active) {
      const dx = mouse.x - flake.x
      const dy = mouse.y - flake.y
      const dist = Math.sqrt(dx * dx + dy * dy)

      // Magnetic attraction - pulls snowflakes towards cursor
      if (dist < CONFIG.magnetRadius && dist > 5) {
        // Stronger falloff for snappier magnetic feel
        const magnetForce = Math.pow(1 - dist / CONFIG.magnetRadius, CONFIG.magnetFalloff) * CONFIG.magnetStrength

        // Pull towards cursor (dx/dist normalizes direction)
        flake.vx += (dx / dist) * magnetForce
        flake.vy += (dy / dist) * magnetForce * 0.8  // Slightly less vertical pull

        // Also add some cursor velocity influence
        flake.vx += mouse.vx * magnetForce * 0.2
        flake.vy += mouse.vy * magnetForce * 0.2
      }

      // Glow and sparkles when close
      if (dist < CONFIG.glowTriggerDistance) {
        flake.glow = Math.min(1, flake.glow + 0.15)
        if (Math.random() < CONFIG.sparkleChance) {
          createSparkle(flake.x, flake.y)
        }
      }
    }

    // Shake impulse
    if (isShaking && shakeTime < 200) {
      flake.vx += (Math.random() - 0.5) * CONFIG.shakeIntensity * 0.1
      flake.vy -= Math.random() * CONFIG.shakeIntensity * 0.15
      flake.glow = 0.8
    }

    // Friction
    flake.vx *= CONFIG.friction
    flake.vy *= CONFIG.friction

    // Speed cap
    const speed = Math.sqrt(flake.vx * flake.vx + flake.vy * flake.vy)
    if (speed > CONFIG.maxSpeed) {
      const ratio = CONFIG.maxSpeed / speed
      flake.vx *= ratio
      flake.vy *= ratio
    }

    // Update position
    flake.x += flake.vx
    flake.y += flake.vy

    // Decay glow
    flake.glow *= CONFIG.glowDecay

    // Horizontal wrapping
    if (flake.x < -20) flake.x = width + 20
    if (flake.x > width + 20) flake.x = -20

    // Check accumulation - snow surface Y position
    const gridX = Math.floor(flake.x / CONFIG.gridCellSize)
    let shouldRemove = false

    if (gridX >= 0 && gridX < gridCols) {
      // Snow surface is at: height - accumulationGrid[gridX]
      const snowSurfaceY = height - accumulationGrid[gridX]

      if (flake.y >= snowSurfaceY) {
        // Add to accumulation (with height limit)
        if (accumulationGrid[gridX] < CONFIG.maxAccumulationHeight) {
          // Calculate cursor proximity boost
          let cursorBoost = 1.0
          if (mouse.active) {
            const cursorDist = Math.abs(flake.x - mouse.x)
            if (cursorDist < CONFIG.magnetRadius) {
              // Boost accumulation near cursor (builds drifts faster)
              cursorBoost = 1 + (1 - cursorDist / CONFIG.magnetRadius) * (CONFIG.cursorAccumulationBoost - 1)
            }
          }

          // Accumulation amount based on flake size + cursor boost
          const amount = flake.radius * CONFIG.accumulationRate * cursorBoost
          accumulationGrid[gridX] += amount

          // Cap at max height
          if (accumulationGrid[gridX] > CONFIG.maxAccumulationHeight) {
            accumulationGrid[gridX] = CONFIG.maxAccumulationHeight
          }

          // Spread to neighbors for smooth surface (also boosted near cursor)
          const spread = flake.radius * CONFIG.spreadRate * cursorBoost
          if (gridX > 0) {
            accumulationGrid[gridX - 1] += spread * 0.5
          }
          if (gridX < gridCols - 1) {
            accumulationGrid[gridX + 1] += spread * 0.5
          }
        }

        score++
        if (score > highScore) highScore = score

        // REMOVE the flake - this frees up space for new snowflakes!
        shouldRemove = true
      }
    }

    // Remove if settled or too far off screen
    if (shouldRemove || flake.y > height + 50 || flake.y < -200) {
      snowflakes.splice(i, 1)
    }
  }

  // Very slow natural settling of snow (gravity compression)
  for (let i = 0; i < gridCols; i++) {
    if (accumulationGrid[i] > CONFIG.compressionThreshold) {
      // Extremely slow settling - almost imperceptible
      accumulationGrid[i] *= CONFIG.compressionRate
    }
  }
}

function updateSparkles(): void {
  for (let i = sparkles.length - 1; i >= 0; i--) {
    const s = sparkles[i]
    s.x += s.vx
    s.y += s.vy
    s.vy += CONFIG.sparkleGravity
    s.vx *= CONFIG.sparkleFriction
    s.vy *= CONFIG.sparkleFriction
    s.life -= CONFIG.sparkleLifeDecay

    if (s.life <= 0) {
      sparkles.splice(i, 1)
    }
  }
}

function updateHiddenObjects(): void {
  for (const obj of hiddenObjects) {
    // Check snow coverage at object position
    const gridX = Math.floor(obj.x / CONFIG.gridCellSize)
    if (gridX >= 0 && gridX < gridCols) {
      const snowHeight = accumulationGrid[gridX]
      const snowSurfaceY = height - snowHeight
      const objectBottomY = obj.y + 20

      // AWAKENING: Object materializes when snow reaches its level
      // Object awakens when snow height reaches where it's positioned
      const awakeThreshold = height - obj.y - CONFIG.awakeningThresholdOffset
      if (snowHeight >= awakeThreshold && obj.awakened < 1) {
        // Snow has reached the object - start awakening!
        const targetAwakened = Math.min(1, (snowHeight - awakeThreshold) / CONFIG.awakeningRange)
        const prevAwakened = obj.awakened
        obj.awakened += (targetAwakened - obj.awakened) * CONFIG.awakeningSpeedFactor

        // Trigger sparkle burst when crossing 0.5 threshold
        if (prevAwakened < 0.5 && obj.awakened >= 0.5) {
          obj.awakeningSparkles = 30
          obj.wobble = 8
        }
      }

      // Spawning awakening sparkles
      if (obj.awakeningSparkles > 0) {
        obj.awakeningSparkles--
        if (Math.random() < 0.4) {
          const angle = Math.random() * Math.PI * 2
          const speed = 1 + Math.random() * 3
          sparkles.push({
            x: obj.x + (Math.random() - 0.5) * 30,
            y: obj.y + (Math.random() - 0.5) * 30,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed - 1,
            life: 1,
            radius: 2 + Math.random() * 3,
            colorIndex: Math.floor(Math.random() * 3),
          })
        }
      }

      // REVEALING: Only awakened objects can be revealed
      // Object is revealed when snow surface drops below it
      if (obj.awakened > 0.5) {
        let targetReveal = 0
        if (snowSurfaceY > objectBottomY) {
          targetReveal = 1
        } else if (snowSurfaceY > obj.y - 10) {
          targetReveal = (snowSurfaceY - (obj.y - 10)) / 30
        }
        obj.revealed += (targetReveal - obj.revealed) * CONFIG.revealSpeedFactor
      }

      // Wobble decay
      obj.wobble *= CONFIG.wobbleDecay
    }
  }
}

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

// ============== RENDERING ==============
function render(): void {
  if (!ctx) return

  ctx.save()
  ctx.translate(shakeOffset.x, shakeOffset.y)

  // Clear
  ctx.clearRect(-10, -10, width + 20, height + 20)

  // Draw cursor magnetic field - pulsing glow that attracts snow
  if (mouse.active) {
    const pulse = 0.8 + Math.sin(Date.now() / 200) * 0.2
    const gradient = ctx.createRadialGradient(
      mouse.x, mouse.y, 0,
      mouse.x, mouse.y, CONFIG.magnetRadius * pulse
    )
    // Festive gradient: blue center → red → green → transparent
    gradient.addColorStop(0, `rgba(${ACCENT_BLUE.main},0.2)`)
    gradient.addColorStop(0.3, `rgba(${CHRISTMAS_RED.main},0.1)`)
    gradient.addColorStop(0.6, `rgba(${FOREST_GREEN.main},0.05)`)
    gradient.addColorStop(1, 'rgba(0,0,0,0)')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(mouse.x, mouse.y, CONFIG.magnetRadius * pulse, 0, Math.PI * 2)
    ctx.fill()
  }

  // Draw hidden objects
  for (const obj of hiddenObjects) {
    // AWAKENING GLOW: Show magical glow under snow when object is awakening
    if (obj.awakened > 0.1 && obj.awakened < 1 && obj.revealed < 0.5) {
      ctx.save()
      const pulseIntensity = 0.5 + Math.sin(Date.now() / 300) * 0.3
      const glowRadius = 30 + obj.awakened * 20

      const gradient = ctx.createRadialGradient(
        obj.x, obj.y, 0,
        obj.x, obj.y, glowRadius
      )
      // Blue center fading to purple edge
      gradient.addColorStop(0, `rgba(${ACCENT_BLUE.main}, ${obj.awakened * pulseIntensity * 0.4})`)
      gradient.addColorStop(0.5, `rgba(${MAGIC_PURPLE.main}, ${obj.awakened * pulseIntensity * 0.2})`)
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(obj.x, obj.y, glowRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()
    }

    // REVEALED OBJECT: Draw emoji when visible above snow
    if (obj.revealed > 0.05 && obj.awakened > 0.5) {
      ctx.save()
      ctx.globalAlpha = Math.min(1, obj.revealed * 1.2)
      ctx.font = obj.clicked ? '48px serif' : '40px serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'

      // Wobble animation
      const wobbleAngle = Math.sin(Date.now() / 200) * obj.wobble * 0.1
      ctx.translate(obj.x, obj.y)
      ctx.rotate(wobbleAngle)

      // Glow effect - stronger when clicked
      if (obj.clicked) {
        ctx.shadowBlur = 30
        ctx.shadowColor = 'rgba(255,215,0,0.8)'
      } else if (obj.revealed > 0.7) {
        ctx.shadowBlur = 15
        ctx.shadowColor = 'rgba(168,85,247,0.5)'
      }

      ctx.fillText(obj.emoji, 0, 0)
      ctx.restore()
    }
  }

  // Draw accumulated snow - only where there's actual snow (> 0)
  // Find the minimum Y (highest snow point) for gradient
  let minSnowY = height
  for (let i = 0; i < gridCols; i++) {
    if (accumulationGrid[i] > 0.5) {
      const y = height - accumulationGrid[i]
      if (y < minSnowY) minSnowY = y
    }
  }

  // Only draw snow if there's any accumulation
  const hasSnow = accumulationGrid.some(v => v > 0.5)
  if (hasSnow) {
    ctx.fillStyle = 'rgba(255,255,255,0.9)'
    ctx.beginPath()
    ctx.moveTo(0, height + 10) // Start below screen

    // Draw snow surface
    for (let i = 0; i < gridCols; i++) {
      const x = i * CONFIG.gridCellSize
      const snowHeight = accumulationGrid[i]
      // Only draw if there's snow here
      const y = snowHeight > 0.5 ? height - snowHeight : height + 5
      ctx.lineTo(x, y)
    }

    ctx.lineTo(width, height + 10)
    ctx.closePath()
    ctx.fill()

    // Snow gradient overlay for depth
    const snowGrad = ctx.createLinearGradient(0, minSnowY - 20, 0, height)
    snowGrad.addColorStop(0, 'rgba(220,240,255,0.3)')
    snowGrad.addColorStop(0.5, 'rgba(240,248,255,0.6)')
    snowGrad.addColorStop(1, 'rgba(255,255,255,0.95)')
    ctx.fillStyle = snowGrad
    ctx.fill()
  }

  // Draw sparkles (on top of snow)
  for (const s of sparkles) {
    const color = COLORS.sparkle[s.colorIndex]
    const alpha = s.life * 0.8
    ctx.fillStyle = `hsla(${color.h},${color.s}%,${color.l}%,${alpha})`
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.radius * s.life, 0, Math.PI * 2)
    ctx.fill()
  }

  // Draw snowflakes (all are falling - settled ones are removed)
  for (const flake of snowflakes) {
    // Glow effect - use stable glowColorIndex to prevent flicker
    if (flake.glow > 0.1) {
      const glowColor = COLORS.glow[flake.glowColorIndex]
      ctx.fillStyle = glowColor.replace('0.6', String(flake.glow * 0.5))
      ctx.beginPath()
      ctx.arc(flake.x, flake.y, flake.radius * 2.5, 0, Math.PI * 2)
      ctx.fill()
    }

    // Main snowflake
    ctx.fillStyle = COLORS.snow[flake.colorIndex]
    ctx.beginPath()
    ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2)
    ctx.fill()
  }

  // Draw accumulated snow counter (subtle)
  ctx.fillStyle = 'rgba(255,255,255,0.3)'
  ctx.font = '12px monospace'
  ctx.textAlign = 'left'
  ctx.fillText(`❄ ${score}`, 10, 20)

  ctx.restore()
}

// ============== GAME LOOP ==============
function update(): void {
  // Spawn new snowflakes
  const spawnCount = isShaking ? CONFIG.spawnRate * 3 : CONFIG.spawnRate
  for (let i = 0; i < spawnCount; i++) {
    const flake = createSnowflake()
    if (flake) snowflakes.push(flake)
  }

  // Update cursor velocity
  mouse.vx = (mouse.x - mouse.prevX) * 0.5
  mouse.vy = (mouse.y - mouse.prevY) * 0.5
  mouse.prevX = mouse.x
  mouse.prevY = mouse.y

  updateSnowflakes()
  updateSparkles()
  updateHiddenObjects()
  updateShake()
}

function animate(): void {
  update()
  render()
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

  // Check if clicking on a revealed hidden object first
  // Object must be awakened AND revealed to be clickable
  for (const obj of hiddenObjects) {
    if (obj.awakened > 0.5 && obj.revealed > 0.6 && !obj.clicked) {
      const dist = Math.sqrt(
        Math.pow(obj.x - clickX, 2) + Math.pow(obj.y - clickY, 2)
      )
      if (dist < CONFIG.objectClickRadius) {
        // Object clicked!
        obj.clicked = true
        obj.wobble = 15

        // Big sparkle burst in blue
        for (let i = 0; i < 40; i++) {
          const angle = Math.random() * Math.PI * 2
          const speed = 3 + Math.random() * 8
          sparkles.push({
            x: obj.x,
            y: obj.y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            life: 1,
            radius: 2 + Math.random() * 4,
            colorIndex: Math.floor(Math.random() * 3),
          })
        }

        // Emit event for parent to handle reward
        emit('object-clicked', obj.type, obj.reward)
        return // Don't clear snow when clicking object
      }
    }
  }

  // Trigger shake
  isShaking = true
  shakeTime = 0

  // Burst sparkles at click point
  for (let i = 0; i < 25; i++) {
    createSparkle(clickX, clickY)
  }

  // Clear accumulated snow in area (reduce accumulation values)
  const gridX = Math.floor(clickX / CONFIG.gridCellSize)
  const clearRadius = CONFIG.snowClearRadius
  for (let dx = -clearRadius; dx <= clearRadius; dx++) {
    const i = gridX + dx
    if (i >= 0 && i < gridCols) {
      const dist = Math.abs(dx)
      const force = (1 - dist / clearRadius) * CONFIG.snowClearStrength
      accumulationGrid[i] -= force

      // Can't go below 0 (no snow)
      if (accumulationGrid[i] < 0) {
        accumulationGrid[i] = 0
      }
    }
  }

  // Blow nearby falling snowflakes away
  for (const flake of snowflakes) {
    const dx = flake.x - clickX
    const dy = flake.y - clickY
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < CONFIG.explosionRadius && dist > 0) {
      const force = (1 - dist / CONFIG.explosionRadius) * CONFIG.shakeIntensity
      flake.vx += (dx / dist) * force * 0.8
      flake.vy += (dy / dist) * force * 0.5 - Math.random() * force * 0.5
      flake.glow = 1
    }
  }

  // Wobble hidden objects near click
  for (const obj of hiddenObjects) {
    const dist = Math.sqrt(
      Math.pow(obj.x - clickX, 2) + Math.pow(obj.y - clickY, 2)
    )
    if (dist < CONFIG.objectWobbleRadius) {
      obj.wobble = (1 - dist / CONFIG.objectWobbleRadius) * 10
    }
  }
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
    handleClick({ clientX: e.touches[0].clientX, clientY: e.touches[0].clientY } as MouseEvent)
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
