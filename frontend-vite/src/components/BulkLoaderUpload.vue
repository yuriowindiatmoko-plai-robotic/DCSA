<!-- src/components/BulkLoaderUpload.vue -->
<template>
  <div class="bulk-loader-container">
    <!-- Upload Area -->
    <div
      class="upload-area"
      :class="{ 'drag-over': isDragOver, 'has-file': selectedFile }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInputRef"
        type="file"
        accept=".csv"
        class="hidden-input"
        @change="handleFileSelect"
      />

      <div v-if="!selectedFile" class="upload-prompt">
        <Upload class="upload-icon" :size="48" />
        <p class="upload-text">
          Drag & drop your CSV file here, or click to browse
        </p>
        <p class="upload-hint">Supported formats: Sample 1-5 CSV files</p>
      </div>

      <div v-else class="file-info">
        <FileSpreadsheet class="file-icon" :size="32" />
        <div class="file-details">
          <p class="file-name">{{ selectedFile.name }}</p>
          <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          class="remove-btn"
          @click.stop="removeFile"
        >
          <X :size="16" />
        </Button>
      </div>
    </div>

    <!-- Action Buttons -->
    <div v-if="selectedFile" class="action-buttons">
      <Button
        variant="outline"
        @click="removeFile"
        :disabled="isLoading"
      >
        Cancel
      </Button>
      <Button
        @click="handlePreview"
        :disabled="isLoading"
        class="preview-btn"
      >
        <Loader2 v-if="isLoading" class="spinner" :size="16" />
        {{ isLoading ? 'Processing...' : 'Preview Orders' }}
      </Button>
    </div>

    <!-- Preview Modal -->
    <BulkLoaderPreviewModal
      v-if="showPreviewModal"
      :preview-data="previewData"
      :csv-content="csvContent"
      :is-submitting="isSubmitting"
      @close="showPreviewModal = false"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileSpreadsheet, X, Loader2 } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { previewBulkUpload, submitBulkUpload } from '@/services/bulkUploadApi'
import type { BulkUploadPreviewResponse } from '@/services/bulkUploadApi'
import { toast } from 'vue-sonner'
import BulkLoaderPreviewModal from './BulkLoaderPreviewModal.vue'

// State
const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const isDragOver = ref(false)
const isLoading = ref(false)
const isSubmitting = ref(false)
const csvContent = ref('')
const previewData = ref<BulkUploadPreviewResponse | null>(null)
const showPreviewModal = ref(false)

// Drag and drop handlers
function handleDragOver() {
  isDragOver.value = true
}

function handleDragLeave() {
  isDragOver.value = false
}

function handleDrop(e: DragEvent) {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file && file.name.endsWith('.csv')) {
      selectedFile.value = file
      readCSVContent(file)
    } else {
      toast.error('Please select a CSV file')
    }
  }
}

// File input handlers
function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file) {
      selectedFile.value = file
      readCSVContent(file)
    }
  }
}

function removeFile() {
  selectedFile.value = null
  csvContent.value = ''
  previewData.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// Read CSV content
function readCSVContent(file: File) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target?.result as string
    csvContent.value = text
  }
  reader.onerror = () => {
    toast.error('Failed to read file')
  }
  reader.readAsText(file)
}

// Preview handler
async function handlePreview() {
  if (!selectedFile.value) {
    toast.error('Please select a file first')
    return
  }

  isLoading.value = true

  try {
    const result = await previewBulkUpload(selectedFile.value)

    if (result.success) {
      previewData.value = result
      showPreviewModal.value = true
      toast.success(`Parsed ${result.parsed_rows} orders successfully`)
    } else {
      previewData.value = result
      showPreviewModal.value = true
      toast.warning(`Preview loaded with ${result.validation_errors.length} errors`)
    }
  } catch (error: any) {
    console.error('Preview failed:', error)
    toast.error(error.response?.data?.detail || 'Failed to preview CSV file')
  } finally {
    isLoading.value = false
  }
}

// Submit handler
async function handleSubmit() {
  if (!csvContent.value) {
    toast.error('No CSV content to submit')
    return
  }

  isSubmitting.value = true

  try {
    const result = await submitBulkUpload(csvContent.value)

    if (result.success) {
      toast.success(`Successfully created ${result.orders_created} orders!`)
      showPreviewModal.value = false
      removeFile()
    } else {
      toast.error('Failed to create orders')
    }
  } catch (error: any) {
    console.error('Submit failed:', error)
    toast.error(error.response?.data?.detail || 'Failed to submit orders')
  } finally {
    isSubmitting.value = false
  }
}

// Utility functions
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.bulk-loader-container {
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.upload-area {
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #f8fafc;
}

.upload-area:hover {
  border-color: #3b82f6;
  background-color: #eff6ff;
}

.upload-area.drag-over {
  border-color: #3b82f6;
  background-color: #dbeafe;
  transform: scale(1.01);
}

.upload-area.has-file {
  border-color: #10b981;
  background-color: #f0fdf4;
  cursor: default;
}

.upload-area.has-file:hover {
  transform: none;
}

.hidden-input {
  display: none;
}

.upload-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  color: #94a3b8;
}

.upload-text {
  font-size: 16px;
  font-weight: 500;
  color: #475569;
  margin: 0;
}

.upload-hint {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
}

.file-icon {
  color: #10b981;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  text-align: left;
}

.file-name {
  font-weight: 500;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.file-size {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.remove-btn {
  flex-shrink: 0;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.preview-btn {
  min-width: 140px;
}

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
