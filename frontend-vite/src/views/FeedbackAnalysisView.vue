<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Search,
  Bell,
  Menu,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Users,
  LogOut,
  Loader2,
  MessageSquare,
  ChevronUp,
  Star
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Auth & Router
const router = useRouter()
const authStore = useAuthStore()

// RBAC Check
const isAuthorized = computed(() => {
  const role = authStore.getRole
  return role === 'DK_ADMIN' || role === 'SUPER_ADMIN'
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Types
interface MenuRatingItem {
  menu: string
  rating: number
}

interface MenuRatings {
  heavy_meal?: MenuRatingItem[]
  snack?: MenuRatingItem[]
  beverages?: MenuRatingItem[]
}

interface Feedback {
  id: string
  institution_id: string
  order_id: string
  meal_time: string
  date_of_feedback: string
  user_type: string
  user_name: string | null
  is_anonymous: boolean
  spice_level: string | null
  additional_comments: string | null
  menu_ratings: MenuRatings
  created_at: string
  // Joined data
  institution?: { name: string; institution_id: string }
}

interface FeedbackListResponse {
  feedbacks: Feedback[]
  total: number
  page: number
  page_size: number
}

// Sidebar state
const isSidebarOpen = ref(true)
const toggleSidebar = () => isSidebarOpen.value = !isSidebarOpen.value

// Loading State
const isLoading = ref(true)
const isInitialLoad = ref(true)

// Feedbacks Data from API
const rawFeedbacks = ref<Feedback[]>([])

// Pagination State
const pageSize = ref(10)
const currentPage = ref(1)
const totalFeedbacks = ref(0)

// Filters State
const filterDate = ref<string | undefined>(undefined)
const filterInstitution = ref('all')
const filterSearch = ref('')

// Expanded rows state
const expandedRows = ref<Set<string>>(new Set())

// Institution list for filter
const institutions = ref<Array<{ institution_id: string; name: string }>>([])

// Fetch institutions
const fetchInstitutions = async () => {
  try {
    const response = await axios.get(`${API_URL}/api/institutions/`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })
    institutions.value = response.data
  } catch (error) {
    console.error('Failed to fetch institutions:', error)
  }
}

// Fetch feedbacks from API
const fetchFeedbacks = async () => {
  try {
    isLoading.value = true
    const params = new URLSearchParams()

    // Add pagination params
    params.append('skip', ((currentPage.value - 1) * pageSize.value).toString())
    params.append('limit', pageSize.value.toString())

    // Add date filter
    if (filterDate.value) {
      params.append('date_of_feedback', filterDate.value)
    }

    // Add institution filter
    if (filterInstitution.value && filterInstitution.value !== 'all') {
      params.append('institution_id', filterInstitution.value)
    }

    const response = await axios.get<FeedbackListResponse>(`${API_URL}/api/rating-food/`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      params
    })

    rawFeedbacks.value = response.data.feedbacks
    totalFeedbacks.value = response.data.total
  } catch (error) {
    console.error('Failed to fetch feedbacks:', error)
  } finally {
    isLoading.value = false
    isInitialLoad.value = false
  }
}

// Search by feedback_id
const searchByFeedbackId = async (feedbackId: string) => {
  try {
    isLoading.value = true
    const params = new URLSearchParams()
    params.append('feedback_id', feedbackId)

    const response = await axios.get<FeedbackListResponse>(`${API_URL}/api/rating-food/`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      params
    })

    rawFeedbacks.value = response.data.feedbacks
    totalFeedbacks.value = response.data.total
  } catch (error) {
    console.error('Failed to search feedback:', error)
    rawFeedbacks.value = []
    totalFeedbacks.value = 0
  } finally {
    isLoading.value = false
    isInitialLoad.value = false
  }
}

// Handle search on Enter key
const handleSearchKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && filterSearch.value.trim()) {
    currentPage.value = 1
    searchByFeedbackId(filterSearch.value.trim())
  } else if (event.key === 'Enter' && !filterSearch.value.trim()) {
    // Clear search and fetch all
    currentPage.value = 1
    fetchFeedbacks()
  }
}

// Initial fetch on mount
onMounted(() => {
  if (isAuthorized.value) {
    fetchInstitutions()
    fetchFeedbacks()
  }
})

// Watch filter changes and refetch
watch([filterDate, filterInstitution, currentPage], () => {
  if (!filterSearch.value.trim()) {
    fetchFeedbacks()
  }
})

