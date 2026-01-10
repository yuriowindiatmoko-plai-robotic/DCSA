# app/models/order.py
from sqlalchemy import String, Integer, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime, date

import uuid

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.institution_id"), nullable=False
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    order_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="REGULAR"
    )
    total_portion: Mapped[int] = mapped_column(Integer, nullable=False)
    staff_allocation: Mapped[dict] = mapped_column(JSONB, nullable=False)
    menu_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dropping_location_food: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    special_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    institution = relationship("Institution", backref="orders")
    creator = relationship("User", foreign_keys=[created_by], backref="orders_created")
    approver = relationship("User", foreign_keys=[approved_by], backref="orders_approved")
