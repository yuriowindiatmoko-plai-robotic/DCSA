# app/routers/feedback_ratings.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
import pytz

from app.db.engine import SessionLocal
from app.models.feedback_rating import FeedbackRating
from app.models.order import Order
from app.models.institution import Institution
from app.schemas.feedback_rating import (
    FeedbackRatingCreate,
    FeedbackRatingRead,
    FeedbackRatingListResponse,
    OrderForRatingResponse,
)

router = APIRouter()

# WIB Timezone
WIB_TZ = pytz.timezone("Asia/Jakarta")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_date_wib() -> date:
    """Get current date in WIB (GMT+7) timezone"""
    utc_now = datetime.utcnow()
    wib_now = utc_now.replace(tzinfo=pytz.UTC).astimezone(WIB_TZ)
    return wib_now.date()


# GET /api/rating-food/{institution_id} - Fetch today's order for rating form
@router.get("/{institution_id}", response_model=OrderForRatingResponse)
def get_order_for_rating(
    institution_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Fetch today's order for the rating form.
    Returns formatted menu items for the frontend.
    """
    today_wib = get_current_date_wib()

    # Get today's order for the institution
    query = (
        select(Order)
        .options(joinedload(Order.institution))
        .where(
            Order.institution_id == institution_id,
            Order.order_date == today_wib,
            Order.is_deleted == False,
        )
        .order_by(Order.created_at.desc())
    )

    order = db.execute(query).scalars().unique().first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail=f"No order found for today ({today_wib}) for this institution"
        )

    # Format response
    order_dict = {
        "order_id": str(order.order_id),
        "institution_id": str(order.institution_id),
        "institution_name": order.institution.name if order.institution else None,
        "order_date": order.order_date.isoformat(),
        "menu_details": order.menu_details or {},
    }

    # Determine meal time based on menu or default to lunch
    meal_time = None
    if order.menu_details:
        # You can customize this logic based on your needs
        if order.menu_details.get("heavy_meal"):
            meal_time = "Makan Siang"  # Default lunch

    return OrderForRatingResponse(
        order=order_dict,
        today_date_wib=today_wib.isoformat(),
        meal_time=meal_time,
    )


# POST /api/rating-food/{institution_id} - Submit feedback rating
@router.post("/{institution_id}", response_model=FeedbackRatingRead, status_code=status.HTTP_201_CREATED)
def submit_feedback_rating(
    institution_id: UUID,
    feedback_data: FeedbackRatingCreate,
    db: Session = Depends(get_db),
):
    """
    Submit feedback rating for an order.
    Validates that the order exists and belongs to the institution.
    """
    # Verify the order exists and belongs to the institution
    order = db.execute(
        select(Order).where(
            Order.order_id == feedback_data.order_id,
            Order.institution_id == institution_id,
            Order.is_deleted == False,
        )
    ).scalars().first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found or does not belong to this institution"
        )

    # Validate ratings
    for category, items in feedback_data.menu_ratings.dict().items():
        for item in items:
            rating = item.get("rating")
            if rating is not None and (rating < 1 or rating > 5):
                raise HTTPException(
                    status_code=400,
                    detail=f"Rating must be between 1 and 5. Got: {rating}"
                )

    # Create feedback rating
    feedback_rating = FeedbackRating(
        institution_id=institution_id,
        order_id=feedback_data.order_id,
        meal_time=feedback_data.meal_time,
        date_of_feedback=feedback_data.date_of_feedback,
        user_type=feedback_data.user_type,
        user_name=feedback_data.user_name if not feedback_data.is_anonymous else None,
        is_anonymous=feedback_data.is_anonymous,
        spice_level=feedback_data.spice_level,
        additional_comments=feedback_data.additional_comments,
        menu_ratings=feedback_data.menu_ratings.dict(),
    )

    db.add(feedback_rating)
    db.commit()
    db.refresh(feedback_rating)

    return feedback_rating


# GET /api/rating-food - Get all feedback ratings (admin view)
@router.get("/", response_model=FeedbackRatingListResponse)
def get_all_feedback_ratings(
    db: Session = Depends(get_db),
    institution_id: Optional[UUID] = Query(None),
    date_of_feedback: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get all feedback ratings from all institutions (admin view).
    Can be filtered by institution_id and date_of_feedback.
    """
    query = select(FeedbackRating).options(
        joinedload(FeedbackRating.institution),
        joinedload(FeedbackRating.order),
    )

    if institution_id:
        query = query.where(FeedbackRating.institution_id == institution_id)
    if date_of_feedback:
        query = query.where(FeedbackRating.date_of_feedback == date_of_feedback)

    # Get total count
    count_query = select(func.count()).select_from(FeedbackRating)
    if institution_id:
        count_query = count_query.where(FeedbackRating.institution_id == institution_id)
    if date_of_feedback:
        count_query = count_query.where(FeedbackRating.date_of_feedback == date_of_feedback)
    total = db.execute(count_query).scalar()

    query = query.order_by(FeedbackRating.created_at.desc()).offset(skip).limit(limit)
    feedbacks = db.execute(query).scalars().unique().all()

    return FeedbackRatingListResponse(
        feedbacks=feedbacks,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


# GET /api/rating-food/{institution_id}/feedbacks - Get feedbacks for an institution
@router.get("/{institution_id}/feedbacks", response_model=FeedbackRatingListResponse)
def get_institution_feedbacks(
    institution_id: UUID,
    db: Session = Depends(get_db),
    date_of_feedback: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Get all feedback for a specific institution (paginated).
    Can be filtered by date_of_feedback.
    """
    query = select(FeedbackRating).options(
        joinedload(FeedbackRating.institution),
        joinedload(FeedbackRating.order),
    ).where(FeedbackRating.institution_id == institution_id)

    if date_of_feedback:
        query = query.where(FeedbackRating.date_of_feedback == date_of_feedback)

    # Get total count
    count_query = select(func.count()).select_from(FeedbackRating).where(
        FeedbackRating.institution_id == institution_id
    )
    if date_of_feedback:
        count_query = count_query.where(FeedbackRating.date_of_feedback == date_of_feedback)
    total = db.execute(count_query).scalar()

    query = query.order_by(FeedbackRating.created_at.desc()).offset(skip).limit(limit)
    feedbacks = db.execute(query).scalars().unique().all()

    return FeedbackRatingListResponse(
        feedbacks=feedbacks,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


# GET /api/rating-food/{institution_id}/feedbacks/{feedback_id} - Get specific feedback
@router.get("/{institution_id}/feedbacks/{feedback_id}", response_model=FeedbackRatingRead)
def get_feedback_by_id(
    institution_id: UUID,
    feedback_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve a specific feedback by ID.
    Validates that the feedback belongs to the institution.
    """
    feedback = db.execute(
        select(FeedbackRating).options(
            joinedload(FeedbackRating.institution),
            joinedload(FeedbackRating.order),
        ).where(
            FeedbackRating.id == feedback_id,
            FeedbackRating.institution_id == institution_id,
        )
    ).scalars().unique().first()

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    return feedback
