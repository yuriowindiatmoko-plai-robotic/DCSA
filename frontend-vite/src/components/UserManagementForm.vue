<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RefreshCw, Info, Loader2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

const API_URL = 'http://localhost:8000'

const formData = ref({
  username: '',
  email: '',
  phone: '',
  employeeId: '',
  role: '',
  institution: '',
  password: ''
})

const isSubmitting = ref(false)

const generatePassword = () => {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
  let password = ""
  for (let i = 0; i < 12; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  formData.value.password = password
}

const handleRegister = async () => {
  // Trim inputs
  const username = formData.value.username.trim()
  const email = formData.value.email.trim()
  const password = formData.value.password.trim()
  const role = formData.value.role
  const institution = formData.value.institution

  if (!username || !email || !password || !role || !institution) {
    toast.error('Please fill in all required fields')
    return
  }

  if (password.length < 6) {
    toast.error('Password must be at least 6 characters')
    return
  }

  isSubmitting.value = true
  try {
    const payload = {
      username,
      email,
      password,
      institution_name: institution,
      role
    }

    console.log('Sending Registration Payload:', payload)

    const response = await axios.post(`${API_URL}/api/auth/register`, payload)
    
    console.log('Registration Success:', response.data)
    toast.success('User created successfully')
    
    // Reset form
    formData.value = {
      username: '',
      email: '',
      phone: '',
      employeeId: '',
      role: '',
      institution: '',
      password: ''
    }
  } catch (error: any) {
    console.error('Registration failed:', error)
    
    let errorMsg = 'Registration failed'
    
    if (error.response?.status === 422) {
      const detail = error.response.data?.detail
      if (Array.isArray(detail)) {
        errorMsg = detail.map((d: any) => `${d.loc[d.loc.length - 1]}: ${d.msg}`).join(', ')
      } else if (typeof detail === 'string') {
        errorMsg = detail
      }
    } else {
      errorMsg = error.response?.data?.detail || 'An unexpected error occurred'
    }
    
    toast.error(errorMsg, {
      description: 'Check the console for more details.'
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-8 pb-10">
    <!-- Header -->
    <div class="space-y-1">
      <h2 class="text-2xl font-bold tracking-tight text-zinc-900">Register New User</h2>
      <p class="text-sm text-zinc-500">Create and provision new accounts. Admin use only.</p>
    </div>

    <!-- Personal Information -->
    <div class="space-y-6">
      <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Personal Information</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-2">
          <Label>Username</Label>
          <Input v-model="formData.username" placeholder="e.g. johndoe_admin" class="bg-white" />
        </div>
        <div class="space-y-2">
          <Label>Email Address</Label>
          <Input v-model="formData.email" placeholder="e.g. john.doe@dcsa.app" class="bg-white" />
        </div>
        <div class="space-y-2">
          <Label>Phone Number <span class="text-zinc-400 font-normal">(Optional)</span></Label>
          <Input v-model="formData.phone" placeholder="+62 812..." class="bg-white" />
        </div>
        <div class="space-y-2">
          <Label>Employee ID <span class="text-zinc-400 font-normal">(Optional)</span></Label>
          <Input v-model="formData.employeeId" placeholder="EMP-0000" class="bg-white" />
        </div>
      </div>
    </div>

    <!-- Access & Permissions -->
    <div class="space-y-6">
      <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Access & Permissions</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="space-y-2">
          <Label>Role Assignment</Label>
          <Select v-model="formData.role">
            <SelectTrigger class="bg-white">
              <SelectValue placeholder="Select a role..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="CLIENT_ADMIN">Client Admin</SelectItem>
              <SelectItem value="DK_ADMIN">DK Admin</SelectItem>
              <SelectItem value="SUPER_ADMIN">Super Admin</SelectItem>
            </SelectContent>
          </Select>
          <p class="text-[11px] text-zinc-500">Determines the user's permissions within the portal.</p>
        </div>
        <div class="space-y-2">
          <Label>Assign Institution</Label>
          <Select v-model="formData.institution">
            <SelectTrigger class="bg-white">
              <SelectValue placeholder="Select institution..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Dapur Kuliner BMD">Dapur Kuliner BMD</SelectItem>
              <SelectItem value="SD Budi Mulia Dua Panjen">SD BMD Panjen</SelectItem>
              <SelectItem value="SMP Budi Mulia Dua">SMP BMD</SelectItem>
              <SelectItem value="SMA Budi Mulia Dua">SMA BMD</SelectItem>
              <SelectItem value="PLAI BMD">PLAI BMD</SelectItem>
              <SelectItem value="VHS">VHS</SelectItem>
            </SelectContent>
          </Select>
          <p class="text-[11px] text-zinc-500">The primary branch or unit this user belongs to.</p>
        </div>
      </div>
    </div>

    <!-- Security -->
    <div class="space-y-6">
      <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-wider">Security</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        <div class="space-y-2">
          <Label>Password</Label>
          <div class="flex gap-2">
            <Input v-model="formData.password" placeholder="TempPass123!" class="bg-white font-mono" />
            <Button variant="outline" class="shrink-0 gap-2" @click="generatePassword">
              <RefreshCw class="h-3.5 w-3.5" />
              Generate
            </Button>
          </div>
          <p class="text-[11px]" :class="formData.password.length > 0 && formData.password.length < 6 ? 'text-red-500 font-bold' : 'text-zinc-500'">
            {{ formData.password.length > 0 && formData.password.length < 6 ? 'Password is too short (min 6 characters)' : 'User will be forced to change this on first login.' }}
          </p>
        </div>

        <div class="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3">
          <Info class="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
          <div class="space-y-1">
            <h4 class="text-sm font-bold text-blue-900">Admin Note</h4>
            <p class="text-xs text-blue-700 leading-relaxed">
              Creating a user manually bypasses the standard email verification flow. Please ensure the email address is correct.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="pt-6 border-t border-zinc-200 flex justify-end">
      <Button 
        size="lg" 
        class="bg-emerald-600 hover:bg-emerald-700 text-white min-w-[150px] gap-2" 
        :disabled="isSubmitting"
        @click="handleRegister"
      >
        <Loader2 v-if="isSubmitting" class="h-4 w-4 animate-spin" />
        {{ isSubmitting ? 'Creating...' : 'Create User' }}
      </Button>
    </div>
  </div>
</template>
