# app/schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    CLIENT_ADMIN = "CLIENT_ADMIN"
    DK_ADMIN = "DK_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    institution_name: str  # Will lookup institution_id by name
    role: UserRole

    @validator("username")
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        if v.lower() in ["admin", "root", "system"]:
            raise ValueError("Username not allowed")
        return v

    @validator("password")
    def validate_password(cls, v: str) -> str:
        if len(v.strip()) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v.strip()


class UserRead(BaseModel):
    id: UUID
    username: str
    email: str
    role: str
    status: str
    institution_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
