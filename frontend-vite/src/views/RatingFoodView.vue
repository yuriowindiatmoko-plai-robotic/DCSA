<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Star, Loader2, Building2, Calendar, Send, AlertCircle } from 'lucide-vue-next'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { toast } from 'vue-sonner'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const route = useRoute()
const institutionId = route.params.institutionId as string

// Types
interface MenuItem {
  menu: string
  total_qty: number
  rating?: number
}

interface MenuDetails {
  heavy_meal?: MenuItem[]
  snack?: MenuItem[]
  beverages?: MenuItem[]
}

interface OrderData {
  order_id: string
  institution_id: string
  institution_name: string
  order_date: string
  menu_details: MenuDetails
}

// State
const isLoading = ref(true)
const isSubmitting = ref(false)
const error = ref<string | null>(null)
const orderData = ref<OrderData | null>(null)

// Form State
const isAnonymous = ref(false)
const form = ref({
  name: '',
  userType: 'STAFF',
  mealTime: 'Makan Siang',
  spiceLevel: '',
  comment: ''
})



// Hover State for Stars
const hoverState = ref<Record<string, number>>({})

// Flatten menu items with ratings
const menuItems = computed(() => {
  if (!orderData.value?.menu_details) return []

  const items: Array<{ category: string; menu: string; rating: number; key: string }> = []
  const details = orderData.value.menu_details

  // Process heavy_meal
  if (details.heavy_meal) {
    details.heavy_meal.forEach((item) => {
      items.push({
        category: 'Heavy Meal',
        menu: item.menu,
        rating: item.rating || 0,
        key: `heavy_meal_${item.menu}`
      })
    })
  }

  // Process snack
  if (details.snack) {
    details.snack.forEach((item) => {
      items.push({
        category: 'Snack',
        menu: item.menu,
        rating: item.rating || 0,
        key: `snack_${item.menu}`
      })
    })
  }

  // Process beverages
  if (details.beverages) {
    details.beverages.forEach((item) => {
      items.push({
        category: 'Beverages',
        menu: item.menu,
        rating: item.rating || 0,
        key: `beverages_${item.menu}`
      })
    })
  }

  return items
})

// Format date for display
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const day = date.getDate()
  const monthNames = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
  ]
  const month = monthNames[date.getMonth()]
  const year = date.getFullYear()
  return `${day} ${month} ${year}`
}

// Star rating functions
const setHover = (key: string, star: number) => {
  hoverState.value[key] = star
}

const clearHover = (key: string) => {
  hoverState.value[key] = 0
}

const setRating = (key: string, rating: number) => {
  const item = menuItems.value.find(i => i.key === key)
  if (item) {
    item.rating = rating
    // Update the original menu_details
    updateMenuDetailsRating(item.category, item.menu, rating)
  }
}

const updateMenuDetailsRating = (category: string, menuName: string, rating: number) => {
  if (!orderData.value?.menu_details) return

  const categoryKey = category.toLowerCase().replace(' ', '_') as keyof MenuDetails
  const items = orderData.value.menu_details[categoryKey]
  if (items) {
    const item = items.find(i => i.menu === menuName)
    if (item) {
      item.rating = rating
    }
  }
}

// Validation
const isValid = computed(() => {
  // At least one menu item must be rated
  return menuItems.value.some(item => item.rating > 0)
})

// Fetch order data
const fetchOrderData = async () => {
  try {
    isLoading.value = true
    error.value = null

    const response = await axios.get(`${API_URL}/api/rating-food/${institutionId}`)

    orderData.value = {
      order_id: response.data.order.order_id,
      institution_id: response.data.order.institution_id,
      institution_name: response.data.order.institution_name,
      order_date: response.data.order.order_date,
      menu_details: response.data.order.menu_details || {}
    }

    // Set default meal time from response if available
    if (response.data.meal_time) {
      form.value.mealTime = response.data.meal_time
    }
  } catch (err: any) {
    console.error('Failed to fetch order data:', err)
    if (err.response?.status === 404) {
      error.value = 'No order found for today. Please check back later.'
    } else {
      error.value = 'Failed to load order data. Please try again.'
    }
    toast.error('Error', {
      description: error.value
    })
  } finally {
    isLoading.value = false
  }
}

