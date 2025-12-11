/**
 * Snow Globe Physics Engine
 * Handles snowflake movement, accumulation, and sparkle physics
 */

import {
  CONFIG,
  COLORS,
  type Snowflake,
  type Sparkle,
  type HiddenObject,
  type MouseState,
} from './useSnowGlobeConfig'

interface PhysicsState {
  snowflakes: Snowflake[]
  sparkles: Sparkle[]
  hiddenObjects: HiddenObject[]
  accumulationGrid: Float32Array
  gridCols: number
  width: number
  height: number
  mouse: MouseState
  isShaking: boolean
  shakeTime: number
}

/**
 * Create a new snowflake with random properties
 */
export function createSnowflake(state: PhysicsState): Snowflake | null {
  if (state.snowflakes.length >= CONFIG.maxParticles) return null

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
    x: Math.random() * state.width,
    y: -10 - Math.random() * 50,
    vx: (Math.random() - 0.5) * 0.3,
    vy: Math.random() * 0.3 + 0.15,
    radius: size.radius,
    weight: size.weight,
    opacity: 0.4 + Math.random() * 0.4,
    glow: 0,
    colorIndex: Math.floor(Math.random() * COLORS.snow.length),
    glowColorIndex: Math.floor(Math.random() * COLORS.glow.length),
  }
}

/**
 * Creates a sparkle at the specified position.
 */
export function createSparkle(
  sparkles: Sparkle[],
  x: number,
  y: number,
  isSilver: boolean = false
): void {
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
    colorIndex: Math.floor(Math.random() * (isSilver ? COLORS.silverSparkle.length : COLORS.sparkle.length)),
    isSilver,
  })
}

/**
 * Creates a burst of silver sparkles at the specified coordinates.
 */
export function createSilverSparkleBurst(
  sparkles: Sparkle[],
  x: number,
  y: number,
  count: number = 40
): void {
  for (let i = 0; i < count; i++) {
    const angle = Math.random() * Math.PI * 2
    const speed = 3 + Math.random() * 8
    sparkles.push({
      x,
      y,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: 1,
      radius: 2 + Math.random() * 4,
      colorIndex: Math.floor(Math.random() * COLORS.silverSparkle.length),
      isSilver: true,
    })
  }
}

/**
 * Update all snowflakes - physics, accumulation, removal.
 *
 * This function iterates through each snowflake in the state, applying physics such as gravity and wind turbulence, and handling interactions with the mouse for magnetism and glow effects. It also manages the accumulation of snowflakes in the grid, ensuring that they are removed when necessary and updating their positions accordingly. Finally, it applies a natural settling effect to the accumulation grid.
 *
 * @param state - The current physics state containing snowflakes and their properties.
 * @returns The number of snowflakes that have settled.
 */
