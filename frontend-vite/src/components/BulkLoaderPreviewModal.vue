<!-- src/components/BulkLoaderPreviewModal.vue -->
<template>
  <Dialog :open="open" @update:open="$emit('close')">
    <DialogContent class="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
      <DialogHeader>
        <DialogTitle>Bulk Order Upload Preview</DialogTitle>
        <DialogDescription>
          Review {{ previewData?.parsed_rows }} orders before submitting
        </DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-auto">
        <!-- Summary Cards -->
        <div class="grid grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader class="pb-3">
              <CardTitle class="text-sm font-medium text-muted-foreground">
                CSV Format
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold capitalize">
                {{ previewData?.csv_format?.replace('_', ' ') || 'Unknown' }}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="pb-3">
              <CardTitle class="text-sm font-medium text-muted-foreground">
                Total Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">
                {{ previewData?.parsed_rows || 0 }}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader class="pb-3">
              <CardTitle class="text-sm font-medium text-muted-foreground">
                Total Portions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="text-2xl font-bold">
                {{ previewData?.total_portion || 0 }}
              </div>
            </CardContent>
          </Card>
        </div>

        <!-- Validation Errors -->
        <div v-if="hasErrors" class="mb-6">
          <Alert variant="destructive">
            <AlertCircle class="h-4 w-4" />
            <AlertTitle>Validation Errors</AlertTitle>
            <AlertDescription>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li v-for="error in previewData?.validation_errors" :key="error">
                  {{ error }}
                </li>
              </ul>
            </AlertDescription>
          </Alert>
        </div>

        <!-- Validation Warnings -->
        <div v-if="hasWarnings" class="mb-6">
          <Alert>
            <AlertTriangle class="h-4 w-4" />
            <AlertTitle>Warnings</AlertTitle>
            <AlertDescription>
              <ul class="list-disc list-inside mt-2 space-y-1">
                <li v-for="warning in previewData?.validation_warnings" :key="warning">
                  {{ warning }}
                </li>
              </ul>
            </AlertDescription>
          </Alert>
        </div>

        <!-- Preview Table -->
        <div class="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-[60px]">#</TableHead>
                <TableHead>Institution</TableHead>
                <TableHead>Date</TableHead>
                <TableHead class="text-right">Portions</TableHead>
                <TableHead>Drop Location</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="item in previewData?.preview_data"
                :key="item.row_number"
                :class="{ 'bg-destructive/10': item.status === 'error' }"
              >
                <TableCell class="font-medium">{{ item.row_number }}</TableCell>
                <TableCell>{{ item.institution_name }}</TableCell>
                <TableCell>{{ item.order_date }}</TableCell>
                <TableCell class="text-right">{{ item.total_portion }}</TableCell>
                <TableCell>{{ item.dropping_location_food }}</TableCell>
                <TableCell>
                  <Badge :variant="getStatusVariant(item.status)">
                    {{ item.status }}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    @click="selectedItem = item"
                  >
                    <Eye :size="16" />
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>

      <DialogFooter class="border-t pt-4">
        <Button variant="outline" @click="$emit('close')">
          Cancel
        </Button>
        <Button
          variant="default"
          @click="$emit('submit')"
          :disabled="hasErrors || isSubmitting"
        >
          <Loader2 v-if="isSubmitting" class="mr-2 spinner" :size="16" />
          {{ isSubmitting ? 'Creating Orders...' : `Submit ${previewData?.parsed_rows} Orders` }}
        </Button>
      </DialogFooter>
    </DialogContent>

    <!-- Order Details Modal -->
    <Dialog v-model:open="detailsOpen">
      <DialogContent class="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Order Details - Row #{{ selectedItem?.row_number }}</DialogTitle>
        </DialogHeader>

        <div v-if="selectedItem" class="space-y-4">
          <!-- Basic Info -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <Label class="text-sm text-muted-foreground">Institution</Label>
              <p class="font-medium">{{ selectedItem.institution_name }}</p>
            </div>
            <div>
              <Label class="text-sm text-muted-foreground">Order Date</Label>
              <p class="font-medium">{{ selectedItem.order_date }}</p>
            </div>
            <div>
              <Label class="text-sm text-muted-foreground">Total Portions</Label>
              <p class="font-medium">{{ selectedItem.total_portion }}</p>
            </div>
            <div>
              <Label class="text-sm text-muted-foreground">Drop Location</Label>
              <p class="font-medium">{{ selectedItem.dropping_location_food }}</p>
            </div>
          </div>

          <!-- Staff Allocation -->
          <div>
            <Label class="text-sm text-muted-foreground">Staff Allocation</Label>
            <div class="mt-2 border rounded-lg p-3 space-y-2">
              <div
                v-for="(alloc, role) in selectedItem.staff_allocation"
                :key="role"
                class="flex justify-between items-center text-sm"
              >
                <span class="capitalize font-medium">{{ role }}</span>
                <span class="text-muted-foreground">
                  {{ alloc.total }} × {{ alloc.serving_type }} → {{ alloc.drop_off_location }}
                </span>
              </div>
            </div>
          </div>

          <!-- Menu Details -->
          <div v-if="selectedItem.menu_details">
            <Label class="text-sm text-muted-foreground">Menu Details</Label>
            <div class="mt-2 space-y-3">
              <div v-if="selectedItem.menu_details.snack?.length">
                <Label class="text-xs font-medium text-muted-foreground">Snacks</Label>
                <div class="border rounded p-2 mt-1">
                  <div
                    v-for="item in selectedItem.menu_details.snack"
                    :key="item.menu"
                    class="flex justify-between text-sm"
                  >
                    <span>{{ item.menu }}</span>
                    <span class="text-muted-foreground">× {{ item.total_qty }}</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedItem.menu_details.beverages?.length">
                <Label class="text-xs font-medium text-muted-foreground">Beverages</Label>
                <div class="border rounded p-2 mt-1">
                  <div
                    v-for="item in selectedItem.menu_details.beverages"
                    :key="item.menu"
                    class="flex justify-between text-sm"
                  >
                    <span>{{ item.menu }}</span>
                    <span class="text-muted-foreground">× {{ item.total_qty }}</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedItem.menu_details.heavy_meal?.length">
                <Label class="text-xs font-medium text-muted-foreground">Heavy Meals</Label>
                <div class="border rounded p-2 mt-1">
                  <div
                    v-for="item in selectedItem.menu_details.heavy_meal"
                    :key="item.menu"
                    class="flex justify-between text-sm"
                  >
                    <span>{{ item.menu }}</span>
                    <span class="text-muted-foreground">× {{ item.total_qty }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Special Notes -->
          <div v-if="selectedItem.special_notes">
            <Label class="text-sm text-muted-foreground">Special Notes</Label>
            <p class="text-sm mt-1">{{ selectedItem.special_notes }}</p>
          </div>
        </div>

        <DialogFooter>
          <Button @click="detailsOpen = false">Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, AlertTriangle, Eye, Loader2 } from 'lucide-vue-next'
import type { BulkUploadPreviewResponse, BulkUploadPreviewItem } from '@/services/bulkUploadApi'

// Props
interface Props {
  previewData: BulkUploadPreviewResponse | null
  csvContent: string
  isSubmitting: boolean
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  close: []
  submit: []
}>()

// State
const open = computed(() => props.previewData !== null)
const detailsOpen = ref(false)
const selectedItem = ref<BulkUploadPreviewItem | null>(null)

// Computed
const hasErrors = computed(() =>
  props.previewData && props.previewData.validation_errors.length > 0
)

const hasWarnings = computed(() =>
  props.previewData && props.previewData.validation_warnings.length > 0
)

// Methods
function getStatusVariant(status: string): 'default' | 'destructive' | 'secondary' {
  if (status === 'error') return 'destructive'
  if (status === 'warning') return 'secondary'
  return 'default'
}
</script>

<style scoped>
.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
