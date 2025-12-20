import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import Particles from 'vue3-particles'
import router from './router'
import App from './App.vue'

// PrimeVue components
import AutoComplete from 'primevue/autocomplete'

// Import global styles
import 'primeicons/primeicons.css'
import './assets/styles/main.css'

// Error handling for debugging
window.onerror = (msg, url, line, col, error) => {
  console.error('Global error:', { msg, url, line, col, error })
  const errorDiv = document.createElement('div')
  errorDiv.style.cssText = 'position:fixed;top:0;left:0;right:0;background:red;color:white;padding:20px;z-index:99999;'
  errorDiv.textContent = `Error: ${msg} at ${url}:${line}:${col}`
  document.body.appendChild(errorDiv)
}

try {
  console.log('Creating Vue app...')
  const app = createApp(App)

  console.log('Setting up Pinia...')
  app.use(createPinia())

  console.log('Setting up Router...')
  app.use(router)

  console.log('Setting up PrimeVue...')
  app.use(PrimeVue, {
    theme: {
      preset: Aura,
      options: {
        darkModeSelector: '.dark-theme',
        cssLayer: {
          name: 'primevue',
          order: 'tailwind-base, primevue, tailwind-utilities'
        }
      }
    }
  })

  console.log('Setting up Particles...')
  app.use(Particles)

  console.log('Registering components...')
  app.component('AutoComplete', AutoComplete)

  console.log('Mounting app...')
  app.mount('#app')
  console.log('App mounted successfully!')
} catch (error) {
  console.error('Failed to initialize app:', error)
  const errorDiv = document.createElement('div')
  errorDiv.style.cssText = 'position:fixed;top:0;left:0;right:0;background:red;color:white;padding:20px;z-index:99999;'
  errorDiv.textContent = `Init Error: ${error}`
  document.body.appendChild(errorDiv)
}