// Submit feedback
const submitFeedback = async () => {
  if (!isValid.value || !orderData.value) return

  isSubmitting.value = true

  try {
    // Build menu_ratings object
    const menuRatings: Record<string, Array<{ menu: string; rating: number }>> = {
      heavy_meal: [],
      snack: [],
      beverages: []
    }

    menuItems.value.forEach(item => {
      if (item.rating > 0) {
        const categoryKey = item.category.toLowerCase().replace(' ', '_') as keyof typeof menuRatings
        if (menuRatings[categoryKey]) {
          menuRatings[categoryKey].push({
            menu: item.menu,
            rating: item.rating
          })
        }
      }
    })

    const payload = {
      order_id: orderData.value.order_id,
      meal_time: form.value.mealTime,
      date_of_feedback: orderData.value.order_date,
      user_type: form.value.userType,
      user_name: isAnonymous.value ? undefined : form.value.name,
      is_anonymous: isAnonymous.value,
      spice_level: form.value.spiceLevel || undefined,
      additional_comments: form.value.comment || undefined,
      menu_ratings: menuRatings
    }

    await axios.post(`${API_URL}/api/rating-food/${institutionId}`, payload)

    toast.success('Feedback submitted!', {
      description: 'Thank you for helping us improve.'
    })

    resetForm()
  } catch (err: any) {
    console.error('Failed to submit feedback:', err)
    const errorMsg = err.response?.data?.detail || 'Failed to submit feedback. Please try again.'
    toast.error('Error', {
      description: errorMsg
    })
  } finally {
    isSubmitting.value = false
  }
}

const resetForm = () => {
  form.value.comment = ''
  form.value.spiceLevel = ''
  form.value.name = ''
  isAnonymous.value = false
  // Reset ratings
  if (orderData.value?.menu_details) {
    Object.values(orderData.value.menu_details).forEach(items => {
      if (items) {
        items.forEach(item => {
          item.rating = 0
        })
      }
    })
  }
}

// Initial fetch
onMounted(() => {
  fetchOrderData()
})
</script>

