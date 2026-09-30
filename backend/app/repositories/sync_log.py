"""Data-access layer for the Sync Log module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog


class SyncLogRepository:
    """CRUD and query operations for ``SyncLog`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, sync_log_id: UUID) -> SyncLog | None:
        """Return the log entry with ``sync_log_id`` or ``None``."""
        return self.db.get(SyncLog, sync_log_id)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        module: str | None = None,
        action: str | None = None,
        status: str | None = None,
    ) -> tuple[list[SyncLog], int]:
        """Return a page of log entries and the total number of matching rows."""
        conditions = []
        if module is not None:
            conditions.append(SyncLog.module == module)
        if action is not None:
            conditions.append(SyncLog.action == action)
        if status is not None:
            conditions.append(SyncLog.status == status)

        count_stmt = select(func.count()).select_from(SyncLog)
        items_stmt = select(SyncLog)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(SyncLog.created_at.desc(), SyncLog.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(
        self,
        *,
        module: str,
        action: str,
        status: str,
        message: str | None = None,
    ) -> SyncLog:
        """Create and flush a new log entry."""
        log = SyncLog(
            module=module,
            action=action,
            status=status,
            message=message,
        )
        self.db.add(log)
        self.db.flush()
        return log