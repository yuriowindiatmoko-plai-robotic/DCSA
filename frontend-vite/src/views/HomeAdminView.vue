<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  Search,
  Bell,
  MoreHorizontal,
  Star,
  AlertCircle,
  Menu,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  LayoutDashboard,
  Users,
  LogOut,
  ArrowUpDown,
  Loader2,
  Check,
  Trash2,
  RefreshCw,
  FileText,
  Info
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
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
import UserManagementForm from '@/components/UserManagementForm.vue'
import EditNotesDialog from '@/components/EditNotesDialog.vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

// Auth & Router
const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Types - Updated to match backend API response
interface MenuItem {
  menu: string
  total_qty: number
}

interface MenuDetails {
  heavy_meal?: MenuItem[]
  snack?: MenuItem[]
  beverages?: MenuItem[]
}

interface Order {
  order_id: string
  institution_id: string
  institution_name: string
  order_date: string
  total_portion: number
  dropping_location_food: string
  staff_allocation: Record<string, { total: number; drop_off_location: string; serving_type: string }>
  menu_details?: MenuDetails | null
  status: string
}

// Sidebar state
const isSidebarOpen = ref(true)
const toggleSidebar = () => isSidebarOpen.value = !isSidebarOpen.value

// View State
const currentView = ref('dashboard') // 'dashboard' | 'user-management'

// Loading State
const isLoading = ref(true)
const isInitialLoad = ref(true)

// Orders Data from API
const rawOrders = ref<Order[]>([])

// Pagination State
const pageSize = ref(10)
const currentPage = ref(1)
const totalOrders = ref(0)

// Filters State
const todayString = new Date().toISOString().split('T')[0]
const filterDate = ref<string | null>(null)
const filterInstitution = ref('all')
const filterSearch = ref('')
const filterStatus = ref('All Orders')

// Modal State
const isModalOpen = ref(false)
const selectedOrder = ref<Order | null>(null)

// Notes Dialog State
const isNotesDialogOpen = ref(false)
const selectedOrderForNotes = ref<Order | null>(null)
const localNotes = ref('')

// Checkbox Selection State
const selectedOrderIds = ref<Set<string>>(new Set())
const isAllSelected = computed(() =>
  filteredOrders.value.length > 0 && selectedOrderIds.value.size === filteredOrders.value.length
)
const isSomeSelected = computed(() =>
  selectedOrderIds.value.size > 0 && selectedOrderIds.value.size < filteredOrders.value.length
)

// Status Change Confirmation State
const showStatusChangeDialog = ref(false)
const statusChangeOrder = ref<Order | null>(null)
const newStatus = ref('')

// Delete Confirmation State
const showDeleteDialog = ref(false)

// Toggle select all
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedOrderIds.value.clear()
  } else {
    filteredOrders.value.forEach(order => selectedOrderIds.value.add(order.order_id))
  }
}

// Toggle individual selection
const toggleSelectOrder = (orderId: string) => {
  if (selectedOrderIds.value.has(orderId)) {
    selectedOrderIds.value.delete(orderId)
  } else {
    selectedOrderIds.value.add(orderId)
  }
}

// Handle status badge click
const handleStatusClick = (order: Order) => {
  statusChangeOrder.value = order
  newStatus.value = order.status
  showStatusChangeDialog.value = true
}

