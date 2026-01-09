import type { ISourceOptions } from 'tsparticles-engine'

/**
 * Configures particle effects for a snow animation.
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
        value: 150,
        density: {
          enable: true,
          area: 800
        }
      },
      color: {
        value: ['#ffffff', '#e0f7ff', '#c9e8ff']
      },
      shape: {
        type: 'circle'
      },
      opacity: {
        value: { min: 0.2, max: 0.9 },
        animation: {
          enable: true,
          speed: 0.8,
          minimumValue: 0.2,
          sync: false
        }
      },
      size: {
        value: { min: 1, max: 6 },
        animation: {
          enable: true,
          speed: 2,
          minimumValue: 1,
          sync: false
        }
      },
      move: {
        enable: true,
        speed: { min: 0.2, max: 1.2 },
        direction: 'bottom',
        random: true,
        straight: false,
        outModes: {
          default: 'out',
          bottom: 'out',
          left: 'out',
          right: 'out',
          top: 'out'
        },
        drift: {
          min: -0.3,
          max: 0.3
        }
      },
      wobble: {
        enable: true,
        distance: 15,
        speed: {
          min: 3,
          max: 10
        }
      },
      rotate: {
        value: { min: 0, max: 360 },
        animation: {
          enable: true,
          speed: 5,
          sync: false
        }
      },
      tilt: {
        enable: true,
        value: { min: 0, max: 20 },
        animation: {
          enable: true,
          speed: 5
        }
      },
      twinkle: {
        particles: {
          enable: true,
          frequency: 0.03,
          opacity: 1,
          color: {
            value: '#C0C0C0'
          }
        }
      },
      shadow: {
        enable: true,
        color: '#E8E8E8',
        blur: 8,
        offset: {
          x: 0,
          y: 0
        }
      }
    },
    interactivity: {
      detectsOn: 'window',
      events: {
        onHover: {
          enable: true,
          mode: 'repulse',
          parallax: {
            enable: true,
            force: 20,
            smooth: 30
          }
        },
        onClick: {
          enable: false,
          mode: 'push'
        },
        resize: true
      },
      modes: {
        repulse: {
          distance: 80,
          duration: 0.4,
          speed: 0.5
        },
        push: {
          quantity: 6
        }
      }
    },
    detectRetina: true,
    smooth: true
  }
}
