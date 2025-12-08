import type { ISourceOptions } from 'tsparticles-engine'

/**
 * Configuration for snow particle effect
 */
export function useParticlesConfig(): ISourceOptions {
  return {
    background: {
      color: {
        value: 'transparent'
      }
    },
    fpsLimit: 60,
    particles: {
      number: {
        value: 100,
        density: {
          enable: true,
          area: 800
        }
      },
      color: {
        value: '#ffffff'
      },
      shape: {
        type: 'circle'
      },
      opacity: {
        value: { min: 0.3, max: 0.8 },
        animation: {
          enable: true,
          speed: 1,
          minimumValue: 0.3
        }
      },
      size: {
        value: { min: 1, max: 5 }
      },
      move: {
        enable: true,
        speed: 2,
        direction: 'bottom',
        random: false,
        straight: false,
        outModes: {
          default: 'out',
          bottom: 'out',
          left: 'out',
          right: 'out',
          top: 'out'
        }
      },
      wobble: {
        enable: true,
        distance: 10,
        speed: {
          min: 5,
          max: 15
        }
      }
    },
    interactivity: {
      detectsOn: 'canvas',
      events: {
        onHover: {
          enable: false
        },
        onClick: {
          enable: false
        },
        resize: true
      }
    },
    detectRetina: true
  }
}
