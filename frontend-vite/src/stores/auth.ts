import { defineStore } from 'pinia'
import axios from 'axios'
import { ref, computed } from 'vue'


// Set default base URL for axios
// Ideally this should be in an env var
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('token'))
    const userRole = ref<string | null>(localStorage.getItem('role'))
    const username = ref<string | null>(localStorage.getItem('username'))
    const institutionId = ref<string | null>(localStorage.getItem('institution_id'))

    const isAuthenticated = computed(() => !!token.value)
    
    // Getter for role
    const getRole = computed(() => userRole.value)

    async function login(usernameInput: string, passwordInput: string) {
        try {
            const params = new URLSearchParams()
            params.append('grant_type', 'password')
            params.append('username', usernameInput)
            params.append('password', passwordInput)
            params.append('scope', '')
            params.append('client_id', 'string')
            params.append('client_secret', 'string')

            const response = await axios.post(`${API_URL}/api/auth/login`, params, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            })

            // Store data in state
            token.value = response.data.access_token
            userRole.value = response.data.role
            username.value = response.data.username
            institutionId.value = response.data.institution_id

            // Store data in localStorage
            if (token.value) localStorage.setItem('token', token.value)
            if (userRole.value) localStorage.setItem('role', userRole.value)
            if (username.value) localStorage.setItem('username', username.value)
            // handle institution_id possibly being null/undefined
            if (institutionId.value) {
                localStorage.setItem('institution_id', institutionId.value)
            } else {
                localStorage.removeItem('institution_id')
            }

            return { success: true }
        } catch (error: any) {
            console.error('Login failed', error)
            return {
                success: false,
                error: error.response?.data?.detail || 'Login failed'
            }
        }
    }

    function logout() {
        token.value = null
        userRole.value = null
        username.value = null
        institutionId.value = null
        
        localStorage.removeItem('token')
        localStorage.removeItem('role')
        localStorage.removeItem('username')
        localStorage.removeItem('institution_id')
    }

    return { 
        token, 
        userRole, 
        username, 
        institutionId, 
        isAuthenticated, 
        getRole, 
        login, 
        logout 
    }
})
