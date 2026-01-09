<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  Search, 
  Bell, 
  MoreHorizontal,
  AlertCircle,
  Menu,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  LogOut,
  ArrowUpDown
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
import OrderDetailsModal from '@/components/OrderDetailsModal.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
    authStore.logout()
    router.push('/login')
}


// Types
interface Order {
  id: number
  orderId: string
  date: string
  institution: string
  portions: number
  location: string
  staff: number
  status: string
  alerts: number | null
  ratings: number
}

// Sidebar state
const isSidebarOpen = ref(true)
const toggleSidebar = () => isSidebarOpen.value = !isSidebarOpen.value

// Mock Logged In User Institution
const currentInstitution = 'VHS'

// Filters State
const todayString = new Date().toISOString().split('T')[0]
const filterDate = ref(todayString)
const filterSearch = ref('')

const filterStatus = ref('All Orders')

// Modal State
const isModalOpen = ref(false)
const selectedOrder = ref<Order | null>(null)

const handleEditDetails = (order: Order) => {
  selectedOrder.value = { ...order } // Clone to avoid direct mutation
  isModalOpen.value = true
}

const handleSaveChanges = (updatedOrder: Order) => {
  const index = rawOrders.value.findIndex(o => o.id === updatedOrder.id)
  if (index !== -1) {
    rawOrders.value[index] = { ...updatedOrder }
  }
  isModalOpen.value = false
}

const statusOptions = ['All Orders', 'Requested Edit', 'Edited', 'Cooking', 'Delivered']

// Dummy Data (Same as Admin, but will be filtered)
const rawOrders = ref<Order[]>([
  { id: 1, orderId: '#ORD-2091', date: '2023-10-24', institution: 'VHS', portions: 450, location: 'Main Hall', staff: 3, status: 'Requested Edit', alerts: 2, ratings: 4.8 },
  { id: 2, orderId: '#ORD-2092', date: '2023-10-24', institution: 'PLAI', portions: 1200, location: 'Main Hall', staff: 5, status: 'Ordered', alerts: null, ratings: 0 },
  { id: 3, orderId: '#ORD-2095', date: '2023-10-25', institution: 'SD BMD Panjen', portions: 300, location: 'Classroom', staff: 5, status: 'Edited', alerts: null, ratings: 0 },
  { id: 4, orderId: '#ORD-2101', date: '2023-10-25', institution: 'SMP BMD', portions: 50, location: 'Cafetaria', staff: 4, status: 'Cooking', alerts: null, ratings: 0 },
  { id: 5, orderId: '#ORD-2088', date: '2023-10-23', institution: 'SMA BMD', portions: 850, location: 'Main Hall', staff: 5, status: 'Delivered', alerts: null, ratings: 0 },
  // Add more for pagination demo
  { id: 6, orderId: '#ORD-3001', date: '2023-10-24', institution: 'Binus Univ', portions: 150, location: 'Aula', staff: 2, status: 'Delivered', alerts: null, ratings: 4.5 },
  { id: 7, orderId: '#ORD-3002', date: '2023-10-24', institution: 'VHS', portions: 200, location: 'Main Hall', staff: 3, status: 'Cooking', alerts: 1, ratings: 0 },
  { id: 8, orderId: '#ORD-3003', date: '2023-10-23', institution: 'PLAI', portions: 500, location: 'Lab', staff: 4, status: 'Edited', alerts: null, ratings: 4.9 },
])

// Sorting
const sortField = ref<keyof Order | null>(null)
const sortOrder = ref<'asc' | 'desc'>('asc')

const handleSort = (field: keyof Order) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'asc'
  }
}

// Reactive Pipeline with Data Isolation
const filteredOrders = computed(() => {
  let result = rawOrders.value.filter(o => {
    // strict isolation
    if (o.institution !== currentInstitution) return false

    const matchDate = filterDate.value ? o.date === filterDate.value : true
    const matchSearch = o.orderId.toLowerCase().includes(filterSearch.value.toLowerCase()) || 
                      o.location.toLowerCase().includes(filterSearch.value.toLowerCase())
    const matchStatus = filterStatus.value === 'All Orders' || o.status === filterStatus.value || (filterStatus.value === 'Ordered' && o.status === 'Ordered')
    
    return matchDate && matchSearch && matchStatus
  })

  if (sortField.value) {
    result = [...result].sort((a, b) => {
      const valA = a[sortField.value!]
      const valB = b[sortField.value!]
      if (valA === valB) return 0
      if (valA === null) return 1
      if (valB === null) return -1
      
      const modifier = sortOrder.value === 'asc' ? 1 : -1
      return valA < valB ? -1 * modifier : 1 * modifier
    })
  }

  return result
})

