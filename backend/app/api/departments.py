"""HTTP router for the Department module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentList,
    DepartmentRead,
    DepartmentUpdate,
)
from app.services.department import (
    DepartmentInUseError,
    DepartmentNotFoundError,
    DepartmentService,
    DuplicateDepartmentError,
)

router = APIRouter(prefix="/departments", tags=["departments"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DepartmentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, DepartmentInUseError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    if isinstance(exc, DuplicateDepartmentError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


@router.get("", response_model=DepartmentList, summary="List departments")
def list_departments(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1)] = None,
) -> DepartmentList:
    service = DepartmentService(db)
    items, total = service.list_departments(limit=limit, offset=offset, search=search)
    return DepartmentList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
)
def create_department(
    payload: DepartmentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> DepartmentRead:
    service = DepartmentService(db)
    try:
        department = service.create(payload)
    except DuplicateDepartmentError as exc:
        raise _to_http_error(exc) from exc
    return DepartmentRead.model_validate(department)


@router.get("/{department_id}", response_model=DepartmentRead, summary="Get a department")
def get_department(
    department_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> DepartmentRead:
    service = DepartmentService(db)
    try:
        department = service.get(department_id)
    except DepartmentNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return DepartmentRead.model_validate(department)


@router.put(
    "/{department_id}",
    response_model=DepartmentRead,
    summary="Update a department",
)
def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> DepartmentRead:
    service = DepartmentService(db)
    try:
        department = service.update(department_id, payload)
    except (DepartmentNotFoundError, DuplicateDepartmentError) as exc:
        raise _to_http_error(exc) from exc
    return DepartmentRead.model_validate(department)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a department",
)
def delete_department(
    department_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = DepartmentService(db)
    try:
        service.delete(department_id)
    except (DepartmentNotFoundError, DepartmentInUseError) as exc:
        raise _to_http_error(exc) from exc