// Toggle row expansion
const toggleRowExpansion = (feedbackId: string) => {
  if (expandedRows.value.has(feedbackId)) {
    expandedRows.value.delete(feedbackId)
  } else {
    expandedRows.value.add(feedbackId)
  }
}

// Calculate average rating from menu_ratings
const getAverageRating = (menuRatings: MenuRatings): number => {
  const allRatings: number[] = []

  if (menuRatings.heavy_meal) {
    menuRatings.heavy_meal.forEach(item => {
      if (item.rating) allRatings.push(item.rating)
    })
  }
  if (menuRatings.snack) {
    menuRatings.snack.forEach(item => {
      if (item.rating) allRatings.push(item.rating)
    })
  }
  if (menuRatings.beverages) {
    menuRatings.beverages.forEach(item => {
      if (item.rating) allRatings.push(item.rating)
    })
  }

  if (allRatings.length === 0) return 0
  return Math.round((allRatings.reduce((a, b) => a + b, 0) / allRatings.length) * 10) / 10
}

// Get institution name from feedback
const getInstitutionName = (feedback: Feedback): string => {
  if (feedback.institution && feedback.institution.name) {
    return feedback.institution.name
  }
  // Fallback: find from institutions list
  const inst = institutions.value.find(i => i.institution_id === feedback.institution_id)
  return inst?.name || 'Unknown'
}

// Helpers
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return dateString
}

const formatMealTime = (mealTime: string) => {
  return mealTime || '-'
}
</script>

