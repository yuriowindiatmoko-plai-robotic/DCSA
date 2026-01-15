# 🚀 BULK LOADER CSV - CLAUDE CODE DEVELOPMENT PROMPT

**Project:** Dynamic Catering Order Bulk Loader Feature  
**Tech Stack:** FastAPI (Backend) + Vue.js 3 (Frontend)

## 📋 TABLE OF CONTENTS

1. [Overview & Architecture](#1-overview--architecture)
2. [Data Structure & Sample Mapping](#2-data-structure--sample-mapping)
3. [Backend Development (FastAPI)](#3-backend-development-fastapi)
4. [Frontend Development (Vue.js)](#4-frontend-development-vuejs)
5. [CSV Processing Pipeline](#5-csv-processing-pipeline)
6. [Preview & Validation System](#6-preview--validation-system)
7. [Integration Points](#7-integration-points)
8. [Code Standards & Project Consistency](#8-code-standards--project-consistency)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment Checklist](#10-deployment-checklist)

## 1. OVERVIEW & ARCHITECTURE

### 🎯 Feature Goals

**Primary Objective:** Enable bulk creation of catering orders (DCSA) via CSV upload with:

- ✅ Dynamic staff allocation per institution/event
- ✅ Menu details with flexible syntax
- ✅ Real-time preview before submission
- ✅ Comprehensive validation & error handling
- ✅ Support for 5 CSV sample formats

**Success Criteria:**

- Process 100+ orders in < 5 seconds
- 99%+ validation accuracy
- Zero data loss during import
- User-friendly error feedback
- 100% data integrity

### 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                       │
│  Vue.js 3 Component: BulkLoaderUpload                  │
│  - File Upload (Drag & Drop) or file select            │
│  - CSV Format Selection                                │
│  - Preview Grid (Tabular Format)                       │
│  - Validation Feedback                                 │
│  - Submit & Confirmation                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              FRONTEND PROCESSING LAYER                  │
│  - File Reading (FileReader API)                       │
│  - CSV Parsing (Papa Parse)                            │
│  - Data Mapping (Sample Format → Internal Format)      │
│  - Pre-validation (Client-side)                        │
│  - Transform to Payload                                │
└──────────────────┬──────────────────────────────────────┘
                   │ (API Call: POST /api/orders/bulk/preview)
                   ▼
┌─────────────────────────────────────────────────────────┐
│         BACKEND PROCESSING LAYER (FastAPI)             │
│  - Parse CSV Payload                                   │
│  - Validate Against Rules                              │
│  - Enrich Data (Institution, Menu Lookup)              │
│  - Transform to Order Objects                          │
│  - Return Preview Data + Warnings                      │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   [Preview Shown]     [If OK: Submit]
        │                     │
        │                     ▼
        │          ┌───────────────────────────────┐
        │          │ POST /api/orders/bulk/submit  │
        │          └──────────┬────────────────────┘
        │                     │
        │          ┌──────────▼────────────────────┐
        │          │  Database Insert              │
        │          │  Transaction                  │
        │          └──────────┬────────────────────┘
        │                     │
        └─────────┬───────────┘
                  ▼
         ┌────────────────┐
         │  Success/Error │
         │   Response     │
         └────────────────┘
```

### 📊 Data Flow

```
CSV File (5 formats)
    ↓
Frontend: Parse & Validate
    ↓
API: /bulk/preview (Dry run)
    ↓
User Reviews Preview
    ↓
API: /bulk/submit (If approved)
    ↓
Backend: Process & Insert
    ↓
Database: Persist Orders
    ↓
Response: Confirmation + Order IDs
```

### 🗂️ CSV Sample Formats

#### SAMPLE 1: Standard Orders

no,institution_name,order_date,total_portions,dropping_location_main,sa_dosen_total,sa_dosen_type,sa_dosen_drop_loc,sa_siswa_total,sa_siswa_type,sa_siswa_drop_loc,sa_staff_total,sa_staff_type,sa_staff_drop_loc,sa_satpam_total,sa_satpam_type,sa_satpam_drop_loc,menu_snack_items,menu_beverage_items,menu_heavy_meal_items,special_notes
1,PLAI BMD,2026-01-15,320,KANTIN_PUSAT,20,Box,Pantry,150,Prasmanan,Kantin,135,Prasmanan,Kantin,15,Box,Meja CS,Kue Sus=110; Risoles=50,Kolak=110; Es Teh=20,Nasi Padang=100; Gado-Gado=80,Tanpa MSG
2,SMP Budi Mulia Dua,2026-01-16,333,GEDUNG_UTAMA,15,Box,Pantry Lantai 2,180,Prasmanan,Kantin Utama,120,Prasmanan,Kantin Utama,18,Box,Pos Depan,Sus=100; Donat=100,Kolak=100,Nasi Padang=100; Perkedel=50,
3,SD Budi Mulia Dua Panjen,2026-01-17,450,GEDUNG_B,25,Box,Pantry,200,Prasmanan,Kantin Lantai 1,180,Prasmanan,Kantin Lantai 1,45,Box,Lobby,Brownis=150; Kue Lapis=100,Es Jeruk=120; Teh Hangat=80,Nasi Kuning=150; Lumpia=100,

**Mapping Logic:**

```
institution_name → lookup institution_id from DB
order_date → date parsing (YYYY-MM-DD)
order_type → validate enum (REGULAR, SPECIAL)
staff_allocation[*qty inside] → total_portion
```

#### SAMPLE 2

```csv
no,institution_name,order_date,total_portions,dropping_location_main,sa_umum_total,sa_umum_type,sa_umum_drop_loc,menu_snack_items,menu_beverage_items,menu_heavy_meal_items,special_notes
1,PLAI BMD,2026-01-20,100,LOBBY_UTAMA,100,Box,Resepsionis,Roti Manis=50; Donat=50,Kopi=50; Teh=50,Sandwich=100,
2,SMA Budi Mulia Dua,2026-01-21,150,RUANG RAPAT,150,Prasmanan,Area Rapat,Croissant=75; Kue Ulang Tahun=75,Jus Buah=100; Air Mineral=50,Chicken Rice Bowl=150,Vegetarian untuk 10 orang
3,SMP Budi Mulia Dua,2026-01-22,200,WAREHOUSE,200,Box,Loading Dock,Granola Bar=100; Muffin=100,Minuman Isotonik=200,Burger Ayam=200,
```

#### SAMPLE 3

```csv
no,institution_name,order_date,total_portions,dropping_location_main,sa_dosen_total,sa_dosen_type,sa_dosen_drop_loc,sa_siswa_total,sa_siswa_type,sa_siswa_drop_loc,sa_staff_total,sa_staff_type,sa_staff_drop_loc,sa_satpam_total,sa_satpam_type,sa_satpam_drop_loc,sa_tamu_total,sa_tamu_type,sa_tamu_drop_loc,sa_kasir_total,sa_kasir_type,sa_kasir_drop_loc,menu_snack_items,menu_beverage_items,menu_heavy_meal_items,special_notes
1,PLAI BMD,2026-02-01,800,GEDUNG_REKTORAT,50,Box,Ruang Meeting,400,Prasmanan,Kantin Utama,250,Prasmanan,Kantin Cabang,75,Box,Pos Keamanan,20,Box,VIP Lounge,5,Box,Kasir,Sus Profesional=200; Kue Tradisional=300; Donat Gourmet=300,Kolak Premium=250; Es Teh Manis=300; Air Mineral=250,Tumpeng Ekstra=350; Perkedel Goreng=350; Sambal Matah=100,Event besar - konfirmasi lokasi detail
2,SMA Budi Mulia Dua,2026-02-02,600,LOBBY_UTAMA,30,Box,Ruang Dokter,200,Prasmanan,Kantin Pasien,150,Prasmanan,Kantin Staf,180,Box,Pos Penjaga,40,Box,Area Tunggu,0,,,Bakpia=100; Cookie=150; Brownies=150,Kolak Sehat=180; Es Campur=200; Teh Herbal=220,Bubur Ayam=200; Nasi Goreng Spesial=220; Tahu Goreng=180,Pasien vegetarian: 50 porsi. Pantang kacang untuk 20 orang
3,SMP Budi Mulia Dua,2026-02-03,500,RUANG MEETING,0,,,350,Prasmanan,Kantin,120,Box,Ruang Rapat,30,Box,Lobby,0,,,,,,Biscuit Premium=150; Kue Basah=200,Kopi Arabika=200; Air Mineral=300,Beef Wellington=200; Salmon Teriyaki=300,VIP meeting - presentasi bagus minta
```

#### SAMPLE 4

```csv
no,institution_name,order_date,total_portions,dropping_location_main,sa_peserta_total,sa_peserta_type,sa_peserta_drop_loc,sa_panitia_total,sa_panitia_type,sa_panitia_drop_loc,menu_snack_items,menu_beverage_items,menu_heavy_meal_items,special_notes
1,PLAI BMD,2026-02-10,400,AULA UTAMA,350,Prasmanan,Panggung,50,Box,Ruang Panitia,Kue Sus=150; Risoles=150; Lumpia Goreng=100,Kolak=200; Es Teh=200,Nasi Kuning=300; Sayuran=100,Workshop pelatihan
2,PLAI BMD,2026-02-11,450,AULA UTAMA,400,Prasmanan,Panggung,50,Box,Ruang Panitia,Sus=200; Donat=150; Bakpia=100,Es Jeruk=250; Air Mineral=200,Nasi Goreng=300; Lumpia=150,Lanjutan workshop hari ke-2
3,PLAI BMD,2026-02-12,500,AULA UTAMA,450,Prasmanan,Panggung,50,Box,Ruang Panitia,Kue Lapis=200; Donat Premium=150; Risoles=150,Kolak Spesial=250; Es Cendol=250,Tumpeng=350; Lauk Pauk=150,Penutupan acara - paket spesial
4,PLAI BMD,2026-02-15,350,GEDUNG_B,300,Prasmanan,Ruang Kelas,50,Box,Kantor,Brownies=100; Cookies=150; Kue Sus=100,Jus Buah=200; Air Mineral=150,Nasi Putih=250; Lauk Pauk Beragam=100,Training lanjutan batch ke-2
```

#### SAMPLE 5

```csv
no,institution_name,order_date,total_portions,dropping_location_main,sa_umum_total,sa_umum_type,sa_umum_drop_loc,menu_snack_items,menu_beverage_items,menu_heavy_meal_items
1,SMA Budi Mulia Dua,2026-02-20,250,OUTDOOR,250,Prasmanan,Lapangan,Snack Sehat=150; Buah Segar=100,Air Mineral=250,Nasi Goreng Vegetarian=250
2,SMP Budi Mulia Dua,2026-02-21,80,STUDIO_UTAMA,80,Box,Meja Kerja,Croissant=40; Granola Bar=40,Kopi=50; Air Mineral=30,Pasta Carbonara=80
3,SD Budi Mulia Dua Panjen,2026-02-22,180,BALAI,180,Prasmanan,Area Rapat,Kue Tradisional=100; Roti Manis=80,Kolak=100; Teh=80,Nasi Kuning=180
```

### 🔄 dynamic header staff_allocation

#### menu_details not too dynamic just static pattern from input

staff_allocation handling and detection

```python
import pandas as pd
import re
import json

# Simulasi Data CSV (Perhatikan urutan kolom acak pun tidak masalah)
data = {
    'id': [1, 2],
    # Group Dosen
    'sa_dosen_total': [20, 10],
    'sa_dosen_type': ['Box', 'Prasmanan'],
    'sa_dosen_drop_loc': ['Pantry', 'R. Rapat'],
    # Group Siswa
    'sa_siswa_total': [150, 0], # Baris 2 siswanya 0 (tidak akan masuk json)
    'sa_siswa_type': ['Prasmanan', None],
    'sa_siswa_drop_loc': ['Kantin', None],
    # Group Satpam (Role baru misal)
    'sa_satpam_total': [15, 15],
    'sa_satpam_type': ['Box', 'Box'],
    'sa_satpam_drop_loc': ['Pos 1', 'Pos 2'],

    # Menu (Opsi Mini-Syntax yang kamu setujui)
    'menu_snack_items': ['Kue Sus=110;Risoles=50', 'Tahu=50']
}

df = pd.DataFrame(data)

def parse_dynamic_staff_allocation(row, all_columns):
    allocation = {}

    # 1. Cari semua kolom yang berakhiran "_total" dan berawalan "sa_"
    # Regex: sa_(nama_role)_total
    potential_roles = [col for col in all_columns if col.startswith('sa_') and col.endswith('_total')]

    for col_total in potential_roles:
        # 2. Ekstrak nama role dari header kolom (misal: 'sa_dosen_total' -> 'dosen')
        # Pola: sa_{role}_total
        role_name = col_total.replace('sa_', '').replace('_total', '')

        # Ambil value total
        total_val = row.get(col_total)

        # 3. Validasi: Hanya proses jika total ada dan > 0
        if pd.notna(total_val) and total_val > 0:
            # 4. Cari pasangan kolom type dan loc secara dinamis
            col_type = f"sa_{role_name}_type"
            # col_loc = f"sa_{role_name}_drop_loc" # Atau 'loc' sesuaikan nama kolom
            # Note: Sesuaikan suffix header dengan CSV kamu, misal di sini saya pakai '_loc' sesuai contoh datamu
            col_loc_actual = f"sa_{role_name}_drop_loc"

            allocation[role_name] = {
                "total": int(total_val),
                "serving_type": row.get(col_type),
                "drop_off_location": row.get(col_loc_actual)
            }

    return json.dumps(allocation)

# Pass list kolom df ke fungsi
df['staff_allocation'] = df.apply(lambda row: parse_dynamic_staff_allocation(row, df.columns), axis=1)
```

menu_details handling

```python
def parse_menu_category(cell_value):
    items_list = []
    if not isinstance(cell_value, str) or not cell_value:
        return items_list

    # Misal format: "Kue Sus=110; Risoles=50"
    entries = cell_value.split(';')
    for entry in entries:
        if '=' in entry:
            name, qty = entry.split('=')
            items_list.append({
                "menu": name.strip(),
                "total_qty": int(qty.strip())
            })
    return items_list

# df['snack'] = df['menu_snack_items'].apply(parse_menu_category)
# Lalu gabungkan menjadi satu kolom JSONB menu_details

```

---

## 3. BACKEND DEVELOPMENT (FastAPI)

---

## 4. FRONTEND DEVELOPMENT (Vue.js)

---

## 5. CSV PROCESSING PIPELINE

```
┌──────────────────────────────────────────┐
│  CSV File                                   │
│ (Drag & Drop) or file selection from device │
└────────┬───────────────────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Client-Side Parsing           │
│  - Papa Parse library          │
│  - Normalize headers           │
│  - Validate encoding           │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Format Detection              │
│  - Analyze column count        │
│  - Match known patterns        │
│  - Return format ID            │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Server: PREVIEW Endpoint      │
│  POST /api/orders/bulk/preview
│  - Re-parse CSV                │
│  - Validate structure          │
│  - Transform to objects        │
│  - Validate business rules     │
│  - Return preview + warnings   │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  User Review Preview           │
│  - Display grid with data      │
│  - Show errors/warnings        │
│  - Option to fix or proceed    │
└────────┬───────────────────────┘
         │
         ├─ If Errors: STOP ─────┐
         │                        │
         │ If Valid: Continue     │
         ▼                        │
┌────────────────────────────────┐ │
│  Server: SUBMIT Endpoint       │ │
│  POST /api/orders/bulk/submit
│  - Re-parse & re-validate      │ │
│  - Insert to database (TX)     │ │
│  - Return order IDs            │ │
└────────┬───────────────────────┘ │
         │                          │
         ▼                          │
┌────────────────────────────────┐ │
│  Success Response              │ │
│  - Order IDs created           │ │
│  - Record count                │ │
│  - Total portions              │ │
└────────────────────────────────┘ │
                                   │
                  ┌────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  User Reviews  │
         │  & Can Fix     │
         │  Data          │
         └────────────────┘
```

---

## 6. PREVIEW & VALIDATION SYSTEM

### 🔍 Validation Layers

**Layer 1: CSV Structure** (Frontend & Backend)

- File exists and is readable
- Valid CSV format (header row, columns)
- Encoding compatibility (UTF-8, ISO-8859-1)
- File size < 50MB

**Layer 2: Column Validation** (Backend)

- Required columns present
- Column names match expected format
- No duplicate column names

**Layer 3: Data Validation** (Backend)

- Data type validation (dates, numbers, strings)
- Enum validation (order_type, serving_type)
- Required field validation
- Business logic validation:
  - Institution exists in DB
  - Total portion > 0
  - Date is reasonable
  - Menu items exist
  - Drop locations are valid

**Layer 4: Consistency Validation** (Backend)

- Role allocation matches template
- Staff numbers are reasonable
- Menu totals align with portions (optional)
- No duplicate orders for same date/institution

### 📝 Validation Response Format

```json
{
  "success": true,
  "csv_format": "sample_1",
  "parsed_rows": 3,
  "preview_data": [
    {
      "row_number": 1,
      "institution": "PLAI BMD",
      "order_date": "2026-01-12",
      "total_portion": 320,
      "status": "ok"
    },
    {
      "row_number": 2,
      "institution": "PLAI BMD",
      "order_date": "2026-01-11",
      "total_portion": 320,
      "status": "warning"
    },
    {
      "row_number": 3,
      "institution": "SMP Budi Mulia",
      "order_date": "2026-02-07",
      "total_portion": 333,
      "status": "error"
    }
  ],
  "validation_errors": [
    "Row 3: Institution 'SMP Budi Mulia' not found in database"
  ],
  "validation_warnings": [
    "Row 2: Large order for this institution (320 portions)"
  ],
  "total_portion": 973
}
```

---

## 7. INTEGRATION POINTS

### Frontend → Backend API Calls

```
┌─────────────────────────────┐
│     FRONTEND (Vue.js)       │
└────────────┬────────────────┘
             │
             ├─→ GET /api/orders/bulk/formats
             │   (Get available CSV templates)
             │
             ├─→ POST /api/orders/bulk/preview
             │   (Dry-run CSV validation)
             │   Payload: File (multipart/form-data)
             │   Response: Preview + Errors/Warnings
             │
             └─→ POST /api/orders/bulk/submit
                 (Persist orders to DB)
                 Payload: CSV content + format + confirmation
                 Response: Order IDs + confirmation
```

### Data Flow Through System

```
User Uploads CSV
    ↓
Frontend parses locally (Papa Parse)
    ↓
Sends to: POST /api/orders/bulk/preview
    ↓
Backend:
  - Re-parses CSV (security)
  - Validates structure
  - Transforms to Order objects
  - Validates against DB rules
    ↓
Returns: Preview grid + Errors + Warnings
    ↓
User reviews & clicks "Submit Orders"
    ↓
Frontend sends: POST /api/orders/bulk/submit
    ↓
Backend:
  - Re-parses & re-validates (belt & suspenders)
  - Begins database transaction
  - Inserts all Order objects
  - Commits transaction
    ↓
Returns: Order IDs + confirmation
    ↓
Frontend: Show success message
Database: Orders persisted with status=DRAFT
```

---

## 8. CODE STANDARDS & PROJECT CONSISTENCY

### Backend Standards (FastAPI)

**Style Guide:**

- Follow PEP 8
- Type hints on all functions
- Docstrings for all modules/functions/classes
- Error handling with try/except
- Logging for all major operations

**Directory Structure:**

- api/ for routes and endpoints
- models/ for SQLAlchemy ORM models
- db/ for database configuration
- services/ for business logic
- validators/ for validation rules
- tests/ for unit and integration tests

**Naming Conventions:**

- Functions: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Private methods: \_leading_underscore

**Database:**

- Use SQLAlchemy ORM (no raw SQL)
- Always use transactions for bulk operations
- Include timestamps (created_at, updated_at)
- Soft deletes with is_deleted flag
- Foreign keys with proper relationships

**Error Handling:**

```python
# Custom exceptions in app/core/exceptions.py
class BulkUploadException(Exception):
    pass

class CSVParsingError(BulkUploadException):
    pass

class ValidationError(BulkUploadException):
    pass

class DataTransformError(BulkUploadException):
    pass
```

**Logging:**

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Processing CSV: {format_id}, rows={len(rows)}")
logger.warning(f"Large order detected: {total_portion} portions")
logger.error(f"Database insertion failed: {str(e)}")
```

### Frontend Standards (Vue.js)

**Style Guide:**

- Vue 3 Composition API (not Options API)
- TypeScript for all components
- Tailwind CSS for styling
- Prettier for formatting
- ESLint for linting

**Component Structure:**

```vue
<template>
  <!-- Component HTML -->
</template>

<script setup lang="ts">
// Imports
import { ref, computed } from 'vue'

// Props & emits
interface Props { ... }
defineProps<Props>()
defineEmits<Emits>()

// State
const state = ref(...)

// Computed
const computed_value = computed(() => ...)

// Methods
const handleClick = () => { ... }

// Lifecycle
onMounted(() => { ... })
</script>

<style scoped>
/* Component styles */
</style>
```

**Composable Structure:**

```typescript
export const useComposableName = () => {
  // State
  const state = ref(...)

  // Methods
  const doSomething = () => { ... }

  // Return public API
  return {
    state,
    doSomething
  }
}
```

**Naming Conventions:**

- Components: PascalCase (e.g., `BulkLoaderUpload.vue`)
- Composables: camelCase with `use` prefix (e.g., `useBulkLoader.ts`)
- Files: kebab-case for utilities, camelCase for modules
- CSS classes: kebab-case (e.g., `.bulk-loader-container`)

**Pinia Store:**

```typescript
import { defineStore } from 'pinia'

export const useBulkLoaderStore = defineStore('bulk-loader', () => {
  // State
  const uploadStatus = ref('idle')
  const previewData = ref(null)

  // Actions
  const setUploadStatus = (status: string) => { ... }
  const setPreviewData = (data: any) => { ... }

  // Return
  return {
    uploadStatus,
    previewData,
    setUploadStatus,
    setPreviewData
  }
})
```

---

## 9. TESTING STRATEGY

### Backend Tests

**File:** `tests/test_bulk_upload.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestBulkUploadPreview:
    """Test CSV preview endpoint"""

    def test_preview_sample_1_valid(self):
        """Test preview with valid sample 1 CSV"""
        with open('tests/fixtures/sample_1_valid.csv', 'rb') as f:
            response = client.post(
                '/api/v1/orders/bulk/preview',
                files={'file': f}
            )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['parsed_rows'] == 3
        assert len(data['preview_data']) == 3

    def test_preview_invalid_institution(self):
        """Test preview with non-existent institution"""
        with open('tests/fixtures/sample_1_invalid_institution.csv', 'rb') as f:
            response = client.post(
                '/api/v1/orders/bulk/preview',
                files={'file': f}
            )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is False
        assert len(data['validation_errors']) > 0

    def test_preview_large_portions(self):
        """Test preview with large portions generates warning"""
        # ... test setup
        assert len(data['validation_warnings']) > 0

class TestBulkUploadSubmit:
    """Test CSV submit endpoint"""

    def test_submit_creates_orders(self):
        """Test submit creates orders in database"""
        # Preview first
        preview_response = client.post(...)

        # Then submit
        submit_response = client.post(
            '/api/v1/orders/bulk/submit',
            json={
                'csv_content': '...',
                'confirmed': True
            }
        )

        assert submit_response.status_code == 200
        data = submit_response.json()
        assert data['success'] is True
        assert data['orders_created'] == 3
        assert len(data['order_ids']) == 3

    def test_submit_transaction_rollback_on_error(self):
        """Test transaction rolls back if any error occurs"""
        # ... setup CSV with mixed valid/invalid
        # Verify no orders created on failure
        pass
```

### Frontend Tests

**File:** `src/__tests__/BulkLoaderUpload.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import BulkLoaderUpload from '@/components/BulkLoader/BulkLoaderUpload.vue'
import { bulkLoaderApi } from '@/services/bulkLoaderApi'

vi.mock('@/services/bulkLoaderApi')

describe('BulkLoaderUpload', () => {
  let wrapper: any

  beforeEach(() => {
    wrapper = mount(BulkLoaderUpload)
  })

  it('renders upload component', () => {
    expect(wrapper.find('.bulk-loader-container').exists()).toBe(true)
  })

  it('handles file selection', async () => {
    const file = new File(['test'], 'test.csv', { type: 'text/csv' })
    // ... simulate file input
    expect(wrapper.vm.selectedFile).toBe(file)
  })

  it('calls preview API on Preview button click', async () => {
    vi.mocked(bulkLoaderApi.previewCSV).mockResolvedValue({
      success: true,
      csv_format: 'sample_1',
      parsed_rows: 3,
      preview_data: [...],
      validation_errors: [],
      total_portion: 320
    })

    // ... simulate click
    await wrapper.vm.handlePreview()

    expect(bulkLoaderApi.previewCSV).toHaveBeenCalled()
    expect(wrapper.vm.previewData).toBeDefined()
  })

  it('disables submit button when validation errors exist', () => {
    wrapper.vm.previewData = {
      success: false,
      validation_errors: ['Error 1']
    }

    expect(wrapper.find('button.btn-success').attributes('disabled')).toBeDefined()
  })
})
```

---

## 10. DEPLOYMENT CHECKLIST

### Pre-Deployment Backend

- [ ] All tests passing (`pytest tests/`)
- [ ] Environment variables configured (`.env`)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] CSV validation rules finalized
- [ ] Error messages user-friendly
- [ ] Logging configured
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] API documentation complete (`http://localhost:8001/docs`)
- [ ] Load testing done (100+ concurrent uploads)

### Pre-Deployment Frontend

- [ ] Build succeeds (`pnpm run build`)
- [ ] No TypeScript errors
- [ ] All API endpoints configured
- [ ] Error handling complete
- [ ] Accessibility checked
- [ ] Mobile responsive
- [ ] Performance optimized
- [ ] Environment variables configured
- [ ] Tracking/analytics enabled

### Post-Deployment

- [ ] Monitor error logs
- [ ] Check database query performance
- [ ] Verify file upload sizes
- [ ] Test with real data
- [ ] User acceptance testing
- [ ] Documentation updated
- [ ] Support team trained
- [ ] Rollback plan ready

---

## 📚 FINAL NOTES

This prompt provides complete guidance for implementing the Bulk CSV Loader feature with:

✅ **Backend (FastAPI):**

- Complete project structure
- CSV parsing & transformation logic
- Multi-layer validation system
- Bulk insert with transactions
- Error handling & logging
- Full API documentation

✅ **Frontend (Vue.js):**

- Upload component with drag & drop and file selection
- Real-time CSV parsing (client-side)
- Format selection & auto-detection
- Live preview before submission
- Comprehensive validation feedback
- Confirmation dialog

✅ **Integration:**

- API endpoints fully specified
- Data flow diagrams
- Complete type definitions
- Testing strategy
- Deployment checklist

**Next Steps:**

1. Start with Backend: Setup FastAPI project structure
2. Implement CSV parsers for each sample format
3. Build validation layer with comprehensive rules
4. Create preview & submit endpoints
5. Build Frontend components in parallel
6. Integrate and test end-to-end
7. Deploy and monitor

Good luck with development! 🚀