// Pagination
const pageSize = ref(10)
const currentPage = ref(1)
const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredOrders.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(filteredOrders.value.length / pageSize.value))

// Notifications Logic (Mocked for Client)
const requestedEditCount = computed(() => 
  rawOrders.value.filter(o => o.institution === currentInstitution && (o.status === 'Requested Edit' || o.status === 'Edited')).length
)


// Helpers
const getStatusClasses = (status: string) => {
  switch (status) {
    case 'Requested Edit': return 'bg-yellow-50 text-yellow-600 border-yellow-100'
    case 'Ordered': return 'bg-green-50 text-green-600 border-green-100'
    case 'Edited': return 'bg-blue-50 text-blue-600 border-blue-100'
    case 'Cooking': return 'bg-orange-50 text-orange-600 border-orange-100'
    case 'Delivered': return 'bg-emerald-50 text-emerald-600 border-emerald-100'
    default: return 'bg-gray-50 text-gray-500 border-gray-100'
  }
}
</script>

<template>
  <div class="flex h-screen bg-[#F9FAFB] text-zinc-900 font-inter">
    <!-- Sidebar -->
    <aside 
      class="bg-[#020817] text-zinc-400 w-64 shrink-0 transition-all duration-300 ease-in-out border-r border-zinc-800 lg:static fixed z-50 h-full"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:hidden'"
    >
      <div class="p-6 h-full flex flex-col">
        <div class="flex items-center gap-3 mb-10">
          <img src="@/assets/dcsa-logo.svg" alt="DCSA Logo" class="h-8 w-auto brightness-125 filter-[invert(48%)_sepia(79%)_saturate(2476%)_hue-rotate(120deg)_brightness(118%)_contrast(119%)]" />
          <span class="font-bold text-xl text-white tracking-wide">DCSA</span>
        </div>
        <nav class="space-y-1 flex-1">
          <a href="#dashboard" class="flex items-center gap-3 px-4 py-3 text-zinc-200 bg-zinc-800/50 rounded-lg group">
            <LayoutDashboard class="h-5 w-5" />
            <span class="font-medium">Dashboard</span>
          </a>
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
          <h2 class="font-semibold text-lg">Client / My Orders</h2>
        </div>
        <div class="flex items-center gap-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  class="text-zinc-500 relative"
                >
                  <Bell class="h-5 w-5" />
                  <span v-if="requestedEditCount > 0" class="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>You have {{ requestedEditCount }} updates on your orders</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Avatar class="h-8 w-8">
            <AvatarImage src="https://ui.shadcn.com/avatars/04.png" />
            <AvatarFallback>CL</AvatarFallback>
          </Avatar>
        </div>
      </header>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Top Filters Section -->
        <div class="bg-white border border-zinc-100 rounded-xl p-6 shadow-sm space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Date</label>
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
              <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Search</label>
              <div class="relative">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
                <Input 
                  v-model="filterSearch"
                  placeholder="Search order ID, location..." 
                  class="h-11 pl-10 bg-zinc-50 border-zinc-200 focus-visible:ring-0"
                />
              </div>
            </div>
          </div>

          <div class="flex items-center gap-3">
             <span class="text-sm font-medium text-emerald-600 mr-2">Status:</span>
             <div class="flex flex-wrap gap-2">
               <button 
                 v-for="status in statusOptions" 
                 :key="status"
                 @click="filterStatus = status"
                 class="px-4 py-1.5 rounded-full text-xs font-semibold transition-all border"
                 :class="filterStatus === status 
                   ? 'bg-zinc-900 text-white border-zinc-900 shadow-md' 
                   : 'bg-zinc-50 text-emerald-600 border-zinc-100 hover:bg-zinc-100'"
               >
                 {{ status }}
               </button>
             </div>
          </div>
        </div>

        <!-- Table Section -->
        <div class="bg-white border border-zinc-100 rounded-xl shadow-sm overflow-hidden">
          <Table>
            <TableHeader class="bg-zinc-50/50">
              <TableRow class="hover:bg-transparent">

                <TableHead @click="handleSort('date')" class="cursor-pointer hover:text-emerald-600 text-[11px] font-bold uppercase tracking-wider text-emerald-600/70 group">
                   <div class="flex items-center gap-1.5">
                     Date
                     <ArrowUpDown class="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                   </div>
                </TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Order ID</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Portions</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Location</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Staff</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Status</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Alerts</TableHead>
                <TableHead class="text-right text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="order in paginatedOrders" :key="order.id" class="group transition-colors h-16 border-b border-zinc-50" @click="handleEditDetails(order)">

                <TableCell class="font-medium text-zinc-900">{{ order.date }}</TableCell>
                <TableCell class="text-emerald-600/60 font-medium text-[13px]">{{ order.orderId }}</TableCell>
                <TableCell class="font-bold text-zinc-900">{{ order.portions.toLocaleString() }} pax</TableCell>
                <TableCell class="text-zinc-500 font-medium">{{ order.location }}</TableCell>
                <TableCell>
                  <span class="text-emerald-600 font-medium">{{ order.staff }} staff</span>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" :class="getStatusClasses(order.status)" class="rounded-lg px-3 py-1 font-bold shadow-sm whitespace-nowrap">
                    {{ order.status }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div v-if="order.alerts" class="bg-rose-50 border border-rose-100 text-rose-600 text-[10px] font-bold px-2 py-1 rounded flex items-center gap-1.5 w-fit">
                    <AlertCircle class="h-3 w-3" />
                    {{ order.alerts }} Edits
                  </div>
                  <span v-else class="text-zinc-300">-</span>
                </TableCell>
                <TableCell class="text-right">
                  <Button variant="ghost" size="icon" class="h-8 w-8 text-zinc-400 group-hover:text-emerald-600 transition-colors" @click.stop="handleEditDetails(order)">
                    <MoreHorizontal class="h-5 w-5" />
                  </Button>
                </TableCell>
              </TableRow>
              <TableRow v-if="paginatedOrders.length === 0">
                <TableCell colspan="8" class="text-center py-8 text-zinc-500">
                  No orders found for this institution.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <!-- Table Pagination Footer -->
          <div v-if="paginatedOrders.length > 0" class="px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-zinc-50 bg-zinc-50/20">
            <div class="flex items-center gap-4 text-xs font-medium text-emerald-600/70">
              <div class="flex items-center gap-2">
                Rows per page:
                <Select v-model="pageSize" class="w-16">
                  <SelectTrigger class="h-8 w-16 border-zinc-200">
                    <SelectValue :placeholder="pageSize.toString()" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5">5</SelectItem>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredOrders.length) }} of {{ filteredOrders.length }}
              </div>
            </div>

            <div class="flex items-center gap-1">
              <Button 
                variant="ghost" 
                size="icon" 
                :disabled="currentPage === 1"
                @click="currentPage--"
                class="hover:bg-emerald-50 text-emerald-600"
              >
                <ChevronLeft class="h-4 w-4" />
              </Button>
              <div class="flex gap-1">
                <Button 
                  v-for="page in totalPages" 
                  :key="page"
                  variant="ghost" 
                  size="sm"
                  :class="currentPage === page ? 'bg-[#44bb2c] text-white' : 'hover:bg-emerald-50 text-emerald-600'"
                  @click="currentPage = page"
                >
                  {{ page }}
                </Button>
              </div>
              <Button 
                variant="ghost" 
                size="icon" 
                :disabled="currentPage === totalPages"
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


    <!-- Modals -->
    <OrderDetailsModal 
      :open="isModalOpen" 
      :order="selectedOrder"
      mode="client" 
      @update:open="isModalOpen = $event"
      @save="handleSaveChanges"
    />
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-inter {
  font-family: 'Inter', sans-serif;
}

.border-magenta-500 {
  border-color: #ff00ff;
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
