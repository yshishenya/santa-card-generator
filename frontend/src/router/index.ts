import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/success',
      name: 'success',
      // Lazy loaded for better performance
      component: () => import('../views/SuccessView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard for authentication
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  // Check if route requires authentication
  if (to.meta.requiresAuth !== false && authStore.needsAuth) {
    // Redirect to login
    next({ name: 'login' })
  } else if (to.name === 'login' && !authStore.needsAuth) {
    // Already authenticated, redirect to home
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
