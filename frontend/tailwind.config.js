/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Magical Winter Night palette
        christmas: {
          red: '#E25555',        // Warm festive red
          'red-light': '#FF7B7B',
          'red-dark': '#C44545',
          'red-glow': '#FF9999',
          label: '#F87171',      // Form label color (coral red)
          green: '#4A9F4A',       // Pine green
          'green-light': '#6BBF6B',
          'green-dark': '#3A7F3A',
          'green-glow': '#7FCF7F',
          // Primary accent color (blue) - used for highlights, buttons, focus states
          accent: '#3382FE',           // Main accent blue
          'accent-light': '#5B9BFE',   // Lighter variant for hover
          'accent-dark': '#1A6DE0',    // Darker variant for active/pressed
          'accent-glow': '#7AB4FF',    // Glow/shadow color
          // Legacy alias for backward compatibility (deprecated - use 'accent' instead)
          gold: '#3382FE',
          'gold-light': '#5B9BFE',
          'gold-dark': '#1A6DE0',
          'gold-glow': '#7AB4FF',
        },
        // Night sky background colors
        winter: {
          'bg-primary': '#0B1929',     // Deep night sky
          'bg-secondary': '#122640',   // Slightly lighter blue
          'bg-card': '#1A3355',        // Card background
          'frost': '#2A4A6F',          // Frost/lighter accent
          snow: '#E8F4FF',             // Snow white with blue tint
          'text-primary': '#F0F8FF',   // Main text - almost white
          'text-secondary': '#B8D4F0', // Secondary text - soft blue
          'text-muted': '#7BA3CC',     // Muted text
        },
        // Blue glow accents for background effects
        bluelight: {
          primary: '#4D9AFF',          // Main blue glow
          'primary-light': '#7AB4FF',  // Lighter glow
          secondary: '#3382FE',        // Secondary blue
          'secondary-light': '#5B9BFE',
          deep: '#2170E8',             // Deep blue accent
          soft: '#99C8FF',             // Soft blue for subtle effects
        },
        // Legacy warmlight alias (deprecated - use 'bluelight' instead)
        warmlight: {
          orange: '#4D9AFF',
          'orange-light': '#7AB4FF',
          yellow: '#3382FE',
          'yellow-light': '#5B9BFE',
          amber: '#2170E8',
          'amber-glow': '#99C8FF',
        },
        // Magical accent colors
        magic: {
          purple: '#9D7BFF',      // Soft violet
          'purple-light': '#B8A0FF',
          cyan: '#5CC8E8',        // Ice blue
          'cyan-light': '#8EDDFF',
          pink: '#FF8FAB',        // Rose
          'pink-light': '#FFB8C8',
          blue: '#6BA3FF',        // Sky blue
          'blue-light': '#99C2FF',
        },
        // Legacy aurora support
        aurora: {
          purple: '#9D7BFF',
          'purple-dark': '#7B5CE0',
          cyan: '#5CC8E8',
          'cyan-dark': '#4AACC8',
          pink: '#FF8FAB',
          'pink-dark': '#E07090',
          blue: '#6BA3FF',
          'blue-dark': '#5090E0',
        }
      },
      animation: {
        'snow-fall': 'snowfall 10s linear infinite',
        'twinkle': 'twinkle 2s ease-in-out infinite',
        'aurora': 'aurora 15s ease-in-out infinite',
        'aurora-fast': 'aurora 8s ease-in-out infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'sparkle': 'sparkle 1.5s ease-in-out infinite',
        'gradient-x': 'gradientX 3s ease infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        snowfall: {
          '0%': { transform: 'translateY(-100vh)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        twinkle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        },
        aurora: {
          '0%, 100%': {
            backgroundPosition: '0% 50%',
            filter: 'hue-rotate(0deg)',
          },
          '50%': {
            backgroundPosition: '100% 50%',
            filter: 'hue-rotate(30deg)',
          },
        },
        glowPulse: {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(168, 85, 247, 0.4), 0 0 40px rgba(34, 211, 238, 0.2)',
          },
          '50%': {
            boxShadow: '0 0 30px rgba(168, 85, 247, 0.6), 0 0 60px rgba(34, 211, 238, 0.4)',
          },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        sparkle: {
          '0%, 100%': { opacity: '0', transform: 'scale(0) rotate(0deg)' },
          '50%': { opacity: '1', transform: 'scale(1) rotate(180deg)' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'aurora-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%)',
        'magic-gradient': 'linear-gradient(135deg, #A855F7 0%, #22D3EE 50%, #EC4899 100%)',
        'christmas-gradient': 'linear-gradient(135deg, #DC2626 0%, #16A34A 50%, #F59E0B 100%)',
      },
      boxShadow: {
        'glow-red': '0 0 20px rgba(226, 85, 85, 0.5), 0 0 40px rgba(226, 85, 85, 0.3)',
        'glow-green': '0 0 20px rgba(74, 159, 74, 0.5), 0 0 40px rgba(74, 159, 74, 0.3)',
        // Blue accent glow (legacy name: glow-gold)
        'glow-gold': '0 0 20px rgba(51, 130, 254, 0.5), 0 0 40px rgba(51, 130, 254, 0.3)',
        'glow-accent': '0 0 20px rgba(51, 130, 254, 0.5), 0 0 40px rgba(51, 130, 254, 0.3)',
        'glow-purple': '0 0 20px rgba(168, 85, 247, 0.5), 0 0 40px rgba(168, 85, 247, 0.3)',
        'glow-cyan': '0 0 20px rgba(34, 211, 238, 0.5), 0 0 40px rgba(34, 211, 238, 0.3)',
        'glow-aurora': '0 0 30px rgba(168, 85, 247, 0.4), 0 0 60px rgba(34, 211, 238, 0.3), 0 0 90px rgba(236, 72, 153, 0.2)',
      },
    }
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['winter', 'night'],
    darkTheme: 'night',
  }
}
