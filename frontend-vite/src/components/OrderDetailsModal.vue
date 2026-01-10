<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Save, AlertTriangle, Check, X, MessageSquare, Plus, Trash2 } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

// Props & Emits
const props = withDefaults(
  defineProps<{
    open: boolean
    order: any
    mode?: 'admin' | 'client'
  }>(),
  {
    mode: 'admin'  // Default to admin mode (read-only)
  }
)

const emit = defineEmits(['update:open', 'save', 'approve-edit', 'reject-edit'])

// Types
interface MenuItem {
  menu: string
  total_qty: number
}

interface MenuDetails {
  heavy_meal?: MenuItem[]
  snack?: MenuItem[]
  beverages?: MenuItem[]
}

interface DistributionItem {
  category: string
  portions: number
  location: string
  type: string
}

// Mock SLA cutoff (Simulate that the SLA was 48h ago)
const isSLAExceeded = ref(true)

// Local State
const formData = ref({
  date: '',
  institution: '',
  portions: 0,
  location: '',
  staff: 0,
  status: '',
})

// Original Data (Snapshot) - loaded from order prop
const originalDistribution = ref<DistributionItem[]>([])

// Requested Changes (Mutable for Client, Read-only for Admin)
const requestedDistribution = ref<DistributionItem[]>([])

// Menu Details State
const originalMenuDetails = ref<MenuDetails>({
  heavy_meal: [],
  snack: [],
  beverages: []
})

const requestedMenuDetails = ref<MenuDetails>({
  heavy_meal: [],
  snack: [],
  beverages: []
})

const note = ref('')
const showRejectNote = ref(false)

// Menu categories for display
const menuCategories = [
  { key: 'heavy_meal', label: 'Heavy Meal', color: 'bg-orange-50 text-orange-700 border-orange-200' },
  { key: 'snack', label: 'Snack', color: 'bg-purple-50 text-purple-700 border-purple-200' },
  { key: 'beverages', label: 'Beverages', color: 'bg-blue-50 text-blue-700 border-blue-200' }
]

// Add menu item helper
const addMenuItem = (category: keyof MenuDetails) => {
  if (!requestedMenuDetails.value[category]) {
    requestedMenuDetails.value[category] = []
  }
  requestedMenuDetails.value[category]!.push({ menu: '', total_qty: 0 })
}

// Remove menu item helper
const removeMenuItem = (category: keyof MenuDetails, index: number) => {
  if (requestedMenuDetails.value[category]) {
    requestedMenuDetails.value[category]!.splice(index, 1)
  }
}

// Add staff allocation item helper
const addStaffAllocation = () => {
  requestedDistribution.value.push({
    category: '',
    portions: 0,
    location: '',
    type: ''
  })
}

// Remove staff allocation item helper
const removeStaffAllocation = (index: number) => {
  requestedDistribution.value.splice(index, 1)
}

// Logic to calculate diffs
const getDiff = (original: number, requested: number) => {
  return requested - original
}

const hasChanges = computed(() => {
  const distributionChanged = JSON.stringify(originalDistribution.value) !== JSON.stringify(requestedDistribution.value)
  const menuChanged = JSON.stringify(originalMenuDetails.value) !== JSON.stringify(requestedMenuDetails.value)
  return distributionChanged || menuChanged
})

// Watch for prop changes to update local state
watch(() => props.order, (newOrder) => {
  if (newOrder) {
    formData.value = { ...newOrder }

    // Load staff_allocation from order data
    if (newOrder.staff_allocation) {
      const allocationItems: DistributionItem[] = []
      for (const [key, value] of Object.entries(newOrder.staff_allocation)) {
        if (typeof value === 'object' && value !== null) {
          allocationItems.push({
            category: key,
            portions: (value as any).total || 0,
            location: (value as any).drop_off_location || '',
            type: (value as any).serving_type || ''
          })
        }
      }
      originalDistribution.value = allocationItems
      requestedDistribution.value = JSON.parse(JSON.stringify(allocationItems))
    } else {
      originalDistribution.value = []
      requestedDistribution.value = []
    }

    // Load menu_details if available
    if (newOrder.menu_details) {
      originalMenuDetails.value = JSON.parse(JSON.stringify(newOrder.menu_details))
      requestedMenuDetails.value = JSON.parse(JSON.stringify(newOrder.menu_details))
    } else {
      originalMenuDetails.value = { heavy_meal: [], snack: [], beverages: [] }
      requestedMenuDetails.value = { heavy_meal: [], snack: [], beverages: [] }
    }
  }
}, { immediate: true })

const handleSaveClient = () => {
  // Convert requestedDistribution to staff_allocation format
  const staffAllocation: Record<string, { total: number; drop_off_location: string; serving_type: string }> = {}
  for (const item of requestedDistribution.value) {
    if (item.category) {
      staffAllocation[item.category] = {
        total: item.portions || 0,
        drop_off_location: item.location || '',
        serving_type: item.type || ''
      }
    }
  }

  // Logic to submit edit request with both staff allocation and menu details
  const changes = {
    order_id: props.order?.order_id || props.order?.id,
    staff_allocation: staffAllocation,
    menu_details: requestedMenuDetails.value
  }
  console.log("Submitting edit request", changes)
  emit('save', changes)
  emit('update:open', false)
}

