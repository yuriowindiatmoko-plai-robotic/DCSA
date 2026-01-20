import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import HomeAdminView from '../views/HomeAdminView.vue'
import HomeClientView from '../views/HomeClientView.vue'
import RatingFoodView from '../views/RatingFoodView.vue'
import FeedbackAnalysisView from '../views/FeedbackAnalysisView.vue'
import FoodAnalystView from '../views/FoodAnalystView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView, // Smart Router
            meta: { requiresAuth: true }
        },
        {
            path: '/home-admin',
            name: 'home-admin',
            component: HomeAdminView,
            meta: { requiresAuth: true, roles: ['SUPER_ADMIN', 'DK_ADMIN'] }
        },
        {
            path: '/home-client',
            name: 'home-client',
            component: HomeClientView,
            meta: { requiresAuth: true, roles: ['CLIENT_ADMIN'] }
        },
        {
            path: '/rating-food/:institutionId',
            name: 'rating-food',
            component: RatingFoodView,
            meta: { requiresAuth: false }
        },
        {
            path: '/feedback-analysis',
            name: 'feedback-analysis',
            component: FeedbackAnalysisView,
            meta: { requiresAuth: true, roles: ['SUPER_ADMIN', 'DK_ADMIN'] }
        },
        {
            path: '/food-analyst',
            name: 'food-analyst',
            component: FoodAnalystView,
            meta: { requiresAuth: true }
        },
        {
            path: '/login',
            name: 'login',
            component: LoginView
        }
    ]
})

// Navigation Guard
router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()
    
    // Check if the route requires authentication
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next('/login')
        return
    }

    // Role-based protection
    // Check if the route has specific role requirements
    if (to.meta.roles) {
        const requiredRoles = to.meta.roles as string[]
        const userRole = authStore.getRole
        
        if (!userRole || !requiredRoles.includes(userRole)) {
            // User doesn't have the necessary role
            // Redirect to a safe default or show unauthorized
            // For now, redirect to login or root which handles logic
            next('/') 
            return
        }
    }

    next()
})

export default router
