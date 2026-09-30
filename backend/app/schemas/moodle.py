"""Pydantic v2 schemas for the Moodle integration module."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.sync_log import SyncLogRead


class MoodleStatus(BaseModel):
    """Result of a Moodle connection / auth check."""

    connected: bool
    site_name: str | None = None
    moodle_version: str | None = None
    message: str | None = None


class MoodleSyncResult(BaseModel):
    """Summary of a full synchronization run."""

    total: int
    success: int
    failed: int
    logs: list[SyncLogRead]