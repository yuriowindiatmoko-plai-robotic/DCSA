<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  LayoutDashboard, 
  ShoppingBag, 
  Users, 
  Settings, 
  LogOut, 
  Search, 
  Bell, 
  ChevronDown,
  Download,
  Plus,
  MoreHorizontal,
  Info,
  Star,
  AlertCircle,
  Menu,
  X
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'vue-sonner'

// Sidebar state
const isSidebarOpen = ref(true)
const toggleSidebar = () => isSidebarOpen.value = !isSidebarOpen.value

// Dummy Data
const orders = ref([
  {
    id: 1,
    date: '2026-01-07',
    institution: 'Grand Hotel Jakarta',
    portions: 150,
    location: 'Central Jakarta',
    staff: 'Rahmat Hidayat',
    status: 'Completed',
    alerts: 'None',
    ratings: 4.8
  },
  {
    id: 2,
    date: '2026-01-07',
    institution: 'Binus University',
    portions: 300,
    location: 'West Jakarta',
    staff: 'Siti Aminah',
    status: 'Pending',
    alerts: 'Low Stock',
    ratings: 0
  },
  {
    id: 3,
    date: '2026-01-06',
    institution: 'Pertamina Tower',
    portions: 120,
    location: 'Central Jakarta',
    staff: 'Budi Santoso',
    status: 'Processing',
    alerts: 'Late Delivery',
    ratings: 4.5
  },
  {
    id: 4,
    date: '2026-01-06',
    institution: 'Siloam Hospital',
    portions: 200,
    location: 'South Jakarta',
    staff: 'Ani Wijaya',
    status: 'Completed',
    alerts: 'None',
    ratings: 5.0
  },
  {
    id: 5,
    date: '2026-01-05',
    institution: 'Telkom Landmark',
    portions: 250,
    location: 'South Jakarta',
    staff: 'Agus Pratama',
    status: 'Cancelled',
    alerts: 'Refused',
    ratings: 0
  }
])

const activeTab = ref('all')
const filteredOrders = computed(() => {
  if (activeTab.value === 'all') return orders.value
  return orders.value.filter(o => o.status.toLowerCase() === activeTab.value)
})

const getStatusVariant = (status: string) => {
  switch (status.toLowerCase()) {
    case 'completed': return 'default' // Using primary/default colors
    case 'pending': return 'secondary'
    case 'processing': return 'outline'
    case 'cancelled': return 'destructive'
    default: return 'secondary'
  }
}

const handleExport = () => {
  toast.success('Exporting data as CSV...')
}

const handleNewOrder = () => {
  toast.info('Opening New Order modal...')
}
</script>

