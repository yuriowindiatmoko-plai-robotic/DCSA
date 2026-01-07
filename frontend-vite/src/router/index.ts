import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import HomeAdminView from '../views/HomeAdminView.vue'
import HomeClientView from '../views/HomeClientView.vue'
import RatingFoodView from '../views/RatingFoodView.vue'
import { useAuthStore } from '../stores/auth'
const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeAdminView,
            meta: { requiresAuth: true }
        },
        {
            path: '/home-client',
            name: 'home-client',
            component: HomeClientView,
            meta: { requiresAuth: true }
        },
        {
            path: '/rating-food/:institutionId',
            name: 'rating-food',
            component: RatingFoodView,
            meta: { requiresAuth: false }
        },
        {
            path: '/login',
            name: 'login',
            component: LoginView
        },
        {
            path: '/home-admin',
            name: 'home-admin',
            component: HomeAdminView,
            meta: { requiresAuth: true }
        }
    ]
})

// Navigation Guard
router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next('/login')
    } else {
        next()
    }
})

export default router
