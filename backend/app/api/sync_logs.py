"""HTTP router for the Sync Log module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sync_log import SyncLogList, SyncLogRead
from app.services.sync_log import SyncLogNotFoundError, SyncLogService

router = APIRouter(prefix="/sync-logs", tags=["sync-logs"])


@router.get("", response_model=SyncLogList, summary="List synchronization logs")
def list_sync_logs(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    module: Annotated[str | None, Query(min_length=1)] = None,
    action: Annotated[str | None, Query(min_length=1)] = None,
    status_filter: Annotated[str | None, Query(alias="status", pattern="^(Success|Failed)$")] = None,
) -> SyncLogList:
    service = SyncLogService(db)
    items, total = service.list_logs(
        limit=limit,
        offset=offset,
        module=module,
        action=action,
        status=status_filter,
    )
    return SyncLogList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{sync_log_id}", response_model=SyncLogRead, summary="Get a sync log entry")
def get_sync_log(
    sync_log_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> SyncLogRead:
    service = SyncLogService(db)
    try:
        log = service.get(sync_log_id)
    except SyncLogNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return SyncLogRead.model_validate(log)