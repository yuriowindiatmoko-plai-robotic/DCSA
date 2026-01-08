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
import { Save, AlertTriangle, Check, X, MessageSquare } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'

// Props & Emits
const props = defineProps<{
  open: boolean
  order: any
  mode?: 'admin' | 'client'
}>()

const emit = defineEmits(['update:open', 'save', 'approve-edit', 'reject-edit'])

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

interface DistributionItem {
  category: string
  portions: number
  location: string
  type: string
}

// Original Data (Snapshot)
const originalDistribution = ref<DistributionItem[]>([
  { category: 'Staff (Reguler)', portions: 150, location: 'Lobby 1, Floor 2', type: 'Buffet' },
  { category: 'Manager', portions: 25, location: 'Meeting Room A', type: 'Box Meal' },
  { category: 'VIP Guest', portions: 10, location: 'VIP Lounge', type: 'Plated Service' },
])

// Requested Changes (Mutable for Client, Read-only for Admin)
const requestedDistribution = ref<DistributionItem[]>(JSON.parse(JSON.stringify(originalDistribution.value)))

const note = ref('')
const showRejectNote = ref(false)

// Logic to calculate diffs
const getDiff = (original: number, requested: number) => {
  return requested - original
}

const hasChanges = computed(() => {
  return JSON.stringify(originalDistribution.value) !== JSON.stringify(requestedDistribution.value)
})

// Watch for prop changes to update local state
watch(() => props.order, (newOrder) => {
  if (newOrder) {
    formData.value = { ...newOrder }
    // In a real app, we'd fetch specific edit requests here
  }
}, { immediate: true })

const handleSaveClient = () => {
  // Logic to submit edit request
  console.log("Submitting edit request", requestedDistribution.value)
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
               {{ isClientMode ? 'Edit Request' : 'Review Edit Request' }}: {{ order?.orderId || order?.id }}
             </h2>
             <Badge variant="outline" class="bg-blue-50 text-blue-700 border-blue-200">
                Pending Action
             </Badge>
           </div>
           <p class="text-sm text-zinc-500">
             {{ isClientMode ? 'Submit changes for approval.' : 'Review requests submitted by the client.' }}
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
             <h3 class="font-bold text-zinc-500 text-sm uppercase tracking-wide">Original Allocation</h3>
             <Badge variant="secondary" class="bg-zinc-100 text-zinc-600">Approved Oct 10</Badge>
          </div>

          <div class="border rounded-lg overflow-hidden bg-zinc-50/50">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead class="text-right">Qty</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                 <TableRow v-for="(item, idx) in originalDistribution" :key="idx">
                   <TableCell class="font-medium text-zinc-700">{{ item.category }}</TableCell>
                   <TableCell class="text-zinc-600">{{ item.location }}</TableCell>
                   <TableCell class="text-zinc-600">{{ item.type }}</TableCell>
                   <TableCell class="text-right font-medium">{{ item.portions }}</TableCell>
                 </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>

        <!-- Right Column: REQUESTED CHANGES -->
        <div class="space-y-4">
          <div class="flex items-center justify-between border-b pb-2">
             <div class="flex items-center gap-2">
               <h3 class="font-bold text-emerald-600 text-sm uppercase tracking-wide">Requested Changes</h3>
               <div class="bg-emerald-100 p-1 rounded-full">
                 <div class="bg-emerald-500 h-2 w-2 rounded-full"></div>
               </div>
             </div>
             <Badge class="bg-emerald-100 text-emerald-700 border-emerald-200">Pending</Badge>
          </div>

          <div class="border rounded-lg overflow-hidden bg-white ring-4 ring-emerald-50/50">
            <Table>
              <TableHeader class="bg-emerald-50/30">
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead class="text-center w-[100px]">Qty</TableHead>
                  <TableHead class="w-[60px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                 <TableRow v-for="(item, idx) in requestedDistribution" :key="idx">
                   <TableCell class="font-bold text-zinc-900">{{ item.category }}</TableCell>
                   <TableCell class="font-bold text-zinc-900">{{ item.location }}</TableCell>
                   <TableCell class="font-bold text-zinc-900">{{ item.type }}</TableCell>
                   <TableCell>
                      <Input 
                        v-if="isClientMode"
                        v-model="item.portions" 
                        type="number" 
                        class="h-8 w-20 text-center font-bold bg-white border-zinc-300 focus:border-emerald-500 focus:ring-emerald-500" 
                      />
                      <div v-else class="text-center font-bold text-zinc-900">{{ item.portions }}</div>
                   </TableCell>
                   <TableCell>
                      <span 
                        v-if="originalDistribution[idx] && getDiff(originalDistribution[idx].portions, item.portions) !== 0"
                        class="text-xs font-bold px-1.5 py-0.5 rounded-full"
                        :class="getDiff(originalDistribution[idx].portions, item.portions) > 0 ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'"
                      >
                        {{ getDiff(originalDistribution[idx].portions, item.portions) > 0 ? '+' : ''}}{{ getDiff(originalDistribution[idx].portions, item.portions) }}
                      </span>
                   </TableCell>
                 </TableRow>
              </TableBody>
            </Table>
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
