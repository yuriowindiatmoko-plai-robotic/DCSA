<script setup lang="ts">
import { ref, watch } from 'vue'
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
import { Textarea } from '@/components/ui/textarea'

// Props & Emits
const props = defineProps<{
  open: boolean
  notes?: string
}>()

const emit = defineEmits(['update:open', 'save'])

// Local State
const localNotes = ref(props.notes || '')

// Watch for prop changes
watch(() => props.notes, (newNotes) => {
  localNotes.value = newNotes || ''
})

const handleSave = () => {
  emit('save', localNotes.value)
  emit('update:open', false)
}

const handleCancel = () => {
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent class="sm:max-w-md">
      <DialogHeader>
        <DialogTitle>Edit Special Notes</DialogTitle>
        <DialogDescription>
          Add or edit special notes for this order.
        </DialogDescription>
      </DialogHeader>

      <div class="py-4">
        <Label for="notes">Notes</Label>
        <Textarea
          id="notes"
          v-model="localNotes"
          placeholder="Enter special notes..."
          rows="5"
          class="mt-2"
        />
      </div>

      <DialogFooter>
        <Button variant="outline" @click="handleCancel">
          Cancel
        </Button>
        <Button @click="handleSave" class="bg-emerald-600 hover:bg-emerald-700">
          Save Notes
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
