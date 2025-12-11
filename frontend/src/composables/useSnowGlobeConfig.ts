/**
 * Snow Globe Configuration and Types
 * Extracted from SnowGlobe.vue for maintainability
 */

// ============== CONFIGURATION ==============
export const CONFIG = {
  // Particles - increased for continuous snowfall
  maxParticles: 600,  // Active falling particles only (settled ones are removed)
  spawnRate: 12,      // Much higher - snow never stops
  maxSparkles: 100,   // Maximum sparkle particles

  // Physics
  gravity: 0.04,      // Slower, gentler fall
  maxSpeed: 6,
  friction: 0.99,

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

  // Accumulation - softer, more rounded drifts
  gridCellSize: 6,              // Larger cells for smoother, softer surface
  maxAccumulationHeight: 300,   // Allow snow to pile up to ~1/3 of screen
  accumulationRate: 0.6,        // How much each flake adds (multiplied by radius)
  spreadRate: 0.5,              // More spread = softer, rounder drifts

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
  ] as { radius: number; weight: number; chance: number }[],
}

// ============== COLOR PALETTE ==============
// Extracted color values for consistency and easy theming

export const ACCENT_BLUE = {
  main: '51,130,254',       // #3382FE - Main accent blue
  light: '77,154,255',      // #4D9AFF - Lighter blue
  soft: '122,180,255',      // #7AB4FF - Soft blue glow
  hsl: { h: 215, s: 99, l: 60 },  // HSL for sparkles
}

export const CHRISTMAS_RED = {
  main: '196,30,58',        // Christmas red
  hsl: { h: 350, s: 75, l: 50 },
}

export const FOREST_GREEN = {
  main: '34,139,34',        // Forest green
  hsl: { h: 120, s: 60, l: 35 },
}

export const MAGIC_PURPLE = {
  main: '168,85,247',       // Purple for awakening glow
}

// Silver colors for cursor and sparkle effects
export const SILVER = {
  bright: '220,220,220',    // #DCDCDC - Bright silver
  medium: '192,192,192',    // #C0C0C0 - Medium silver
  soft: '169,169,169',      // #A9A9A9 - Soft silver
  hsl: { h: 0, s: 0, l: 75 },  // HSL for silver sparkles
}

// Pre-computed colors (avoid string creation in render loop)
export const COLORS = {
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
  // Silver sparkles for object clicks
  silverSparkle: [
    SILVER.hsl,
    { h: 0, s: 0, l: 80 },   // Lighter silver
    { h: 0, s: 0, l: 70 },   // Darker silver
  ],
}

// ============== TYPES ==============
export interface Snowflake {
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

export interface Sparkle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  radius: number
  colorIndex: number
  isSilver?: boolean  // Flag for silver sparkles
}

export interface HiddenObject {
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

export interface MouseState {
  x: number
  y: number
  prevX: number
  prevY: number
  vx: number
  vy: number
  active: boolean
}

// Rewards for hidden objects
export const OBJECT_REWARDS: Record<string, string> = {
  gift: 'hyperrealism',  // Unlocks hyperrealism style hint
  star: 'space',         // Unlocks space style hint
  tree: 'pixel_art',     // Unlocks pixel art style hint
  snowman: 'movie',      // Unlocks movie style hint
}

// Hidden object definitions
export const HIDDEN_OBJECT_DEFS = [
  { type: 'tree', emoji: '🎄', x: 0.12, awakeHeight: 25 },    // Awakens first
  { type: 'gift', emoji: '🎁', x: 0.38, awakeHeight: 45 },    // Needs more snow
  { type: 'snowman', emoji: '⛄', x: 0.62, awakeHeight: 35 }, // Medium
  { type: 'star', emoji: '⭐', x: 0.88, awakeHeight: 55 },    // Hardest to find
]
