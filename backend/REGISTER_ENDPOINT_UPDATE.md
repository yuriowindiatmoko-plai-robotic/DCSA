# ✅ Register Endpoint Update - Complete

## Summary

Successfully updated the `/api/auth/register` endpoint to work with the new database schema including `institutions` and enhanced `users` tables.

---

## Changes Made

### 1. **Created `Institution` Model**

**File:** `app/models/institution.py`

- Maps to the `institutions` table
- Includes all columns: `institution_id`, `name`, `type`, `total_users`, `contact_email`, `contact_person`, `status`, `created_at`, `updated_at`

### 2. **Updated `User` Model**

**File:** `app/models/user.py`

Added new columns:

- ✅ `email` (unique, required)
- ✅ `institution_id` (FK to institutions)
- ✅ `role` (CLIENT_ADMIN, DK_ADMIN, SUPER_ADMIN)
- ✅ `status` (ACTIVE, INACTIVE, SUSPENDED)
- ✅ `created_at`, `updated_at`, `last_login` (timestamps)
- ✅ Relationship to `Institution` model

### 3. **Updated Schemas**

**File:** `app/schemas/user.py`

**UserCreate:**

- Added `email: EmailStr` with validation
- Added `institution_name: str` (user submits name, backend looks up ID)
- Added `role: UserRole` enum (CLIENT_ADMIN, DK_ADMIN, SUPER_ADMIN)
- Added validators for username and password

**UserRead:**

- Added `email`, `role`, `status`, `institution_id`, `created_at`
- Changed `orm_mode = True` (Pydantic v1 compatibility)

### 4. **Updated Auth Router**

**File:** `app/routers/auth.py`

**Register Endpoint:**

- ✅ Looks up institution by name → gets `institution_id`
- ✅ Validates username doesn't exist
- ✅ Validates email doesn't exist
- ✅ Creates user with all new fields
- ✅ Sets default status to 'ACTIVE'

**Login Endpoint:**

- ✅ Updates `last_login` timestamp
- ✅ Returns enhanced response with: `username`, `email`, `role`, `institution_id`

---

## API Usage

### Register a New User

**Endpoint:** `POST /api/auth/register`

**Request Body:**

```json
{
  "username": "john_doe",
  "email": "john@plai.ac.id",
  "password": "securepass123",
  "institution_name": "PLAI BMD",
  "role": "CLIENT_ADMIN"
}
```

**Success Response (201):**

```json
{
  "id": "b64126de-cb16-4162-b411-f1afa4db2c4a",
  "username": "john_doe",
  "email": "john@plai.ac.id",
  "role": "CLIENT_ADMIN",
  "status": "ACTIVE",
  "institution_id": "a539afa0-d102-4589-9cab-12c901dcd606",
  "created_at": "2026-01-08T06:45:21.051379"
}
```

**Error Responses:**

- `404`: Institution not found
- `400`: Username already exists
- `400`: Email already exists
- `422`: Validation error (invalid email, short password, etc.)

---

### Login

**Endpoint:** `POST /api/auth/login`

**Request Body (form-urlencoded):**

```
username=john_doe&password=securepass123
```

**Success Response:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "uuid": "b64126de-cb16-4162-b411-f1afa4db2c4a",
  "username": "john_doe",
  "email": "john@plai.ac.id",
  "role": "CLIENT_ADMIN",
  "institution_id": "a539afa0-d102-4589-9cab-12c901dcd606"
}
```

---

## Validation Rules

### Username

- ✅ Minimum 3 characters
- ✅ No spaces allowed
- ✅ Cannot be: "admin", "root", "system"

### Password

- ✅ Minimum 6 characters

### Email

- ✅ Valid email format (validated by Pydantic EmailStr)

### Role

- ✅ Must be one of: `CLIENT_ADMIN`, `DK_ADMIN`, `SUPER_ADMIN`

### Institution

- ✅ Must exist in the database (lookup by exact name match)

---

## Test Results ✅

All tests passed successfully:

1. ✅ **Valid registration** - User created successfully
2. ✅ **Invalid institution** - Returns 404 error
3. ✅ **Duplicate username** - Returns 400 error
4. ✅ **Duplicate email** - Returns 400 error
5. ✅ **Enhanced login** - Returns user info (email, role, institution_id)

---

## Available Institutions

Based on your sample data:

- `PLAI BMD` (UNIVERSITY)
- `SMA Budi Mulia Dua` (SCHOOL_HIGH)
- `SMP Budi Mulia Dua` (SCHOOL_MIDDLE)
- `SD Budi Mulia Dua Panjen` (SCHOOL_PRIMARY)
- `Yayasan BMD` (FOUNDATION)
- `Dapur Kuliner BMD` (BUSINESS_ENTITY_FOUNDATION)

---

## Notes

- Using **Pydantic v1.10.9** (not v2) - validators use `@validator` decorator
- Institution lookup is **case-sensitive** - must match exact name
- Default user status is `ACTIVE`
- `last_login` is updated on every successful login
