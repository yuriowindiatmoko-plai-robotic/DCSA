<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Star, Loader2, Building2, Calendar, Send } from 'lucide-vue-next'
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

// Mock Data
const MOCK_INSTITUTION = {
  id: "PLAI",
  name: "PLAI",
}

const getToday = () => {
  const date = new Date()
  const day = date.getDate()
  const monthNames = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
  ]
  const month = monthNames[date.getMonth()]
  const year = date.getFullYear()
  return `${day} ${month} ${year}`
}

const currentDate = getToday()

const route = useRoute()
const institutionId = route.params.institutionId

// Form State
const form = ref({
  name: '',
  userType: 'STAFF',
  mealTime: 'Makan Siang',
  spiceLevel: '',
  isAnonymous: false,
  comment: ''
})

// Menu Items State
const menuItems = ref([
  { 
    id: 'kh', 
    label: 'KH', 
    name: 'Nasi', 
    rating: 0, 
    required: false,
    options: ['Nasi', 'Bubur', 'Lontong', 'Ketupat']
  },
  { 
    id: 'sambal', 
    label: 'SAMBAL', 
    name: 'Sambel Hijau', 
    rating: 0, 
    required: false,
    options: ['Sambel Hijau', 'Sambel Terasi', 'Sambel Bawang', 'Sambel Matah']
  },
  { 
    id: 'sayur', 
    label: 'SAYUR', 
    name: 'Sayur Tempe', 
    rating: 0, 
    required: true,
    options: ['Sayur Tempe', 'Sayur Asem', 'Sop Ayam', 'Lodeh']
  },
  { 
    id: 'lauk', 
    label: 'LAUK', 
    name: 'Ayam Kecap', 
    rating: 0, 
    required: true,
    options: ['Ayam Kecap', 'Ikan Goreng', 'Telur Balado', 'Rendang']
  },
  { 
    id: 'buah', 
    label: 'BUAH', 
    name: 'Melon', 
    rating: 0, 
    required: false,
    options: ['Melon', 'Semangka', 'Pisang', 'Jeruk']
  },
])

const isSubmitting = ref(false)

// Hover State for Stars
const hoverState = ref<Record<string, number>>({})

const setHover = (id: string, star: number) => {
  hoverState.value[id] = star
}

const clearHover = (id: string) => {
  hoverState.value[id] = 0
}

// Validation
const isValid = computed(() => {
  // Check required menu ratings
  const requiredItems = menuItems.value.filter(item => item.required)
  const allRequiredRated = requiredItems.every(item => item.rating > 0)
  
  // If not anonymous, name is optional/required? Screenshot says (Optional) for name, so maybe it's always valid.
  // Actually, let's strictly follow the "Required" badges on Sayur and Lauk.
  return allRequiredRated
})

const submitFeedback = async () => {
  if (!isValid.value) return

  isSubmitting.value = true
  
  // Simulate network request
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // Log payload
  console.log({
    meta: {
      institution_id: institutionId || MOCK_INSTITUTION.id,
      date: currentDate,
      user_type: form.value.userType,
      meal_time: form.value.mealTime,
      submitted_at: new Date().toISOString()
    },
    respondent: {
      name: form.value.isAnonymous ? 'Anonymous' : form.value.name,
      is_anonymous: form.value.isAnonymous
    },
    ratings: menuItems.value.map(item => ({
      category: item.label,
      dish_name: item.name,
      rating: item.rating
    })),
    preferences: {
      spice_level: form.value.spiceLevel
    },
    comment: form.value.comment
  })

  toast.success("Feedback submitted!", {
    description: "Thank you for helping us improve."
  })

  isSubmitting.value = false
  // Ideally redirect or show success state. For now, just toast and reset.
  resetForm()
}

const resetForm = () => {
  form.value.comment = ''
  form.value.spiceLevel = ''
  menuItems.value.forEach(item => item.rating = 0)
}
</script>

<template>
  <div class="min-h-screen w-full bg-[#F8FAFC] flex flex-col items-center justify-center p-4 font-inter py-12">
    
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
             <span class="text-sm font-bold text-zinc-900">{{ MOCK_INSTITUTION.name }}</span>
          </div>
        </div>
        
        <div class="flex items-start gap-3 text-right">
          <div class="bg-[#22C55E] p-1.5 rounded-md mt-0.5 order-2">
            <Calendar class="h-4 w-4 text-white" />
          </div>
          <div class="order-1">
             <span class="text-[10px] font-bold text-[#15803D] uppercase tracking-wider block mb-0.5">Date</span>
             <span class="text-sm font-bold text-zinc-900">{{ currentDate }}</span>
          </div>
        </div>
      </div>

      <CardContent class="p-8 space-y-8">
        
        <!-- User Info Section -->
        <div class="space-y-6">
          <div class="space-y-2">
            <Label class="text-xs font-bold text-zinc-500 uppercase tracking-widest">Name <span class="text-zinc-400 font-normal capitalize tracking-normal">(Optional)</span></Label>
            <Input 
              v-model="form.name" 
              placeholder="Enter your name" 
              class="h-11 bg-white border-zinc-200 focus-visible:ring-emerald-500 disabled:opacity-50"
              :disabled="form.isAnonymous"
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
                  <SelectItem value="GUEST">GUEST</SelectItem>
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
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <!-- Rating Section -->
        <div class="space-y-5">
          <h3 class="font-bold text-lg text-zinc-900 border-b border-zinc-100 pb-2">Rate Menu Items</h3>
          
          <div v-for="item in menuItems" :key="item.id" class="flex items-center justify-between p-3 rounded-lg hover:bg-zinc-50 transition-colors group">
             <div class="flex items-center gap-4 flex-1">
               <div class="w-16 shrink-0">
                 <span class="text-xs font-bold text-zinc-900 uppercase block">{{ item.label }}</span>
                 <span v-if="item.required" class="text-[10px] text-red-500 font-medium">* Required</span>
               </div>
               
               <div class="flex-1 max-w-[200px]">
                 <Select v-model="item.name">
                    <SelectTrigger class="h-10 border-zinc-200 bg-white shadow-sm">
                      <SelectValue :placeholder="item.name" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem v-for="option in item.options" :key="option" :value="option">
                        {{ option }}
                      </SelectItem>
                    </SelectContent>
                 </Select>
               </div>
             </div>

             <!-- Stars -->
             <div class="flex gap-1">
                <button 
                  v-for="star in 5" 
                  :key="star"
                  type="button"
                  class="p-0.5 focus:outline-none transition-transform hover:scale-110"
                  @mouseenter="setHover(item.id, star)"
                  @mouseleave="clearHover(item.id)"
                  @click="item.rating = star"
                >
                  <Star 
                    class="h-6 w-6 transition-colors"
                    :class="(hoverState[item.id] || item.rating) >= star ? 'fill-[#22C55E] text-[#22C55E]' : 'fill-transparent text-zinc-300'"
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
                <Label class="text-xs font-bold text-zinc-500 uppercase">Spice Level <span class="text-zinc-400 font-normal capitalize">(Optional)</span></Label>
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
                <Switch id="anonymous-mode" :checked="form.isAnonymous" @update:checked="form.isAnonymous = $event" />
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
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

.font-inter {
  font-family: 'Plus Jakarta Sans', sans-serif;
}
</style>
