/**
 * Snow Globe Canvas Renderer
 * Handles all drawing operations for the snow globe
 */

import {
  CONFIG,
  COLORS,
  ACCENT_BLUE,
  MAGIC_PURPLE,
  type Snowflake,
  type Sparkle,
  type HiddenObject,
  type MouseState,
} from './useSnowGlobeConfig'

interface RenderState {
  ctx: CanvasRenderingContext2D
  width: number
  height: number
  snowflakes: Snowflake[]
  sparkles: Sparkle[]
  hiddenObjects: HiddenObject[]
  accumulationGrid: Float32Array
  gridCols: number
  mouse: MouseState
  shakeOffset: { x: number; y: number }
  score: number
}

/**
 * Draws a cursor magnetic field with a silver glow based on the mouse state.
 */
function drawCursorField(state: RenderState): void {
  if (!state.mouse.active) return

  const pulse = 0.8 + Math.sin(Date.now() / 200) * 0.2
  const gradient = state.ctx.createRadialGradient(
    state.mouse.x, state.mouse.y, 0,
    state.mouse.x, state.mouse.y, CONFIG.magnetRadius * pulse
  )
  // Silver gradient: bright center → soft silver → transparent
  gradient.addColorStop(0, 'rgba(220,220,220,0.25)')
  gradient.addColorStop(0.3, 'rgba(192,192,192,0.15)')
  gradient.addColorStop(0.6, 'rgba(169,169,169,0.08)')
  gradient.addColorStop(1, 'rgba(0,0,0,0)')
  state.ctx.fillStyle = gradient
  state.ctx.beginPath()
  state.ctx.arc(state.mouse.x, state.mouse.y, CONFIG.magnetRadius * pulse, 0, Math.PI * 2)
  state.ctx.fill()
}

/**
 * Draws hidden objects with an awakening glow and revealed emoji.
 *
 * The function iterates through the hidden objects in the provided state. For each object, it checks if it should display an awakening glow based on its properties and draws a radial gradient. If the object is revealed, it adjusts the context settings and draws the emoji with potential wobble and shadow effects based on its state.
 *
 * @param state - The RenderState containing the context and hidden objects to be drawn.
 * @returns void
 */
function drawHiddenObjects(state: RenderState): void {
  for (const obj of state.hiddenObjects) {
    // AWAKENING GLOW
    if (obj.awakened > 0.1 && obj.awakened < 1 && obj.revealed < 0.5) {
      state.ctx.save()
      const pulseIntensity = 0.5 + Math.sin(Date.now() / 300) * 0.3
      const glowRadius = 30 + obj.awakened * 20

      const gradient = state.ctx.createRadialGradient(
        obj.x, obj.y, 0,
        obj.x, obj.y, glowRadius
      )
      gradient.addColorStop(0, `rgba(${ACCENT_BLUE.main}, ${obj.awakened * pulseIntensity * 0.4})`)
      gradient.addColorStop(0.5, `rgba(${MAGIC_PURPLE.main}, ${obj.awakened * pulseIntensity * 0.2})`)
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')

      state.ctx.fillStyle = gradient
      state.ctx.beginPath()
      state.ctx.arc(obj.x, obj.y, glowRadius, 0, Math.PI * 2)
      state.ctx.fill()
      state.ctx.restore()
    }

    // REVEALED OBJECT
    if (obj.revealed > 0.05 && obj.awakened > 0.5) {
      state.ctx.save()
      state.ctx.globalAlpha = Math.min(1, obj.revealed * 1.2)
      state.ctx.font = obj.clicked ? '48px serif' : '40px serif'
      state.ctx.textAlign = 'center'
      state.ctx.textBaseline = 'middle'

      const wobbleAngle = Math.sin(Date.now() / 200) * obj.wobble * 0.1
      state.ctx.translate(obj.x, obj.y)
      state.ctx.rotate(wobbleAngle)

      if (obj.clicked) {
        state.ctx.shadowBlur = 30
        state.ctx.shadowColor = 'rgba(255,215,0,0.8)'
      } else if (obj.revealed > 0.7) {
        state.ctx.shadowBlur = 15
        state.ctx.shadowColor = 'rgba(168,85,247,0.5)'
      }

      state.ctx.fillText(obj.emoji, 0, 0)
      state.ctx.restore()
    }
  }
}

