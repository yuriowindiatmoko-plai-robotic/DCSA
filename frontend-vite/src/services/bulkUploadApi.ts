// src/services/bulkUploadApi.ts
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const getToken = () => localStorage.getItem('token')

// Bulk upload API interfaces
export interface StaffAllocationItem {
  total: number
  serving_type: string
  drop_off_location: string
}

export interface MenuItem {
  menu: string
  total_qty: number
}

export interface BulkUploadPreviewItem {
  row_number: number
  institution_name: string
  order_date: string
  order_type: string
  total_portion: number
  dropping_location_food: string
  staff_allocation: Record<string, StaffAllocationItem>
  menu_details?: {
    snack?: MenuItem[]
    beverages?: MenuItem[]
    heavy_meal?: MenuItem[]
  }
  special_notes?: string
  status: 'ok' | 'warning' | 'error'
  error_message?: string
}

export interface BulkUploadPreviewResponse {
  success: boolean
  csv_format: string
  parsed_rows: number
  preview_data: BulkUploadPreviewItem[]
  validation_errors: string[]
  validation_warnings: string[]
  total_portion: number
  orders: any[]  // Parsed orders ready for submit
}

export interface BulkUploadSubmitRequest {
  orders: any[]
  confirmed: boolean
}

export interface BulkUploadSubmitResponse {
  success: boolean
  orders_created: number
  order_ids: string[]
  total_portion: number
  message: string
}

/**
 * Preview bulk order upload from CSV file
 */
export async function previewBulkUpload(file: File): Promise<BulkUploadPreviewResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post<BulkUploadPreviewResponse>(
    `${API_URL}/api/orders/bulk/preview`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${getToken()}`
      }
    }
  )

  return response.data
}

/**
 * Submit bulk order upload with parsed orders
 */
export async function submitBulkUpload(orders: any[]): Promise<BulkUploadSubmitResponse> {
  const payload = {
    orders: orders,
    confirmed: true
  }

  console.log('📤 Sending payload to backend:', JSON.stringify(payload, null, 2))

  const response = await axios.post<BulkUploadSubmitResponse>(
    `${API_URL}/api/orders/bulk/submit`,
    payload,
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      }
    }
  )

  return response.data
}
