"""HTTP router for the Moodle integration module."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.integrations.moodle import (
    MoodleAPIError,
    MoodleConnectionError,
    MoodleError,
    MoodleNotConfiguredError,
)
from app.integrations.moodle.client import MoodleClient
from app.schemas.moodle import MoodleStatus, MoodleSyncResult
from app.schemas.sync_log import SyncLogRead
from app.services.moodle import MoodleSyncService, SyncInProgressError

router = APIRouter(prefix="/integrations/moodle", tags=["moodle"])


def get_moodle_client() -> MoodleClient:
    """Build a Moodle client from the application settings."""
    return MoodleClient.from_settings()


@router.get(
    "/status",
    response_model=MoodleStatus,
    summary="Check Moodle connection and token",
)
def moodle_status(
    client: Annotated[MoodleClient, Depends(get_moodle_client)],
) -> MoodleStatus:
    if not client.is_configured:
        return MoodleStatus(
            connected=False,
            message="Moodle is not configured (MOODLE_BASE_URL / MOODLE_WSTOKEN)",
        )
    try:
        info = client.call("core_webservice_get_site_info", {})
    except (MoodleConnectionError, MoodleAPIError) as exc:
        return MoodleStatus(connected=False, message=str(exc))
    site_name = info.get("sitename") if isinstance(info, dict) else None
    version = info.get("version") if isinstance(info, dict) else None
    return MoodleStatus(
        connected=True,
        site_name=str(site_name) if site_name else None,
        moodle_version=str(version) if version else None,
        message="Connected to Moodle",
    )


@router.post(
    "/sync",
    response_model=MoodleSyncResult,
    summary="Run full ERP -> Moodle synchronization",
)
def run_sync(
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[MoodleClient, Depends(get_moodle_client)],
) -> MoodleSyncResult:
    service = MoodleSyncService(db, client)
    try:
        logs = service.sync_all()
    except SyncInProgressError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except MoodleNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    except MoodleError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
        ) from exc

    success = sum(1 for log in logs if log.status == "Success")
    failed = sum(1 for log in logs if log.status == "Failed")
    return MoodleSyncResult(
        total=len(logs),
        success=success,
        failed=failed,
        logs=[SyncLogRead.model_validate(log) for log in logs],
    )