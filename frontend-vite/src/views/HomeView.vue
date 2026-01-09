<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }

  const role = authStore.getRole
  
  if (role === 'SUPER_ADMIN' || role === 'DK_ADMIN') {
    router.replace('/home-admin')
  } else if (role === 'CLIENT_ADMIN') {
    router.replace('/home-client')
  } else {
    // Fallback if role is unknown or missing
    // For now redirecting to login or show an error
    console.warn('Unknown role:', role)
    router.replace('/login') 
  }
})
</script>

<template>
  <div class="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
    <div class="text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
      <h2 class="text-xl font-semibold text-gray-700 dark:text-gray-200">Redirecting...</h2>
      <p class="text-gray-500">Please wait while we route you to your dashboard.</p>
    </div>
  </div>
</template>
