/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        christmas: {
          red: '#DC2626',
          'red-dark': '#991B1B',
          'red-glow': '#FF4444',
          green: '#16A34A',
          'green-dark': '#166534',
          'green-glow': '#22D955',
          gold: '#F59E0B',
          'gold-light': '#FCD34D',
          'gold-glow': '#FFD700',
        },
        winter: {
          'bg-primary': '#0A0E1A',
          'bg-secondary': '#141B2D',
          snow: '#F8FAFC',
        },
        // 2025 Aurora/Magic colors
        aurora: {
          purple: '#A855F7',
          'purple-dark': '#7C3AED',
          cyan: '#22D3EE',
          'cyan-dark': '#06B6D4',
          pink: '#EC4899',
          'pink-dark': '#DB2777',
          blue: '#3B82F6',
          'blue-dark': '#2563EB',
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
        'glow-red': '0 0 20px rgba(220, 38, 38, 0.5), 0 0 40px rgba(220, 38, 38, 0.3)',
        'glow-green': '0 0 20px rgba(22, 163, 74, 0.5), 0 0 40px rgba(22, 163, 74, 0.3)',
        'glow-gold': '0 0 20px rgba(245, 158, 11, 0.5), 0 0 40px rgba(245, 158, 11, 0.3)',
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