export function updateSnowflakes(state: PhysicsState): number {
  let settledCount = 0

  for (let i = state.snowflakes.length - 1; i >= 0; i--) {
    const flake = state.snowflakes[i]

    // Gravity
    flake.vy += CONFIG.gravity * flake.weight

    // Wind turbulence
    flake.vx += (Math.random() - 0.5) * 0.02

    // Cursor magnetism - attracts snowflakes to build drifts faster
    if (state.mouse.active) {
      const dx = state.mouse.x - flake.x
      const dy = state.mouse.y - flake.y
      const dist = Math.sqrt(dx * dx + dy * dy)

      // Magnetic attraction - pulls snowflakes towards cursor
      if (dist < CONFIG.magnetRadius && dist > 5) {
        const magnetForce = Math.pow(1 - dist / CONFIG.magnetRadius, CONFIG.magnetFalloff) * CONFIG.magnetStrength
        flake.vx += (dx / dist) * magnetForce
        flake.vy += (dy / dist) * magnetForce * 0.8
        flake.vx += state.mouse.vx * magnetForce * 0.2
        flake.vy += state.mouse.vy * magnetForce * 0.2
      }

      // Glow and sparkles when close
      if (dist < CONFIG.glowTriggerDistance) {
        flake.glow = Math.min(1, flake.glow + 0.15)
        if (Math.random() < CONFIG.sparkleChance) {
          createSparkle(state.sparkles, flake.x, flake.y)
        }
      }
    }

    // Shake impulse
    if (state.isShaking && state.shakeTime < 200) {
      flake.vx += (Math.random() - 0.5) * CONFIG.shakeIntensity * 0.1
      flake.vy -= Math.random() * CONFIG.shakeIntensity * 0.15
      flake.glow = 0.8
    }

    // Friction and speed cap
    flake.vx *= CONFIG.friction
    flake.vy *= CONFIG.friction

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
    if (flake.x < -20) flake.x = state.width + 20
    if (flake.x > state.width + 20) flake.x = -20

    // Check accumulation
    const gridX = Math.floor(flake.x / CONFIG.gridCellSize)
    let shouldRemove = false

    if (gridX >= 0 && gridX < state.gridCols) {
      const snowSurfaceY = state.height - state.accumulationGrid[gridX]

      if (flake.y >= snowSurfaceY) {
        if (state.accumulationGrid[gridX] < CONFIG.maxAccumulationHeight) {
          let cursorBoost = 1.0
          if (state.mouse.active) {
            const cursorDist = Math.abs(flake.x - state.mouse.x)
            if (cursorDist < CONFIG.magnetRadius) {
              cursorBoost = 1 + (1 - cursorDist / CONFIG.magnetRadius) * (CONFIG.cursorAccumulationBoost - 1)
            }
          }

          const amount = flake.radius * CONFIG.accumulationRate * cursorBoost
          state.accumulationGrid[gridX] += amount

          if (state.accumulationGrid[gridX] > CONFIG.maxAccumulationHeight) {
            state.accumulationGrid[gridX] = CONFIG.maxAccumulationHeight
          }

          const spread = flake.radius * CONFIG.spreadRate * cursorBoost
          if (gridX > 0) {
            state.accumulationGrid[gridX - 1] += spread * 0.5
          }
          if (gridX < state.gridCols - 1) {
            state.accumulationGrid[gridX + 1] += spread * 0.5
          }
        }

        settledCount++
        shouldRemove = true
      }
    }

    if (shouldRemove || flake.y > state.height + 50 || flake.y < -200) {
      state.snowflakes.splice(i, 1)
    }
  }

  // Very slow natural settling
  for (let i = 0; i < state.gridCols; i++) {
    if (state.accumulationGrid[i] > CONFIG.compressionThreshold) {
      state.accumulationGrid[i] *= CONFIG.compressionRate
    }
  }

  return settledCount
}

/**
 * Update the position and state of all sparkles.
 */
export function updateSparkles(sparkles: Sparkle[]): void {
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

/**
 * Update hidden objects - awakening and revealing
 */
export function updateHiddenObjects(
  hiddenObjects: HiddenObject[],
  accumulationGrid: Float32Array,
  gridCols: number,
  height: number,
  sparkles: Sparkle[]
): void {
  for (const obj of hiddenObjects) {
    const gridX = Math.floor(obj.x / CONFIG.gridCellSize)
    if (gridX >= 0 && gridX < gridCols) {
      const snowHeight = accumulationGrid[gridX]
      const snowSurfaceY = height - snowHeight
      const objectBottomY = obj.y + 20

      // AWAKENING
      const awakeThreshold = height - obj.y - CONFIG.awakeningThresholdOffset
      if (snowHeight >= awakeThreshold && obj.awakened < 1) {
        const targetAwakened = Math.min(1, (snowHeight - awakeThreshold) / CONFIG.awakeningRange)
        const prevAwakened = obj.awakened
        obj.awakened += (targetAwakened - obj.awakened) * CONFIG.awakeningSpeedFactor

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

      // REVEALING
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
