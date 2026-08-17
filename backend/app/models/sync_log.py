"""Synchronization log model."""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import BaseModelMixin


class SyncLog(Base, BaseModelMixin):
    """A log entry for a Moodle synchronization operation."""

    __tablename__ = "sync_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Success', 'Failed')",
            name="ck_sync_logs_status",
        ),
        Index("ix_sync_logs_module", "module"),
        Index("ix_sync_logs_status", "status"),
        Index("ix_sync_logs_created_at", "created_at"),
    )

    module: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