<template>
  <div class="min-h-screen w-full bg-[#F8FAFC] flex flex-col items-center justify-center p-4 font-inter py-12">

    <!-- Loading State -->
    <div v-if="isLoading" class="flex flex-col items-center justify-center gap-4">
      <Loader2 class="h-12 w-12 text-emerald-600 animate-spin" />
      <p class="text-zinc-600 font-medium">Loading order information...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center gap-4 max-w-md">
      <AlertCircle class="h-12 w-12 text-red-500" />
      <p class="text-zinc-700 font-medium text-center">{{ error }}</p>
    </div>

    <!-- Main Form -->
    <template v-else-if="orderData">
      <div class="text-center space-y-2 mb-8">
        <h1 class="text-3xl font-extrabold text-zinc-900 tracking-tight">We value your opinion!</h1>
        <p class="text-zinc-500 font-medium">Your feedback helps us improve the dining experience.</p>
      </div>

      <Card class="w-full max-w-[550px] shadow-xl border-zinc-200/50 overflow-hidden">
        <!-- Green Header Info -->
        <div class="bg-[#EBFDF5] px-6 py-4 flex items-center justify-between border-b border-[#D1FAE5]">
          <div class="flex items-start gap-3">
            <div class="bg-[#22C55E] p-1.5 rounded-md mt-0.5">
              <Building2 class="h-4 w-4 text-white" />
            </div>
            <div>
              <span class="text-[10px] font-bold text-[#15803D] uppercase tracking-wider block mb-0.5">Institution</span>
              <span class="text-sm font-bold text-zinc-900">{{ orderData.institution_name }}</span>
            </div>
          </div>

          <div class="flex items-start gap-3 text-right">
            <div class="bg-[#22C55E] p-1.5 rounded-md mt-0.5 order-2">
              <Calendar class="h-4 w-4 text-white" />
            </div>
            <div class="order-1">
              <span class="text-[10px] font-bold text-[#15803D] uppercase tracking-wider block mb-0.5">Date</span>
              <span class="text-sm font-bold text-zinc-900">{{ formatDate(orderData.order_date) }}</span>
            </div>
          </div>
        </div>

        <CardContent class="p-8 space-y-8">

          <!-- User Info Section -->
          <div class="space-y-6">
            <div class="space-y-2">
              <Label class="text-xs font-bold text-zinc-500 uppercase tracking-widest">
                Name <span class="text-zinc-400 font-normal capitalize tracking-normal">(Optional)</span>
              </Label>
              <Input
                v-model="form.name"
                placeholder="Enter your name"
                class="h-11 bg-white border-zinc-200 focus-visible:ring-emerald-500 disabled:opacity-50"
                :disabled="isAnonymous"
              />
            </div>

            <div class="grid grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label class="text-sm font-bold text-zinc-800">User Type</Label>
                <Select v-model="form.userType">
                  <SelectTrigger class="h-11 border-zinc-200 bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="STAFF">STAFF</SelectItem>
                    <SelectItem value="STUDENT">STUDENT</SelectItem>
                    <SelectItem value="TEACHER">TEACHER</SelectItem>
                    <SelectItem value="GUEST">GUEST</SelectItem>
                    <SelectItem value="OTHER">OTHER</SelectItem>
                    <SelectItem value="NONE">NONE</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-2">
                <Label class="text-sm font-bold text-zinc-800">Meal Time</Label>
                <Select v-model="form.mealTime">
                  <SelectTrigger class="h-11 border-zinc-200 bg-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Makan Pagi">Makan Pagi</SelectItem>
                    <SelectItem value="Makan Siang">Makan Siang</SelectItem>
                    <SelectItem value="Makan Malam">Makan Malam</SelectItem>
                    <SelectItem value="OTHER">OTHER</SelectItem>
                    <SelectItem value="NONE">NONE</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <!-- Rating Section -->
          <div class="space-y-5">
            <h3 class="font-bold text-lg text-zinc-900 border-b border-zinc-100 pb-2">Rate Menu Items</h3>

            <div v-if="menuItems.length === 0" class="text-center py-8 text-zinc-500">
              No menu items available for rating.
            </div>

            <div v-for="item in menuItems" :key="item.key" class="flex items-center justify-between p-3 rounded-lg hover:bg-zinc-50 transition-colors group">
              <div class="flex-1">
                <span class="text-xs font-bold text-zinc-900 uppercase block">{{ item.category }}</span>
                <span class="text-sm font-medium text-zinc-700">{{ item.menu }}</span>
              </div>

              <!-- Stars -->
              <div class="flex gap-1">
                <button
                  v-for="star in 5"
                  :key="star"
                  type="button"
                  class="p-0.5 focus:outline-none transition-transform hover:scale-110"
                  @mouseenter="setHover(item.key, star)"
                  @mouseleave="clearHover(item.key)"
                  @click="setRating(item.key, star)"
                >
                  <Star
                    class="h-6 w-6 transition-colors"
                    :class="(hoverState[item.key] || item.rating) >= star ? 'fill-[#22C55E] text-[#22C55E]' : 'fill-transparent text-zinc-300'"
                    stroke-width="2.5"
                  />
                </button>
              </div>
            </div>
          </div>

          <div class="h-px bg-zinc-100 w-full"></div>

          <!-- Footer Form -->
          <div class="space-y-6">
            <div class="flex items-end justify-between gap-4">
              <div class="space-y-2 flex-1">
                <Label class="text-xs font-bold text-zinc-500 uppercase">
                  Spice Level <span class="text-zinc-400 font-normal capitalize">(Optional)</span>
                </Label>
                <Select v-model="form.spiceLevel">
                  <SelectTrigger class="h-10 border-zinc-200 bg-white">
                    <SelectValue placeholder="Pilih level pedas" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Tidak Pedas">Tidak Pedas</SelectItem>
                    <SelectItem value="Sedang">Sedang</SelectItem>
                    <SelectItem value="Pedas">Pedas</SelectItem>
                    <SelectItem value="Sangat Pedas">Sangat Pedas</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="flex items-center gap-3 pb-2">
                <Label class="text-sm font-semibold text-zinc-700 cursor-pointer" for="anonymous-mode">Submit Anonymously</Label>
                <Switch 
                  id="anonymous-mode" 
                  :checked="isAnonymous"
                  :model-value="isAnonymous"
                  @update:checked="(val: boolean) => isAnonymous = val"
                  @update:model-value="(val: boolean) => isAnonymous = val"
                />
              </div>
            </div>

            <div class="space-y-2">
              <div class="flex justify-between">
                <Label class="text-sm font-bold text-zinc-800">Additional Comments</Label>
                <span class="text-[10px] text-zinc-400 uppercase font-medium tracking-wider">Optional</span>
              </div>
              <Textarea
                v-model="form.comment"
                placeholder="Contoh: Rasa kurang asin / Porsi kurang / Terlalu pedas / Enak sekali"
                class="min-h-[100px] resize-none bg-white border-zinc-200 focus:border-emerald-500 focus:ring-emerald-500/20"
                maxlength="200"
              />
              <div class="text-right text-xs text-zinc-400">
                {{ form.comment.length }}/200
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="grid grid-cols-2 gap-4 mt-4">
            <Button variant="outline" class="h-11 border-zinc-200 text-zinc-700 hover:bg-zinc-50 font-semibold" @click="resetForm">
              Cancel
            </Button>
            <Button
              class="h-11 font-bold text-md shadow-lg shadow-emerald-500/20 transition-all hover:translate-y-[px]"
              :class="isValid ? 'bg-[#00E560] hover:bg-[#00CC55] text-emerald-950' : 'bg-zinc-100 text-zinc-400 cursor-not-allowed'"
              :disabled="!isValid || isSubmitting"
              @click="submitFeedback"
            >
              <div v-if="isSubmitting" class="flex items-center gap-2">
                <Loader2 class="h-5 w-5 animate-spin" />
                <span>Sending...</span>
              </div>
              <div v-else class="flex items-center gap-2">
                Submit Feedback
                <Send class="h-4 w-4" />
              </div>
            </Button>
          </div>

        </CardContent>
      </Card>

      <div class="mt-8 text-center">
        <p class="text-zinc-400 text-xs">Powered by DCSA Institutional Solutions</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.font-inter {
  font-family: 'Plus Jakarta Sans', sans-serif;
}
</style>
