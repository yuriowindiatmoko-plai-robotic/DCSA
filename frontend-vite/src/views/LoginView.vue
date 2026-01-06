<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const router = useRouter()
const authStore = useAuthStore()



async function handleLogin() {
  isLoading.value = true
  errorMessage.value = ''
  
  const result = await authStore.login(username.value, password.value)
  
  if (result.success) {
    router.push('/')
  } else {
    errorMessage.value = result.error
  }
  
  isLoading.value = false
}
</script>

<template>
  <div class="w-full h-screen flex lg:grid lg:grid-cols-2">
    <!-- Left Side - Branding -->
    <div class="hidden lg:flex flex-col p-10 relative text-white bg-[#020817]">
      <!-- Content -->
      <div class="relative z-10">
        <div class="flex items-center gap-2">
           <img src="@/assets/dcsa-logo.svg" alt="DCSA Logo" class="h-8 w-auto" />
           <span class="font-bold text-xl tracking-wide">DCSA</span>
        </div>
      </div>
    </div>

    <!-- Right Side - Login Form -->
    <div class="flex items-center justify-center p-8 lg:p-12 w-full bg-white dark:bg-zinc-950">
      <div class="w-full max-w-[400px] space-y-6">
        <div class="flex flex-col space-y-2 text-center">
          <h1 class="text-3xl font-bold tracking-tight">Login</h1>
          <p class="text-sm text-gray-500">Welcome back! Please enter your details.</p>
        </div>



        <form @submit.prevent="handleLogin" class="space-y-4">
          <div class="space-y-2">
            <Label for="username">Username</Label>
            <Input id="username" v-model="username" type="text" placeholder="Enter your username" required />
          </div>
          
          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input id="password" v-model="password" type="password" placeholder="••••••••" required />
          </div>

          <div v-if="errorMessage" class="text-red-500 text-sm text-center">
            {{ errorMessage }}
          </div>

          <Button type="submit" class="w-full mt-4 bg-[#44bb2c] hover:bg-[#6FC276]/90 text-white" :disabled="isLoading">
            <template v-if="isLoading">
                Logging in...
            </template>
            <template v-else>
                Submit
            </template>
          </Button>
        </form>
      </div>
    </div>
  </div>
</template>
