# app/schemas/feedback_rating.py
from pydantic import BaseModel, Field, root_validator
from datetime import date, datetime
from typing import Optional, Dict, List, Any
from uuid import UUID


class MenuRatingItem(BaseModel):
    """Single menu item with rating"""
    menu: str
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")


class MenuRatings(BaseModel):
    """Menu ratings organized by category"""
    heavy_meal: List[MenuRatingItem] = []
    snack: List[MenuRatingItem] = []
    beverages: List[MenuRatingItem] = []


class FeedbackRatingBase(BaseModel):
    """Base feedback rating schema"""
    order_id: UUID
    meal_time: str = Field(..., description="Meal time (e.g., 'Makan Pagi', 'Makan Siang', 'Makan Malam')")
    date_of_feedback: date
    user_type: str = Field(..., description="User type (e.g., 'STAFF', 'STUDENT', 'TEACHER')")
    is_anonymous: bool = False
    spice_level: Optional[str] = Field(None, description="Spice level preference")
    additional_comments: Optional[str] = Field(None, max_length=500, description="Additional comments")
    menu_ratings: MenuRatings

    @root_validator
    def validate_user_name(cls, values):
        """Ensure user_name is provided if not anonymous"""
        is_anonymous = values.get("is_anonymous", False)
        user_name = values.get("user_name")

        # If user_name is explicitly provided in the values, use it
        # Otherwise, require it if not anonymous
        if not is_anonymous and "user_name" in values and not values.get("user_name"):
            raise ValueError("user_name is required when is_anonymous is False")

        return values


class FeedbackRatingCreate(FeedbackRatingBase):
    """Schema for creating feedback rating"""
    user_name: Optional[str] = Field(None, description="User name (required if not anonymous)")

    @root_validator
    def validate_user_name_required(cls, values):
        """Ensure user_name is provided if not anonymous"""
        is_anonymous = values.get("is_anonymous", False)
        user_name = values.get("user_name")

        if not is_anonymous and not user_name:
            raise ValueError("user_name is required when is_anonymous is False")

        return values


class FeedbackRatingUpdate(BaseModel):
    """Schema for updating feedback rating"""
    meal_time: Optional[str] = None
    user_type: Optional[str] = None
    is_anonymous: Optional[bool] = None
    spice_level: Optional[str] = None
    additional_comments: Optional[str] = None
    menu_ratings: Optional[MenuRatings] = None


class FeedbackRatingRead(BaseModel):
    """Schema for reading feedback rating"""
    id: UUID
    institution_id: UUID
    order_id: UUID
    meal_time: str
    date_of_feedback: date
    user_type: str
    user_name: Optional[str]
    is_anonymous: bool
    spice_level: Optional[str]
    additional_comments: Optional[str]
    menu_ratings: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True


class OrderForRatingResponse(BaseModel):
    """Response for order data used in rating form"""
    order: Dict[str, Any]
    today_date_wib: str
    meal_time: Optional[str] = None


class FeedbackRatingListResponse(BaseModel):
    """Response for paginated feedback list"""
    feedbacks: List[FeedbackRatingRead]
    total: int
    page: int
    page_size: int
