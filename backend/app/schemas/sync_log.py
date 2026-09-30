"""Pydantic v2 schemas for the Sync Log module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SyncLogRead(BaseModel):
    """Response schema for a single synchronization log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    module: str
    action: str
    status: str
    message: str | None
    created_at: datetime
    updated_at: datetime


class SyncLogList(BaseModel):
    """Paginated response for a list of synchronization log entries."""

    items: list[SyncLogRead]
    total: int
    limit: int
    offset: int