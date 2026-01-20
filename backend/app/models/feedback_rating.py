# app/models/feedback_rating.py
from sqlalchemy import String, Integer, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime, date

import uuid

from app.db.base import Base


class FeedbackRating(Base):
    __tablename__ = "feedback_ratings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.institution_id"), nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False
    )
    meal_time: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_feedback: Mapped[date] = mapped_column(Date, nullable=False)
    user_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    spice_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    additional_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    menu_ratings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    institution = relationship("Institution", backref="feedback_ratings")
    order = relationship("Order", backref="feedback_ratings")
