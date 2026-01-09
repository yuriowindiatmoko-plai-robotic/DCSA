# app/models/edit_request.py
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime

import uuid

from app.db.base import Base


class EditRequest(Base):
    __tablename__ = "edit_requests"

    edit_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.institution_id"), nullable=False
    )
    original_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    requested_changes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    sla_status: Mapped[str] = mapped_column(String(50), nullable=False)
    approval_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING"
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approval_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    order = relationship("Order", backref="edit_requests")
    institution = relationship("Institution", backref="edit_requests")
    submitter = relationship("User", foreign_keys=[submitted_by], backref="edit_requests_submitted")
    approver = relationship("User", foreign_keys=[approved_by], backref="edit_requests_approved")
