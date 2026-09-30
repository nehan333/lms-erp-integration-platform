"""Business logic for the Sync Log module."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog
from app.repositories.sync_log import SyncLogRepository


class SyncLogNotFoundError(Exception):
    """Raised when a sync log entry does not exist."""

    def __init__(self, sync_log_id: UUID) -> None:
        super().__init__(f"Sync log {sync_log_id} not found")
        self.sync_log_id = sync_log_id


class SyncLogService:
    """Coordinates repository operations for synchronization logs."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = SyncLogRepository(db)

    def get(self, sync_log_id: UUID) -> SyncLog:
        log = self.repo.get(sync_log_id)
        if log is None:
            raise SyncLogNotFoundError(sync_log_id)
        return log

    def list_logs(
        self,
        *,
        limit: int,
        offset: int,
        module: str | None = None,
        action: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[SyncLog], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            module=module,
            action=action,
            status=status,
        )

    def record(
        self,
        *,
        module: str,
        action: str,
        status: str,
        message: str | None = None,
    ) -> SyncLog:
        """Create and commit a sync log entry. Used by the integration engine."""
        log = self.repo.create(
            module=module,
            action=action,
            status=status,
            message=message,
        )
        self.db.commit()
        self.db.refresh(log)
        return log