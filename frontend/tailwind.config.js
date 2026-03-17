/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Professional 4.0 platform palette
        platform: {
          accent: '#6366F1',
          'accent-light': '#818CF8',
          'accent-dark': '#4338CA',
          'accent-glow': '#A5B4FC',
          primary: '#0EA5E9',
          'primary-light': '#38BDF8',
          'primary-dark': '#0284C7',
          'primary-glow': '#7DD3FC',
          secondary: '#1D4ED8',
          'secondary-light': '#60A5FA',
          'secondary-dark': '#1E40AF',
          'secondary-glow': '#93C5FD',
          'light-text': '#F8FAFC',
          'bg-primary': '#060C1A',
          'bg-secondary': '#0B1222',
          'bg-card': '#131B33',
          line: '#243152',
          'text-primary': '#E2E8F0',
          'text-secondary': '#B8C3DD',
          'text-muted': '#94A3B8',
        },
        // Blue-gray glow accents for surfaces
        bluelight: {
          primary: '#3B82F6',
          'primary-light': '#60A5FA',
          secondary: '#6366F1',
          'secondary-light': '#818CF8',
          deep: '#1D4ED8',
          soft: '#A5B4FC',
        },
        // Legacy warmlight alias (deprecated - use 'bluelight' instead)
        warmlight: {
          orange: '#3B82F6',
          'orange-light': '#60A5FA',
          yellow: '#6366F1',
          'yellow-light': '#818CF8',
          amber: '#1D4ED8',
          'amber-glow': '#A5B4FC',
        },
        // Neutral accent colors
        magic: {
          purple: '#8B5CF6',
          'purple-light': '#A78BFA',
          cyan: '#0EA5E9',
          'cyan-light': '#38BDF8',
          pink: '#64748B',
          'pink-light': '#94A3B8',
          blue: '#6366F1',
          'blue-light': '#818CF8',
        },
        // Legacy aurora support
        aurora: {
          purple: '#8B5CF6',
          'purple-dark': '#7C3AED',
          cyan: '#0EA5E9',
          'cyan-dark': '#0284C7',
          pink: '#64748B',
          'pink-dark': '#334155',
          blue: '#6366F1',
          'blue-dark': '#4338CA',
        }
      },
      animation: {
        'drift-fall': 'driftfall 10s linear infinite',
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
        driftfall: {
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
        'aurora-gradient': 'linear-gradient(135deg, #1E293B 0%, #334155 25%, #334155 50%, #475569 75%, #4F46E5 100%)',
        'magic-gradient': 'linear-gradient(135deg, #6366F1 0%, #0EA5E9 50%, #14B8A6 100%)',
        'platform-gradient': 'linear-gradient(135deg, #0EA5E9 0%, #6366F1 50%, #1D4ED8 100%)',
      },
      boxShadow: {
        'glow-red': '0 0 20px rgba(14, 165, 233, 0.35), 0 0 40px rgba(14, 165, 233, 0.2)',
        'glow-green': '0 0 20px rgba(56, 189, 248, 0.35), 0 0 40px rgba(56, 189, 248, 0.2)',
        // Blue accent glow (legacy name: glow-gold)
        'glow-gold': '0 0 20px rgba(99, 102, 241, 0.45), 0 0 40px rgba(99, 102, 241, 0.3)',
        'glow-accent': '0 0 20px rgba(99, 102, 241, 0.45), 0 0 40px rgba(99, 102, 241, 0.3)',
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.45), 0 0 40px rgba(139, 92, 246, 0.3)',
        'glow-cyan': '0 0 20px rgba(14, 165, 233, 0.45), 0 0 40px rgba(14, 165, 233, 0.3)',
        'glow-aurora': '0 0 30px rgba(99, 102, 241, 0.4), 0 0 60px rgba(14, 165, 233, 0.3), 0 0 90px rgba(139, 92, 246, 0.2)',
      },
    }
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['night'],
    darkTheme: 'night',
  }
}
