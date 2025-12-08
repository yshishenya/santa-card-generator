/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        christmas: {
          red: '#DC2626',
          'red-dark': '#991B1B',
          green: '#16A34A',
          'green-dark': '#166534',
          gold: '#F59E0B',
          'gold-light': '#FCD34D',
        },
        winter: {
          'bg-primary': '#0F172A',
          'bg-secondary': '#1E293B',
          snow: '#F8FAFC',
        }
      },
      animation: {
        'snow-fall': 'snowfall 10s linear infinite',
        'twinkle': 'twinkle 2s ease-in-out infinite',
      },
      keyframes: {
        snowfall: {
          '0%': { transform: 'translateY(-100vh)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        twinkle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        }
      }
    }
  },
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['winter', 'night'],
    darkTheme: 'night',
  }
}