/**
 * Draw accumulated snow drifts
 */
function drawAccumulatedSnow(state: RenderState): void {
  // Find the minimum Y (highest snow point) for gradient
  let minSnowY = state.height
  for (let i = 0; i < state.gridCols; i++) {
    if (state.accumulationGrid[i] > 0.5) {
      const y = state.height - state.accumulationGrid[i]
      if (y < minSnowY) minSnowY = y
    }
  }

  // Only draw snow if there's any accumulation
  const hasSnow = state.accumulationGrid.some(v => v > 0.5)
  if (!hasSnow) return

  state.ctx.fillStyle = 'rgba(255,255,255,0.9)'
  state.ctx.beginPath()
  state.ctx.moveTo(0, state.height + 10)

  for (let i = 0; i < state.gridCols; i++) {
    const x = i * CONFIG.gridCellSize
    const snowHeight = state.accumulationGrid[i]
    const y = snowHeight > 0.5 ? state.height - snowHeight : state.height + 5
    state.ctx.lineTo(x, y)
  }

  state.ctx.lineTo(state.width, state.height + 10)
  state.ctx.closePath()
  state.ctx.fill()

  // Snow gradient overlay for depth
  const snowGrad = state.ctx.createLinearGradient(0, minSnowY - 20, 0, state.height)
  snowGrad.addColorStop(0, 'rgba(220,240,255,0.3)')
  snowGrad.addColorStop(0.5, 'rgba(240,248,255,0.6)')
  snowGrad.addColorStop(1, 'rgba(255,255,255,0.95)')
  state.ctx.fillStyle = snowGrad
  state.ctx.fill()
}

/**
 * Draws sparkles on the canvas based on their properties.
 */
function drawSparkles(state: RenderState): void {
  for (const s of state.sparkles) {
    const colors = s.isSilver ? COLORS.silverSparkle : COLORS.sparkle
    const color = colors[s.colorIndex]
    const alpha = s.life * 0.8
    state.ctx.fillStyle = `hsla(${color.h},${color.s}%,${color.l}%,${alpha})`
    state.ctx.beginPath()
    state.ctx.arc(s.x, s.y, s.radius * s.life, 0, Math.PI * 2)
    state.ctx.fill()
  }
}

/**
 * Draws falling snowflakes on the canvas.
 */
function drawSnowflakes(state: RenderState): void {
  for (const flake of state.snowflakes) {
    // Glow effect
    if (flake.glow > 0.1) {
      const glowColor = COLORS.glow[flake.glowColorIndex]
      state.ctx.fillStyle = glowColor.replace('0.5)', `${flake.glow * 0.5})`)
      state.ctx.beginPath()
      state.ctx.arc(flake.x, flake.y, flake.radius * 2.5, 0, Math.PI * 2)
      state.ctx.fill()
    }

    // Main snowflake
    state.ctx.fillStyle = COLORS.snow[flake.colorIndex]
    state.ctx.beginPath()
    state.ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2)
    state.ctx.fill()
  }
}

/**
 * Draws the score counter on the canvas.
 */
function drawScore(state: RenderState): void {
  state.ctx.fillStyle = 'rgba(255,255,255,0.3)'
  state.ctx.font = '12px monospace'
  state.ctx.textAlign = 'left'
  state.ctx.fillText(`❄ ${state.score}`, 10, 20)
}

/**
 * Renders the entire scene by drawing various layers.
 */
export function render(state: RenderState): void {
  state.ctx.save()
  state.ctx.translate(state.shakeOffset.x, state.shakeOffset.y)

  // Clear
  state.ctx.clearRect(-10, -10, state.width + 20, state.height + 20)

  // Draw layers in order (back to front)
  drawCursorField(state)
  drawHiddenObjects(state)
  drawAccumulatedSnow(state)
  drawSparkles(state)
  drawSnowflakes(state)
  drawScore(state)

  state.ctx.restore()
}
