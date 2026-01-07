<script setup lang="ts">
import { ref } from 'vue'
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
import { RefreshCw, Info } from 'lucide-vue-next'
import { toast } from 'vue-sonner'

const formData = ref({
  fullName: '',
  email: '',
  phone: '',
  employeeId: '',
  role: '',
  institution: '',
  password: ''
})

const generatePassword = () => {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
  let password = ""
  for (let i = 0; i < 12; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  formData.value.password = password
}

const handleRegister = () => {
  // Mock registration
  console.log('Registering User:', formData.value)
  toast.success('User created successfully')
  
  // Reset form
  formData.value = {
    fullName: '',
    email: '',
    phone: '',
    employeeId: '',
    role: '',
    institution: '',
    password: ''
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
          <Label>Full Name</Label>
          <Input v-model="formData.fullName" placeholder="e.g. John Doe" class="bg-white" />
        </div>
        <div class="space-y-2">
          <Label>Email Address (Username)</Label>
          <Input v-model="formData.email" placeholder="e.g. john.doe@dcsa.app" class="bg-white" />
        </div>
        <div class="space-y-2">
          <Label>Phone Number</Label>
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
              <SelectItem value="client_admin">Client Admin</SelectItem>
              <SelectItem value="super_admin">Super Admin</SelectItem>
              <SelectItem value="staff">Staff</SelectItem>
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
              <SelectItem value="vhs">VHS</SelectItem>
              <SelectItem value="plai">PLAI</SelectItem>
              <SelectItem value="bmd_panjen">SD BMD Panjen</SelectItem>
              <SelectItem value="smp_bmd">SMP BMD</SelectItem>
              <SelectItem value="sma_bmd">SMA BMD</SelectItem>
              <SelectItem value="binus">Binus Univ</SelectItem>
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
          <p class="text-[11px] text-zinc-500">User will be forced to change this on first login.</p>
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
      <Button size="lg" class="bg-emerald-600 hover:bg-emerald-700 text-white min-w-[150px]" @click="handleRegister">
        Create User
      </Button>
    </div>
  </div>
</template>
