"""HTTP router for the Dashboard / statistics module."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import OverviewStatistics
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/overview",
    response_model=OverviewStatistics,
    summary="Get ERP overview statistics",
)
def get_overview(
    db: Annotated[Session, Depends(get_db)],
) -> OverviewStatistics:
    return DashboardService(db).overview()