<template>
  <div class="flex h-screen bg-[#F9FAFB] dark:bg-zinc-950 overflow-hidden font-inter">
    <!-- Sidebar -->
    <aside 
      class="bg-[#020817] text-zinc-400 w-64 flex-shrink-0 transition-all duration-300 ease-in-out border-r border-zinc-800 lg:static fixed z-50 h-full"
      :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:hidden'"
    >
      <div class="p-6 h-full flex flex-col">
        <div class="flex items-center gap-3 mb-10">
          <img src="@/assets/dcsa-logo.svg" alt="DCSA Logo" class="h-8 w-auto filter invert brightness-200" />
          <span class="font-bold text-xl text-white tracking-wide">DCSA Admin</span>
          <Button variant="ghost" size="icon" @click="toggleSidebar" class="lg:hidden ml-auto">
            <X class="h-5 w-5" />
          </Button>
        </div>

        <nav class="space-y-1 flex-1">
          <a href="#" class="flex items-center gap-3 px-4 py-3 text-zinc-200 bg-zinc-800/50 rounded-lg group">
            <LayoutDashboard class="h-5 w-5" />
            <span class="font-medium">Dashboard</span>
          </a>
          <a href="#" class="flex items-center gap-3 px-4 py-3 hover:bg-zinc-800/30 hover:text-white rounded-lg transition-colors group">
            <ShoppingBag class="h-5 w-5" />
            <span class="font-medium">Orders</span>
          </a>
          <a href="#" class="flex items-center gap-3 px-4 py-3 hover:bg-zinc-800/30 hover:text-white rounded-lg transition-colors group">
            <Users class="h-5 w-5" />
            <span class="font-medium">Customers</span>
          </a>
          <a href="#" class="flex items-center gap-3 px-4 py-3 hover:bg-zinc-800/30 hover:text-white rounded-lg transition-colors group">
            <Settings class="h-5 w-5" />
            <span class="font-medium">Settings</span>
          </a>
        </nav>

        <div class="mt-auto pt-6 border-t border-zinc-800">
          <Button variant="ghost" class="w-full justify-start gap-3 text-zinc-400 hover:text-red-400 hover:bg-red-400/10 transition-colors">
            <LogOut class="h-5 w-5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col overflow-hidden min-w-0">
      <!-- Header -->
      <header class="h-16 bg-white dark:bg-zinc-950 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between px-6 flex-shrink-0">
        <div class="flex items-center gap-4 flex-1">
          <Button variant="ghost" size="icon" @click="toggleSidebar" class="hidden lg:flex">
            <Menu class="h-5 w-5 text-zinc-500" />
          </Button>
          <div class="relative w-full max-w-md lg:ml-0 -ml-2">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
            <Input 
              placeholder="Search orders, institutions..." 
              class="pl-10 h-10 w-full focus-visible:ring-[#44bb2c]" 
            />
          </div>
        </div>

        <div class="flex items-center gap-4 ml-6">
          <Button variant="ghost" size="icon" class="relative text-zinc-500">
            <Bell class="h-5 w-5" />
            <span class="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-zinc-950"></span>
          </Button>
          
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <Button variant="ghost" class="flex items-center gap-2 px-1 py-1 h-auto hover:bg-zinc-100 rounded-full">
                <Avatar class="h-8 w-8 border-2 border-zinc-200">
                  <AvatarImage src="https://ui.shadcn.com/avatars/02.png" />
                  <AvatarFallback>AD</AvatarFallback>
                </Avatar>
                <div class="hidden md:block text-left mr-2">
                  <p class="text-xs font-semibold text-zinc-900 leading-none">Admin User</p>
                  <p class="text-[10px] text-zinc-500">superuser@dcsa.com</p>
                </div>
                <ChevronDown class="h-4 w-4 text-zinc-400 hidden md:block" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" class="w-56">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Billing</DropdownMenuItem>
              <DropdownMenuItem>Team</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem class="text-red-500">Log out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <!-- Dashboard Body -->
      <div class="flex-1 overflow-y-auto p-6 md:p-8 space-y-8">
        <!-- Page Title & Actions -->
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div class="space-y-1">
            <h1 class="text-2xl md:text-3xl font-bold text-zinc-900 dark:text-white tracking-tight">Order Management</h1>
            <p class="text-zinc-500 text-sm md:text-base">View and manage institutional orders and staffing</p>
          </div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="handleExport" class="gap-2 border-zinc-200">
              <Download class="h-4 w-4" />
              <span>Export Data</span>
            </Button>
            <Button @click="handleNewOrder" class="gap-2 bg-[#44bb2c] hover:bg-[#3da126] text-white">
              <Plus class="h-4 w-4" />
              <span>New Order</span>
            </Button>
          </div>
        </div>

        <!-- Filters & Tabs -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-zinc-200 dark:border-zinc-800 pb-1">
          <Tabs v-model="activeTab" class="w-full sm:w-auto">
            <TabsList class="bg-transparent h-auto p-0 gap-8">
              <TabsTrigger 
                value="all" 
                class="data-[state=active]:border-b-2 data-[state=active]:border-[#44bb2c] data-[state=active]:text-[#44bb2c] rounded-none bg-transparent px-0 pb-3 text-zinc-500 font-medium transition-none border-b-2 border-transparent"
              >
                All Orders
              </TabsTrigger>
              <TabsTrigger 
                value="pending" 
                class="data-[state=active]:border-b-2 data-[state=active]:border-[#44bb2c] data-[state=active]:text-[#44bb2c] rounded-none bg-transparent px-0 pb-3 text-zinc-500 font-medium transition-none border-b-2 border-transparent"
              >
                Pending
              </TabsTrigger>
              <TabsTrigger 
                value="completed" 
                class="data-[state=active]:border-b-2 data-[state=active]:border-[#44bb2c] data-[state=active]:text-[#44bb2c] rounded-none bg-transparent px-0 pb-3 text-zinc-500 font-medium transition-none border-b-2 border-transparent"
              >
                Completed
              </TabsTrigger>
              <TabsTrigger 
                value="cancelled" 
                class="data-[state=active]:border-b-2 data-[state=active]:border-[#44bb2c] data-[state=active]:text-[#44bb2c] rounded-none bg-transparent px-0 pb-3 text-zinc-500 font-medium transition-none border-b-2 border-transparent"
              >
                Cancelled
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <div class="flex items-center gap-2 text-zinc-400 text-sm font-medium pr-1">
             <span class="text-zinc-900 font-semibold">{{ orders.length }}</span> Total Orders
          </div>
        </div>

        <!-- Table Container -->
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-sm">
          <Table>
            <TableHeader class="bg-zinc-50/50 dark:bg-zinc-800/50">
              <TableRow>
                <TableHead class="w-[120px] font-semibold text-zinc-900">Date</TableHead>
                <TableHead class="font-semibold text-zinc-900">Institution</TableHead>
                <TableHead class="font-semibold text-zinc-900">Portions</TableHead>
                <TableHead class="font-semibold text-zinc-900">Location</TableHead>
                <TableHead class="font-semibold text-zinc-900 whitespace-nowrap">Staff in Charge</TableHead>
                <TableHead class="font-semibold text-zinc-900">Status</TableHead>
                <TableHead class="font-semibold text-zinc-900">Alerts</TableHead>
                <TableHead class="font-semibold text-zinc-900">Ratings</TableHead>
                <TableHead class="text-right font-semibold text-zinc-900">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="order in filteredOrders" :key="order.id" class="hover:bg-zinc-50/50 transition-colors">
                <TableCell class="font-medium text-zinc-500">{{ order.date }}</TableCell>
                <TableCell class="font-semibold text-zinc-900">{{ order.institution }}</TableCell>
                <TableCell class="text-zinc-600">{{ order.portions }}</TableCell>
                <TableCell class="text-zinc-500">{{ order.location }}</TableCell>
                <TableCell class="text-zinc-900 font-medium">{{ order.staff }}</TableCell>
                <TableCell>
                  <Badge :variant="getStatusVariant(order.status)" class="font-medium px-2.5 py-0.5 rounded-full">
                    {{ order.status }}
                  </Badge>
                </TableCell>
                <TableCell>
                   <div class="flex items-center gap-1.5" :class="order.alerts !== 'None' ? 'text-amber-600' : 'text-zinc-400'">
                     <AlertCircle v-if="order.alerts !== 'None'" class="h-4 w-4" />
                     <span class="text-xs font-medium">{{ order.alerts }}</span>
                   </div>
                </TableCell>
                <TableCell>
                   <div class="flex items-center gap-1 text-zinc-900 font-semibold">
                      <Star class="h-4 w-4 fill-amber-400 text-amber-400" v-if="order.ratings > 0" />
                      <span>{{ order.ratings > 0 ? order.ratings : '-' }}</span>
                   </div>
                </TableCell>
                <TableCell class="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger as-child>
                      <Button variant="ghost" size="icon" class="h-8 w-8 text-zinc-400 hover:text-zinc-900">
                        <MoreHorizontal class="h-5 w-5" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem class="gap-2">
                        <Info class="h-4 w-4" /> View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem class="gap-2 text-red-500">
                        <AlertCircle class="h-4 w-4" /> Report Issue
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>

          <!-- Pagination Mockup -->
          <div class="px-6 py-4 flex items-center justify-between border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/30">
            <p class="text-sm text-zinc-500">Showing <span class="font-medium text-zinc-900">1</span> to <span class="font-medium text-zinc-900">{{ filteredOrders.length }}</span> of <span class="font-medium text-zinc-900">{{ filteredOrders.length }}</span> results</p>
            <div class="flex gap-2">
              <Button variant="outline" size="sm" disabled>Previous</Button>
              <Button variant="outline" size="sm" disabled>Next</Button>
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
</style>