<template>
  <!-- Unauthorized View -->
  <div v-if="!isAuthorized" class="flex h-screen items-center justify-center bg-[#F9FAFB]">
    <div class="text-center space-y-4">
      <h1 class="text-2xl font-bold text-zinc-900">Access Denied</h1>
      <p class="text-zinc-500">You don't have permission to view this page.</p>
      <Button @click="router.push('/')" class="bg-emerald-600 hover:bg-emerald-700">
        Go to Dashboard
      </Button>
    </div>
  </div>

  <!-- Authorized View -->
  <div v-else class="flex h-screen bg-[#F9FAFB] text-zinc-900 font-inter">
    <!-- Sidebar -->
    <aside 
      class="bg-[#020817] text-zinc-400 w-64 shrink-0 transition-all duration-300 ease-in-out border-r border-zinc-800 lg:static fixed z-50 h-full"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:hidden'"
    >
      <div class="p-6 h-full flex flex-col">
        <div class="flex items-center gap-3 mb-10">
          <img src="@/assets/dcsa-logo.svg" alt="DCSA Logo" class="h-8 w-auto brightness-125" />
          <span class="font-bold text-xl text-white tracking-wide">DCSA</span>
        </div>
        <nav class="space-y-1 flex-1">
          <router-link to="/home-admin" class="flex items-center gap-3 px-4 py-3 rounded-lg group transition-colors hover:bg-zinc-800/30 hover:text-white">
            <LayoutDashboard class="h-5 w-5" />
            <span class="font-medium">Dashboard</span>
          </router-link>
          <router-link to="/home-admin" class="flex items-center gap-3 px-4 py-3 rounded-lg group transition-colors hover:bg-zinc-800/30 hover:text-white">
            <Users class="h-5 w-5" />
            <span class="font-medium">User Management</span>
          </router-link>
          <router-link to="/feedback-analysis" class="flex items-center gap-3 px-4 py-3 rounded-lg group transition-colors bg-zinc-800/50 text-zinc-200">
            <MessageSquare class="h-5 w-5" />
            <span class="font-medium">Feedback Analysis</span>
          </router-link>
        </nav>
        <div class="mt-auto pt-6 border-t border-zinc-800">
          <Button @click="handleLogout" variant="ghost" class="w-full justify-start gap-3 text-zinc-400 hover:text-red-400 hover:bg-red-400/10 transition-colors">
            <LogOut class="h-5 w-5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="h-16 bg-white border-b border-zinc-200 flex items-center justify-between px-6 shrink-0">
        <div class="flex items-center gap-4">
          <Button variant="ghost" size="icon" @click="toggleSidebar" class="lg:hidden">
            <Menu class="h-5 w-5" />
          </Button>
          <h2 class="font-semibold text-lg">Admin / Feedback Analysis</h2>
        </div>
        <div class="flex items-center gap-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <Button variant="ghost" size="icon" class="text-zinc-500 relative">
                  <Bell class="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Notifications</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Avatar class="h-8 w-8">
            <AvatarImage src="https://ui.shadcn.com/avatars/02.png" />
            <AvatarFallback>AD</AvatarFallback>
          </Avatar>
        </div>
      </header>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Top Filters Section -->
        <div class="bg-white border border-zinc-100 rounded-xl p-6 shadow-sm space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Feedback Date</label>
              <div class="relative group">
                <Input 
                  type="date" 
                  v-model="filterDate" 
                  class="h-11 bg-zinc-50 border-zinc-200 focus-visible:ring-0 pr-10 appearance-none date-input-custom" 
                />
                <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400 pointer-events-none" />
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Institution</label>
              <Select v-model="filterInstitution">
                <SelectTrigger class="h-11 bg-zinc-50 border-zinc-200 focus-visible:ring-0 capitalize">
                  <SelectValue placeholder="All Institutions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all" class="capitalize">All Institutions</SelectItem>
                  <SelectItem v-for="inst in institutions" :key="inst.institution_id" :value="inst.institution_id" class="capitalize">
                    {{ inst.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Search</label>
              <div class="relative">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input
                  v-model="filterSearch"
                  placeholder="Search feedback ID (Press Enter)"
                  @keydown="handleSearchKeydown"
                  class="h-11 pl-10 bg-zinc-50 border-zinc-200 focus-visible:ring-0"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Table Section -->
        <div class="bg-white border border-zinc-100 rounded-xl shadow-sm overflow-hidden">
          <!-- Loading State -->
          <div v-if="isInitialLoad" class="flex items-center justify-center py-20">
            <div class="flex flex-col items-center gap-3">
              <Loader2 class="h-8 w-8 text-emerald-600 animate-spin" />
              <p class="text-sm text-zinc-500">Loading feedbacks...</p>
            </div>
          </div>

          <!-- Loading Overlay for non-initial loads -->
          <div v-if="isLoading && !isInitialLoad" class="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
            <Loader2 class="h-6 w-6 text-emerald-600 animate-spin" />
          </div>

          <Table v-else>
            <TableHeader class="bg-zinc-50/50">
              <TableRow class="hover:bg-transparent">
                <TableHead class="w-12"></TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Date</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Institution</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Feedback ID</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Meal Time</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Rating</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="feedback in rawFeedbacks" :key="feedback.id">
                <!-- Main Row -->
                <TableRow class="group transition-colors h-16 border-b border-zinc-50 cursor-pointer hover:bg-zinc-50" @click="toggleRowExpansion(feedback.id)">
                  <TableCell>
                    <Button variant="ghost" size="icon" class="h-6 w-6">
                      <ChevronUp v-if="expandedRows.has(feedback.id)" class="h-4 w-4 text-zinc-400" />
                      <ChevronDown v-else class="h-4 w-4 text-zinc-400" />
                    </Button>
                  </TableCell>
                  <TableCell class="font-medium text-zinc-900">{{ formatDate(feedback.date_of_feedback) }}</TableCell>
                  <TableCell>
                    <div class="font-bold text-zinc-900">{{ getInstitutionName(feedback) }}</div>
                  </TableCell>
                  <TableCell class="text-emerald-600/60 font-medium text-[13px]">
                    {{ feedback.id.slice(0, 8) }}...
                  </TableCell>
                  <TableCell class="font-medium text-zinc-700">{{ formatMealTime(feedback.meal_time) }}</TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <Star class="h-4 w-4 text-yellow-400 fill-yellow-400" />
                      <span class="font-bold text-zinc-900">{{ getAverageRating(feedback.menu_ratings) }}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" class="rounded-lg px-3 py-1 font-bold shadow-sm whitespace-nowrap bg-emerald-50 text-emerald-600 border-emerald-100">
                      Received
                    </Badge>
                  </TableCell>
                </TableRow>

                <!-- Expanded Details Row -->
                <TableRow v-if="expandedRows.has(feedback.id)" class="bg-zinc-50/50">
                  <TableCell colspan="7" class="p-0">
                    <div class="p-6 space-y-4">
                      <!-- User Info -->
                      <div class="flex items-center gap-6 text-sm">
                        <div>
                          <span class="text-zinc-500">User:</span>
                          <span class="ml-2 font-medium text-zinc-900">
                            {{ feedback.is_anonymous ? 'Anonymous' : (feedback.user_name || '-') }}
                          </span>
                        </div>
                        <div>
                          <span class="text-zinc-500">Type:</span>
                          <span class="ml-2 font-medium text-zinc-900">{{ feedback.user_type }}</span>
                        </div>
                        <div v-if="feedback.spice_level">
                          <span class="text-zinc-500">Spice Level:</span>
                          <span class="ml-2 font-medium text-zinc-900">{{ feedback.spice_level }}</span>
                        </div>
                      </div>

                      <!-- Menu Ratings Breakdown -->
                      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <!-- Heavy Meal -->
                        <div v-if="feedback.menu_ratings.heavy_meal && feedback.menu_ratings.heavy_meal.length > 0" class="bg-white rounded-lg border border-zinc-100 p-4">
                          <h4 class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Heavy Meal</h4>
                          <div class="space-y-2">
                            <div v-for="item in feedback.menu_ratings.heavy_meal" :key="item.menu" class="flex items-center justify-between">
                              <span class="text-sm text-zinc-700">{{ item.menu }}</span>
                              <div class="flex items-center gap-1">
                                <Star class="h-3 w-3 text-yellow-400 fill-yellow-400" />
                                <span class="text-sm font-medium">{{ item.rating }}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <!-- Snack -->
                        <div v-if="feedback.menu_ratings.snack && feedback.menu_ratings.snack.length > 0" class="bg-white rounded-lg border border-zinc-100 p-4">
                          <h4 class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Snack</h4>
                          <div class="space-y-2">
                            <div v-for="item in feedback.menu_ratings.snack" :key="item.menu" class="flex items-center justify-between">
                              <span class="text-sm text-zinc-700">{{ item.menu }}</span>
                              <div class="flex items-center gap-1">
                                <Star class="h-3 w-3 text-yellow-400 fill-yellow-400" />
                                <span class="text-sm font-medium">{{ item.rating }}</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        <!-- Beverages -->
                        <div v-if="feedback.menu_ratings.beverages && feedback.menu_ratings.beverages.length > 0" class="bg-white rounded-lg border border-zinc-100 p-4">
                          <h4 class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3">Beverages</h4>
                          <div class="space-y-2">
                            <div v-for="item in feedback.menu_ratings.beverages" :key="item.menu" class="flex items-center justify-between">
                              <span class="text-sm text-zinc-700">{{ item.menu }}</span>
                              <div class="flex items-center gap-1">
                                <Star class="h-3 w-3 text-yellow-400 fill-yellow-400" />
                                <span class="text-sm font-medium">{{ item.rating }}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Comments -->
                      <div v-if="feedback.additional_comments" class="bg-white rounded-lg border border-zinc-100 p-4">
                        <h4 class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">Comments</h4>
                        <p class="text-sm text-zinc-700">{{ feedback.additional_comments }}</p>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              </template>
              <TableRow v-if="rawFeedbacks.length === 0 && !isLoading">
                <TableCell colspan="7" class="text-center py-8 text-zinc-500">
                  No feedbacks found.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <!-- Table Pagination Footer -->
          <div class="px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-zinc-50 bg-zinc-50/20">
            <div class="flex items-center gap-4 text-xs font-medium text-emerald-600/70">
              <div class="flex items-center gap-2">
                Rows per page:
                <Select v-model="pageSize" @update:model-value="currentPage = 1; fetchFeedbacks()" class="w-16">
                  <SelectTrigger class="h-8 w-16 border-zinc-200">
                    <SelectValue :placeholder="pageSize.toString()" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem :value="5">5</SelectItem>
                    <SelectItem :value="10">10</SelectItem>
                    <SelectItem :value="20">20</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                {{ rawFeedbacks.length > 0 ? (currentPage - 1) * pageSize + 1 : 0 }}-{{ (currentPage - 1) * pageSize + rawFeedbacks.length }} of {{ totalFeedbacks }}
              </div>
            </div>

            <div class="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                :disabled="currentPage === 1 || isLoading"
                @click="currentPage--"
                class="hover:bg-emerald-50 text-emerald-600"
              >
                <ChevronLeft class="h-4 w-4" />
              </Button>
              <div class="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  :class="'bg-[#44bb2c] text-white'"
                  class="hover:bg-emerald-50 text-emerald-600"
                >
                  {{ currentPage }}
                </Button>
              </div>
              <Button
                variant="ghost"
                size="icon"
                :disabled="rawFeedbacks.length < pageSize || isLoading"
                @click="currentPage++"
                class="hover:bg-emerald-50 text-emerald-600"
              >
                <ChevronRight class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-inter {
  font-family: 'Inter', sans-serif;
}

/* Hide native date picker icon */
.date-input-custom::-webkit-calendar-picker-indicator {
  background: transparent;
  bottom: 0;
  color: transparent;
  cursor: pointer;
  height: auto;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
  width: auto;
}
</style>
