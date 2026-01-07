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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Save } from 'lucide-vue-next'

// Props & Emits
const props = defineProps<{
  open: boolean
  order: any
  mode?: 'admin' | 'client'
}>()

const emit = defineEmits(['update:open', 'save'])

// Local State
const formData = ref({
  date: '',
  institution: '',
  portions: 0,
  location: '',
  staff: 0,
  status: '',
})

// Distribution Data (Mocked based on user request)
const distributionData = ref([
  { category: 'Satpam', portions: 15, location: 'Meja CS', type: 'Box' },
  { category: 'Dosen', portions: 20, location: 'Pantry', type: 'Box' },
  { category: 'Staff', portions: 65, location: 'Kantin', type: 'Prasmanan' },
  { category: 'Siswa', portions: 150, location: 'Kantin', type: 'Prasmanan' },
  { category: 'Guru', portions: 70, location: 'Kantin', type: 'Prasmanan' },
])

// Watch for prop changes to update local state
watch(() => props.order, (newOrder) => {
  if (newOrder) {
    formData.value = { ...newOrder }
  }
}, { immediate: true })

// Total Portions Validation
const totalDistributionPortions = computed(() => {
  return distributionData.value.reduce((sum, item) => sum + Number(item.portions), 0)
})

const isReadOnly = computed(() => {
  if (props.mode === 'client') {
    return ['Cooking', 'Delivered'].includes(formData.value.status)
  }
  return false
})

const isClientMode = computed(() => props.mode === 'client')

// Watch for distribution changes to auto-update total portions in client mode
watch(distributionData, (newData) => {
  if (isClientMode.value) {
    const total = newData.reduce((sum, item) => sum + Number(item.portions), 0)
    formData.value.portions = total
  }
}, { deep: true })

const handleSave = () => {
  // Emit updated data back to parent
  emit('save', {
    ...formData.value,
    id: props.order.id
  })
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent class="sm:max-w-[700px] p-0 overflow-hidden bg-white">
      <!-- Header / Banner Area -->
      <div class="bg-zinc-50 border-b border-zinc-100 p-6 flex flex-col gap-4">
        <div class="flex items-center justify-between">
           <div class="flex items-center gap-3">
             <div class="h-10 w-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 font-bold text-lg">
               DK
             </div>
             <div>
               <h2 class="text-lg font-bold text-zinc-900">{{ mode === 'client' ? 'Client DK' : 'Admin DK' }}</h2>
               <p class="text-xs text-zinc-500">Edit Details & Approval</p>
             </div>
           </div>
           <!-- Status Badge -->
           <div class="px-3 py-1 rounded-full text-xs font-bold border"
             :class="{
               'bg-yellow-50 text-yellow-600 border-yellow-100': formData.status === 'Requested Edit',
               'bg-green-50 text-green-600 border-green-100': formData.status === 'Ordered',
               'bg-blue-50 text-blue-600 border-blue-100': formData.status === 'Edited',
               'bg-orange-50 text-orange-600 border-orange-100': formData.status === 'Cooking',
               'bg-emerald-50 text-emerald-600 border-emerald-100': formData.status === 'Delivered'
             }"
           >
             {{ formData.status }}
           </div>
        </div>
      </div>

      <div class="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
        <!-- Main Form Grid -->
        <div class="grid grid-cols-2 gap-6">
          <div class="space-y-2">
            <Label>Date</Label>
            <Input v-model="formData.date" type="date" class="bg-zinc-50/50" :disabled="isClientMode || isReadOnly" />
          </div>
          <div class="space-y-2">
            <Label>Institution</Label>
            <Select v-model="formData.institution" :disabled="isClientMode || isReadOnly">
              <SelectTrigger class="bg-zinc-50/50">
                <SelectValue placeholder="Select Institution" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="VHS">VHS</SelectItem>
                <SelectItem value="PLAI">PLAI</SelectItem>
                <SelectItem value="SD BMD Panjen">SD BMD Panjen</SelectItem>
                <SelectItem value="SMP BMD">SMP BMD</SelectItem>
                <SelectItem value="SMA BMD">SMA BMD</SelectItem>
                <SelectItem value="Binus Univ">Binus Univ</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="space-y-2">
            <Label>Total Portions</Label>
            <Input v-model="formData.portions" type="number" class="bg-zinc-50/50" :disabled="isClientMode || isReadOnly" />
          </div>
          <div class="space-y-2">
            <Label>Staff Count</Label>
            <Input v-model="formData.staff" type="number" class="bg-zinc-50/50" :disabled="isClientMode || isReadOnly" />
          </div>
           <div class="space-y-2 col-span-2">
            <Label>Location</Label>
            <Input v-model="formData.location" class="bg-zinc-50/50" :disabled="isClientMode || isReadOnly" />
          </div>
          <div class="space-y-2 col-span-2">
            <Label>Status</Label>
             <Select v-model="formData.status" :disabled="isClientMode || isReadOnly">
              <SelectTrigger class="bg-zinc-50/50">
                <SelectValue placeholder="Select Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Requested Edit">Requested Edit</SelectItem>
                <SelectItem value="Ordered">Ordered</SelectItem>
                <SelectItem value="Edited">Edited</SelectItem>
                <SelectItem value="Cooking">Cooking</SelectItem>
                <SelectItem value="Delivered">Delivered</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <!-- Distribution Table -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <Label class="text-base font-bold">Staff Category Distribution</Label>
            <span class="text-xs text-zinc-500">Calculated: <span :class="totalDistributionPortions !== Number(formData.portions) ? 'text-amber-500 font-bold' : 'text-emerald-600 font-bold'">{{ totalDistributionPortions }}</span> / {{ formData.portions }}</span>
          </div>
          
          <div class="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader class="bg-zinc-50">
                <TableRow>
                  <TableHead>Kategori User</TableHead>
                  <TableHead class="w-[100px]">Total Porsi</TableHead>
                  <TableHead>Lokasi</TableHead>
                  <TableHead>Tipe</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="(item, index) in distributionData" :key="index">
                  <TableCell class="font-medium">{{ item.category }}</TableCell>
                  <TableCell>
                    <Input v-model="item.portions" type="number" class="h-8 w-20" :disabled="isReadOnly" />
                  </TableCell>
                  <TableCell>
                     <Input v-model="item.location" class="h-8" :disabled="isReadOnly" />
                  </TableCell>
                  <TableCell>
                     <Select v-model="item.type" :disabled="isReadOnly">
                      <SelectTrigger class="h-8 w-[110px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Box">Box</SelectItem>
                        <SelectItem value="Prasmanan">Prasmanan</SelectItem>
                      </SelectContent>
                    </Select>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </div>
      </div>

      <DialogFooter class="p-6 bg-zinc-50 border-t border-zinc-100 gap-3">
        <Button variant="outline" @click="emit('update:open', false)" class="text-rose-500 hover:text-rose-600 hover:bg-rose-50 border-rose-200">
          Cancel
        </Button>
        <Button v-if="!isReadOnly" class="bg-emerald-500 hover:bg-emerald-600 text-white gap-2" @click="handleSave">
          <Save class="h-4 w-4" />
          Save Changes
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
