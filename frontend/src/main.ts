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

const app = createApp(App)

// Setup Pinia store
app.use(createPinia())

// Setup Vue Router
app.use(router)

// Setup PrimeVue with Aura theme
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

// Setup vue3-particles plugin
app.use(Particles)

// Register PrimeVue components globally
app.component('AutoComplete', AutoComplete)

app.mount('#app')