const handleApprove = () => {
  emit('approve-edit', requestedDistribution.value)
  emit('update:open', false)
}

const handleReject = () => {
  emit('reject-edit', note.value)
  emit('update:open', false)
}

const isClientMode = computed(() => props.mode === 'client')

</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent class="max-w-[1200px] p-0 overflow-hidden bg-white">
      
      <!-- Header Area -->
      <div class="bg-zinc-50 border-b border-zinc-100 p-6 flex items-center justify-between">
        <div>
           <div class="flex items-center gap-3 mb-1">
             <h2 class="text-xl font-bold text-zinc-900">
               Edit Order: {{ order?.order_id?.slice(0, 8) || order?.id?.slice(0, 8) }}...
             </h2>
             <Badge variant="outline" class="bg-blue-50 text-blue-700 border-blue-200">
                {{ order?.status || 'DRAFT' }}
             </Badge>
           </div>
           <p class="text-sm text-zinc-500">
             {{ isClientMode ? 'Submit changes for approval.' : 'Review and approve edit requests.' }}
           </p>
        </div>
        
        <div class="text-right">
           <div class="text-sm font-medium text-zinc-900">{{ formData.institution }}</div>
           <div class="text-xs text-zinc-500">{{ formData.date }}</div>
        </div>
      </div>

      <!-- SLA Warning Banner -->
      <div v-if="isSLAExceeded" class="bg-amber-50 border-b border-amber-100 px-6 py-3 flex items-start gap-3">
        <AlertTriangle class="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
        <div>
          <h4 class="text-sm font-bold text-amber-800">Submitted AFTER SLA</h4>
          <p class="text-xs text-amber-700 mt-0.5">
            This request was submitted past the 48-hour cutoff. There is a high risk of staff shortage for this event.
          </p>
        </div>
      </div>

      <div class="p-6 grid grid-cols-2 gap-8 max-h-[70vh] overflow-y-auto">
        
        <!-- Left Column: ORIGINAL ALLOCATION -->
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b pb-2">
             <h3 class="font-bold text-zinc-500 text-sm uppercase tracking-wide">Current Allocation</h3>
             <Badge variant="secondary" class="bg-zinc-100 text-zinc-600">Current</Badge>
          </div>

          <div class="border rounded-lg overflow-hidden bg-zinc-50/50">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category/Staff</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead class="text-right">Qty</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                 <TableRow v-for="(item, idx) in originalDistribution" :key="idx">
                   <TableCell class="font-medium text-zinc-700">{{ item.category || '-' }}</TableCell>
                   <TableCell class="text-zinc-600">{{ item.location || '-' }}</TableCell>
                   <TableCell class="text-zinc-600">{{ item.type || '-' }}</TableCell>
                   <TableCell class="text-right font-medium">{{ item.portions || 0 }}</TableCell>
                 </TableRow>
                 <TableRow v-if="originalDistribution.length === 0">
                   <TableCell colspan="4" class="text-center py-8 text-zinc-400 text-sm">
                     No current allocation
                   </TableCell>
                 </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>

        <!-- Right Column: REQUESTED CHANGES -->
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b pb-2">
             <div class="flex items-center gap-2">
               <h3 class="font-bold text-emerald-600 text-sm uppercase tracking-wide">Staff Allocation</h3>
               <div class="bg-emerald-100 p-1 rounded-full">
                 <div class="bg-emerald-500 h-2 w-2 rounded-full"></div>
               </div>
             </div>
             <div class="flex items-center gap-2">
               <Badge class="bg-emerald-100 text-emerald-700 border-emerald-200">Pending</Badge>
               <Button
                 variant="ghost"
                 size="sm"
                 @click="addStaffAllocation"
                 class="h-7 px-2 text-xs gap-1 text-emerald-600 hover:bg-emerald-50"
               >
                 <Plus class="h-3 w-3" />
                 Add Staff
               </Button>
             </div>
          </div>

          <div class="border rounded-lg overflow-hidden bg-white ring-4 ring-emerald-50/50">
            <Table>
              <TableHeader class="bg-emerald-50/30">
                <TableRow>
                  <TableHead>Category/Staff</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead class="text-center w-[100px]">Qty</TableHead>
                  <TableHead class="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                 <TableRow v-for="(item, idx) in requestedDistribution" :key="idx" class="group">
                   <TableCell>
                      <Input
                        v-model="item.category"
                        placeholder="Staff name"
                        class="h-8 font-bold bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                      />
                   </TableCell>
                   <TableCell>
                      <Input
                        v-model="item.location"
                        placeholder="Location"
                        class="h-8 font-bold bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                      />
                   </TableCell>
                   <TableCell>
                      <Input
                        v-model="item.type"
                        placeholder="Type"
                        class="h-8 font-bold bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                      />
                   </TableCell>
                   <TableCell>
                      <Input
                        v-model.number="item.portions"
                        type="number"
                        placeholder="0"
                        class="h-8 w-20 text-center font-bold bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500"
                      />
                   </TableCell>
                   <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        @click="removeStaffAllocation(idx)"
                        class="h-8 w-8 text-zinc-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Trash2 class="h-4 w-4" />
                      </Button>
                      <span
                        v-if="!isClientMode && originalDistribution[idx] && getDiff(originalDistribution[idx].portions, item.portions) !== 0"
                        class="text-xs font-bold px-1.5 py-0.5 rounded-full"
                        :class="getDiff(originalDistribution[idx].portions, item.portions) > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
                      >
                        {{ getDiff(originalDistribution[idx].portions, item.portions) > 0 ? '+' : ''}}{{ getDiff(originalDistribution[idx].portions, item.portions) }}
                      </span>
                   </TableCell>
                 </TableRow>
                 <TableRow v-if="requestedDistribution.length === 0">
                   <TableCell colspan="5" class="text-center py-8 text-zinc-400 text-sm">
                     No staff allocation items. Click "Add Staff" to add items.
                   </TableCell>
                 </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>

      </div>

      <!-- Menu Details Section -->
      <div class="border-t border-zinc-100"></div>
      <div class="p-6 bg-zinc-50/30 space-y-6">
        <div class="flex items-center justify-between">
          <h3 class="font-bold text-zinc-700 text-sm uppercase tracking-wide">Menu Details</h3>
          <Badge variant="outline" class="bg-indigo-50 text-indigo-700 border-indigo-200">
            Add-on Items
          </Badge>
        </div>

        <div class="grid grid-cols-1 gap-4">
          <!-- Menu Category Cards -->
          <div v-for="category in menuCategories" :key="category.key" class="border rounded-lg bg-white overflow-hidden">
            <div class="px-4 py-2 border-b flex items-center justify-between" :class="category.color">
              <span class="font-semibold text-xs uppercase">{{ category.label }}</span>
              <Button
                variant="ghost"
                size="sm"
                @click="addMenuItem(category.key as keyof MenuDetails)"
                class="h-6 px-2 text-xs opacity-70 hover:opacity-100"
              >
                <Plus class="h-3 w-3 mr-1" />
                Add Item
              </Button>
            </div>

            <div class="divide-y divide-zinc-50">
              <div
                v-for="(item, idx) in requestedMenuDetails[category.key as keyof MenuDetails]"
                :key="idx"
                class="p-3 flex items-center gap-3 group"
              >
                <div class="flex-1 grid grid-cols-2 gap-3">
                  <div>
                    <label class="text-[10px] font-semibold text-zinc-500 uppercase">Menu Name</label>
                    <Input
                      v-model="item.menu"
                      placeholder="Enter menu name"
                      class="h-8 text-sm"
                    />
                  </div>
                  <div>
                    <label class="text-[10px] font-semibold text-zinc-500 uppercase">Quantity</label>
                    <Input
                      v-model.number="item.total_qty"
                      type="number"
                      placeholder="0"
                      class="h-8 text-sm"
                    />
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  @click="removeMenuItem(category.key as keyof MenuDetails, idx)"
                  class="h-8 w-8 text-zinc-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 class="h-4 w-4" />
                </Button>
              </div>
              <div v-if="!requestedMenuDetails[category.key as keyof MenuDetails]?.length" class="p-4 text-center text-zinc-400 text-sm">
                No items in {{ category.label.toLowerCase() }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer Actions -->
      <DialogFooter class="p-6 bg-zinc-50 border-t border-zinc-100">
        
        <!-- Note Input (Visible when needed specifically) -->
        <div v-if="showRejectNote" class="w-full flex flex-col gap-3 mb-4 animate-in fade-in slide-in-from-bottom-2">
          <Label>Reason / Note</Label>
          <Textarea v-model="note" placeholder="Add a note (optional)..." />
        </div>

        <div class="w-full flex items-center justify-between">
           <Button variant="ghost" @click="emit('update:open', false)">Cancel</Button>
           
           <div class="flex gap-3">
             <template v-if="isClientMode">
                <Button class="bg-emerald-600 hover:bg-emerald-700 text-white gap-2" :disabled="!hasChanges" @click="handleSaveClient">
                  <Save class="h-4 w-4" />
                  Submit Changes
                </Button>
             </template>
             
             <template v-else>
               <Button variant="outline" class="border-rose-200 text-rose-600 hover:bg-rose-50 gap-2" @click="handleReject">
                 <X class="h-4 w-4" />
                 Reject
               </Button>
               <Button variant="secondary" class="bg-amber-100 text-amber-800 hover:bg-amber-200 border border-amber-200 gap-2" @click="showRejectNote = !showRejectNote">
                 <MessageSquare class="h-4 w-4" />
                 Accept with Note
               </Button>
               <Button class="bg-emerald-600 hover:bg-emerald-700 text-white gap-2" @click="handleApprove">
                 <Check class="h-4 w-4" />
                 Approve
               </Button>
             </template>
           </div>
        </div>
      </DialogFooter>

    </DialogContent>
  </Dialog>
</template>