// Confirm status change
const confirmStatusChange = async () => {
  if (!statusChangeOrder.value) return

  try {
    await axios.put(
      `${API_URL}/api/orders/${statusChangeOrder.value.order_id}/status`,
      { status: newStatus.value },
      {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authStore.token}`
        }
      }
    )
    showStatusChangeDialog.value = false
    fetchOrders()
  } catch (error: any) {
    console.error('Failed to update status:', error)
    alert(`Failed to update status: ${error.response?.data?.detail || error.message}`)
  }
}

// Handle bulk delete
const handleBulkDelete = () => {
  if (selectedOrderIds.value.size === 0) return
  showDeleteDialog.value = true
}

// Confirm bulk delete
const confirmBulkDelete = async () => {
  try {
    await axios.delete(
      `${API_URL}/api/orders/bulk`,
      {
        headers: {
          Authorization: `Bearer ${authStore.token}`
        },
        data: {
          order_ids: Array.from(selectedOrderIds.value)
        }
      }
    )
    showDeleteDialog.value = false
    selectedOrderIds.value.clear()
    fetchOrders()
  } catch (error) {
    console.error('Failed to delete orders:', error)
  }
}

const statusOptions = [
  'All Orders',
  'DRAFT',
  'REQUEST_TO_EDIT',
  'APPROVED_EDITED',
  'APPROVED',
  'REJECTED',
  'NOTED',
  'PROCESSING',
  'COOKING',
  'READY',
  'DELIVERED',
  'ORDERED'
]

// Institution list for filter
const institutions = computed(() => {
  const instNames = rawOrders.value.map(o => o.institution_name)
  return ['all', ...new Set(instNames)]
})

// Search mode: 'list' for normal list view, 'single' for searching by order_id
const searchMode = ref<'list' | 'single'>('list')

// Fetch orders from API (list)
const fetchOrders = async () => {
  try {
    isLoading.value = true
    searchMode.value = 'list'
    const params = new URLSearchParams()

    // Add pagination params
    params.append('skip', ((currentPage.value - 1) * pageSize.value).toString())
    params.append('limit', pageSize.value.toString())

    // Add status filter
    if (filterStatus.value && filterStatus.value !== 'All Orders') {
      params.append('status', filterStatus.value)
    }

    // Add date filter
    if (filterDate.value) {
      params.append('order_date', filterDate.value)
    }

    const response = await axios.get(`${API_URL}/api/orders/`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      },
      params
    })

    rawOrders.value = response.data
    totalOrders.value = response.data.length
  } catch (error) {
    console.error('Failed to fetch orders:', error)
  } finally {
    isLoading.value = false
    isInitialLoad.value = false
  }
}

// Search by order_id (single order)
const searchByOrderId = async (orderId: string) => {
  try {
    isLoading.value = true
    searchMode.value = 'single'

    const response = await axios.get(`${API_URL}/api/orders/${orderId}`, {
      headers: {
        Authorization: `Bearer ${authStore.token}`
      }
    })

    rawOrders.value = [response.data]
    totalOrders.value = 1
  } catch (error) {
    console.error('Failed to search order:', error)
    rawOrders.value = []
    totalOrders.value = 0
  } finally {
    isLoading.value = false
    isInitialLoad.value = false
  }
}

// Handle search on Enter key
const handleSearchKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && filterSearch.value.trim()) {
    currentPage.value = 1
    searchByOrderId(filterSearch.value.trim())
  } else if (event.key === 'Enter' && !filterSearch.value.trim()) {
    // Clear search and fetch all
    currentPage.value = 1
    fetchOrders()
  }
}

// Initial fetch on mount
onMounted(() => {
  fetchOrders()
})

// Watch filter changes and refetch
watch([filterStatus, filterDate, currentPage], () => {
  if (searchMode.value === 'list') {
    fetchOrders()
  }
})

// Handle sort (client-side for now, can be moved to server-side later)
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

// Client-side filtering for institution only (search is now server-side)
const filteredOrders = computed(() => {
  let result = [...rawOrders.value]

  // Institution filter
  if (filterInstitution.value !== 'all') {
    result = result.filter(o => o.institution_name === filterInstitution.value)
  }

  // Sorting
  if (sortField.value) {
    result = result.sort((a, b) => {
      const valA = a[sortField.value!]
      const valB = b[sortField.value!]
      if (valA === valB) return 0

      const modifier = sortOrder.value === 'asc' ? 1 : -1
      if (valA < valB) return -1 * modifier
      return 1 * modifier
    })
  }

  return result
})

// Computed staff count from staff_allocation
const getStaffCount = (staffAllocation: Order['staff_allocation']) => {
  return Object.keys(staffAllocation).length
}

const handleEditDetails = (order: Order) => {
  selectedOrder.value = { ...order }
  isModalOpen.value = true
}

const handleSaved = () => {
  // Refresh orders after successful save
  fetchOrders()
}

const handleEditNotes = (order: Order) => {
  selectedOrderForNotes.value = order
  localNotes.value = order.special_notes || ''
  isNotesDialogOpen.value = true
}

const handleSaveNotes = async (notes: string) => {
  if (!selectedOrderForNotes.value) return

  try {
    await axios.patch(
      `${API_URL}/api/orders/${selectedOrderForNotes.value.order_id}/notes`,
      { special_notes: notes },
      {
        headers: { Authorization: `Bearer ${authStore.token}` }
      }
    )
    isNotesDialogOpen.value = false
    fetchOrders() // Refresh to show updated notes
  } catch (error) {
    console.error('Failed to save notes:', error)
  }
}

// Helpers
const getStatusClasses = (status: string) => {
  switch (status) {
    case 'DRAFT': return 'bg-gray-50 text-gray-600 border-gray-100'
    case 'REQUEST_TO_EDIT': return 'bg-yellow-50 text-yellow-600 border-yellow-100'
    case 'ORDERED': return 'bg-green-50 text-green-600 border-green-100'
    case 'APPROVED_EDITED': return 'bg-blue-50 text-blue-600 border-blue-100'
    case 'APPROVED': return 'bg-teal-50 text-teal-600 border-teal-100'
    case 'REJECTED': return 'bg-red-50 text-red-600 border-red-100'
    case 'NOTED': return 'bg-indigo-50 text-indigo-600 border-indigo-100'
    case 'PROCESSING': return 'bg-cyan-50 text-cyan-600 border-cyan-100'
    case 'COOKING': return 'bg-orange-50 text-orange-600 border-orange-100'
    case 'READY': return 'bg-purple-50 text-purple-600 border-purple-100'
    case 'DELIVERED': return 'bg-emerald-50 text-emerald-600 border-emerald-100'
    default: return 'bg-gray-50 text-gray-500 border-gray-100'
  }
}

const formatStatus = (status: string) => {
  return status.replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, l => l.toUpperCase())
}
</script>

<template>
  <div class="flex h-screen bg-[#F9FAFB] text-zinc-900 font-inter">
    <!-- Sidebar (Existing) -->
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
          <a href="#" @click.prevent="currentView = 'dashboard'" :class="currentView === 'dashboard' ? 'bg-zinc-800/50 text-zinc-200' : 'hover:bg-zinc-800/30 hover:text-white'" class="flex items-center gap-3 px-4 py-3 rounded-lg group transition-colors">
            <LayoutDashboard class="h-5 w-5" />
            <span class="font-medium">Dashboard</span>
          </a>
          <a href="#" @click.prevent="currentView = 'user-management'" :class="currentView === 'user-management' ? 'bg-zinc-800/50 text-zinc-200' : 'hover:bg-zinc-800/30 hover:text-white'" class="flex items-center gap-3 px-4 py-3 rounded-lg group transition-colors">
            <Users class="h-5 w-5" />
            <span class="font-medium">User Management</span>
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
          <h2 class="font-semibold text-lg">{{ currentView === 'dashboard' ? 'Admin / Order Analysis' : 'Admin / User Management' }}</h2>
        </div>
        <div class="flex items-center gap-4">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger as-child>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  class="text-zinc-500 relative"
                  @click="filterStatus = 'Requested Edit'"
                >
                  <Bell class="h-5 w-5" />
                  <span class="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>There was 3 requested edit</p>
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
      <div v-if="currentView === 'dashboard'" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Top Filters Section -->
        <div class="bg-white border border-zinc-100 rounded-xl p-6 shadow-sm space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
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
              <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Institution</label>
              <Select v-model="filterInstitution">
                <SelectTrigger class="h-11 bg-zinc-50 border-zinc-200 focus-visible:ring-0 capitalize">
                  <SelectValue placeholder="All Institutions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="inst in institutions" :key="inst" :value="inst" class="capitalize">
                    {{ inst === 'all' ? 'All Institutions' : inst }}
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
                  placeholder="Search order ID (Press Enter)"
                  @keydown="handleSearchKeydown"
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
                 @click="filterStatus = status; currentPage = 1"
                 class="px-4 py-1.5 rounded-full text-xs font-semibold transition-all border"
                 :class="filterStatus === status
                   ? 'bg-zinc-900 text-white border-zinc-900 shadow-md'
                   : 'bg-zinc-50 text-emerald-600 border-zinc-100 hover:bg-zinc-100'"
               >
                 {{ formatStatus(status) }}
               </button>
             </div>
          </div>

          <!-- Action Bar (shows when items are selected) -->
          <div v-if="selectedOrderIds.size > 0" class="flex items-center justify-between p-4 bg-rose-50 border border-rose-100 rounded-lg">
            <div class="flex items-center gap-3">
              <div class="bg-rose-100 p-2 rounded-full">
                <Check class="h-4 w-4 text-rose-600" />
              </div>
              <span class="text-sm font-semibold text-rose-900">{{ selectedOrderIds.size }} order(s) selected</span>
            </div>
            <div class="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                @click="selectedOrderIds.clear()"
                class="border-rose-200 text-rose-700 hover:bg-rose-100"
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                @click="handleBulkDelete"
                class="gap-2"
              >
                <Trash2 class="h-4 w-4" />
                Delete Selected
              </Button>
            </div>
          </div>
        </div>

        <!-- Table Section -->
        <div class="bg-white border border-zinc-100 rounded-xl shadow-sm overflow-hidden">
          <!-- Loading State -->
          <div v-if="isInitialLoad" class="flex items-center justify-center py-20">
            <div class="flex flex-col items-center gap-3">
              <Loader2 class="h-8 w-8 text-emerald-600 animate-spin" />
              <p class="text-sm text-zinc-500">Loading orders...</p>
            </div>
          </div>

          <!-- Loading Overlay for non-initial loads -->
          <div v-if="isLoading && !isInitialLoad" class="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
            <Loader2 class="h-6 w-6 text-emerald-600 animate-spin" />
          </div>

          <Table v-else>
            <TableHeader class="bg-zinc-50/50">
              <TableRow class="hover:bg-transparent">

                <TableHead class="w-12">
                  <input
                    type="checkbox"
                    :checked="isAllSelected"
                    :indeterminate="isSomeSelected"
                    @change="toggleSelectAll"
                    class="w-4 h-4 text-emerald-600 border-zinc-300 rounded focus:ring-emerald-500 cursor-pointer"
                  />
                </TableHead>
                <TableHead @click="handleSort('order_date')" class="cursor-pointer hover:text-emerald-600 text-[11px] font-bold uppercase tracking-wider text-emerald-600/70 group">
                   <div class="flex items-center gap-1.5">
                     Date
                     <ArrowUpDown class="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                   </div>
                </TableHead>
                <TableHead @click="handleSort('institution_name')" class="cursor-pointer hover:text-emerald-600 text-[11px] font-bold uppercase tracking-wider text-emerald-600/70 group">
                   <div class="flex items-center gap-1.5">
                     Institution
                     <ArrowUpDown class="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                   </div>
                </TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Order ID</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Portions</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Location</TableHead>
                <TableHead class="w-4 flex items-center justify-center pt-3 mr-4">
                  <div class="w-2.5 h-2.5 rounded-full border-2 border-magenta-500"></div>
                </TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Staff</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Status</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Alerts</TableHead>
                <TableHead class="text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Rating</TableHead>
                <TableHead class="text-right text-[11px] font-bold uppercase tracking-wider text-emerald-600/70">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="order in filteredOrders" :key="order.order_id" class="group transition-colors h-16 border-b border-zinc-50">

                <TableCell>
                  <input
                    type="checkbox"
                    :checked="selectedOrderIds.has(order.order_id)"
                    @change="toggleSelectOrder(order.order_id)"
                    class="w-4 h-4 text-emerald-600 border-zinc-300 rounded focus:ring-emerald-500 cursor-pointer"
                  />
                </TableCell>
                <TableCell class="font-medium text-zinc-900">{{ order.order_date }}</TableCell>
                <TableCell>
                  <div class="font-bold text-zinc-900">{{ order.institution_name }}</div>
                </TableCell>
                <TableCell class="text-emerald-600/60 font-medium text-[13px]">
                  {{ order.order_id.slice(0, 8) }}...
                </TableCell>
                <TableCell class="font-bold text-zinc-900">{{ order.total_portion.toLocaleString() }} pax</TableCell>
                <TableCell class="text-zinc-500 font-medium">{{ order.dropping_location_food || '-' }}</TableCell>
                <TableCell></TableCell>
                <TableCell>
                  <span class="text-emerald-600 font-medium">{{ getStaffCount(order.staff_allocation) }} staff</span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    :class="getStatusClasses(order.status)"
                    class="rounded-lg px-3 py-1 font-bold shadow-sm whitespace-nowrap cursor-pointer hover:ring-2 hover:ring-emerald-500 transition-all"
                    @click="handleStatusClick(order)"
                  >
                    {{ formatStatus(order.status) }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <span class="text-zinc-300">-</span>
                </TableCell>
                <TableCell>
                  <div class="flex items-center gap-1 font-bold text-zinc-900">
                    <span>-</span>
                  </div>
                </TableCell>
                <TableCell class="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger as-child>
                      <Button variant="ghost" size="icon" class="h-8 w-8 text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreHorizontal class="h-5 w-5" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem @click="handleEditDetails(order)">
                        <Info class="h-4 w-4 mr-2" />
                        Info
                      </DropdownMenuItem>
                      <DropdownMenuItem @click="handleEditNotes(order)">
                        <FileText class="h-4 w-4 mr-2" />
                        Edit Notes
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
              <TableRow v-if="filteredOrders.length === 0 && !isLoading">
                <TableCell colspan="12" class="text-center py-8 text-zinc-500">
                  No orders found.
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <!-- Table Pagination Footer -->
          <div class="px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-zinc-50 bg-zinc-50/20">
            <div class="flex items-center gap-4 text-xs font-medium text-emerald-600/70">
              <div class="flex items-center gap-2">
                Rows per page:
                <Select v-model="pageSize" @update:model-value="currentPage = 1; fetchOrders()" class="w-16">
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
                {{ filteredOrders.length > 0 ? (currentPage - 1) * pageSize + 1 : 0 }}-{{ (currentPage - 1) * pageSize + filteredOrders.length }} of {{ totalOrders }}
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
                :disabled="filteredOrders.length < pageSize || isLoading"
                @click="currentPage++"
                class="hover:bg-emerald-50 text-emerald-600"
              >
                <ChevronRight class="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- User Management View -->
      <div v-if="currentView === 'user-management'" class="flex-1 overflow-y-auto p-6">
        <UserManagementForm />
      </div>
    </main>


    <!-- Modals -->
    <OrderDetailsModal
      :open="isModalOpen"
      :order="selectedOrder"
      @update:open="isModalOpen = $event"
      @saved="handleSaved"
    />

    <!-- Status Change Confirmation Dialog -->
    <Dialog :open="showStatusChangeDialog" @update:open="showStatusChangeDialog = $event">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Change Order Status</DialogTitle>
          <DialogDescription>
            Are you sure you want to change the status for order {{ statusChangeOrder?.order_id?.slice(0, 8) }}...?
          </DialogDescription>
        </DialogHeader>
        <div class="py-4">
          <label class="text-sm font-medium text-zinc-700 mb-2 block">Select New Status</label>
          <Select v-model="newStatus">
            <SelectTrigger class="w-full">
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DRAFT">Draft</SelectItem>
              <SelectItem value="ORDERED">Ordered</SelectItem>
              <SelectItem value="REQUEST_TO_EDIT">Request To Edit</SelectItem>
              <SelectItem value="APPROVED">Approved</SelectItem>
              <SelectItem value="APPROVED_EDITED">Approved Edited</SelectItem>
              <SelectItem value="REJECTED">Rejected</SelectItem>
              <SelectItem value="NOTED">Noted</SelectItem>
              <SelectItem value="PROCESSING">Processing</SelectItem>
              <SelectItem value="COOKING">Cooking</SelectItem>
              <SelectItem value="READY">Ready</SelectItem>
              <SelectItem value="DELIVERED">Delivered</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showStatusChangeDialog = false">Cancel</Button>
          <Button class="bg-emerald-600 hover:bg-emerald-700" @click="confirmStatusChange">
            <Check class="h-4 w-4 mr-2" />
            Change Status
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Delete Confirmation Dialog -->
    <Dialog :open="showDeleteDialog" @update:open="showDeleteDialog = $event">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Orders</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete {{ selectedOrderIds.size }} order(s)? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div class="py-4">
          <div class="flex items-center gap-3 p-4 bg-rose-50 border border-rose-100 rounded-lg">
            <AlertTriangle class="h-5 w-5 text-rose-600" />
            <div class="text-sm text-rose-700">
              <span class="font-semibold">Warning:</span> Orders will be permanently deleted regardless of their current status.
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="showDeleteDialog = false">Cancel</Button>
          <Button variant="destructive" @click="confirmBulkDelete">
            <Trash2 class="h-4 w-4 mr-2" />
            Delete {{ selectedOrderIds.size }} Order(s)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Edit Notes Dialog -->
    <EditNotesDialog
      :open="isNotesDialogOpen"
      :notes="localNotes"
      @update:open="isNotesDialogOpen = $event"
      @save="handleSaveNotes"
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
