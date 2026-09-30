"""HTTP router for the Faculty module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.faculty import FacultyCreate, FacultyList, FacultyRead, FacultyUpdate
from app.services.faculty import (
    DepartmentNotFoundError,
    DuplicateFacultyError,
    FacultyNotFoundError,
    FacultyService,
)

router = APIRouter(prefix="/faculty", tags=["faculty"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, FacultyNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, DuplicateFacultyError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    if isinstance(exc, DepartmentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


@router.get("", response_model=FacultyList, summary="List faculty")
def list_faculty(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    department_id: Annotated[UUID | None, Query()] = None,
    status_filter: Annotated[bool | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1)] = None,
) -> FacultyList:
    service = FacultyService(db)
    items, total = service.list_faculty(
        limit=limit,
        offset=offset,
        department_id=department_id,
        status=status_filter,
        search=search,
    )
    return FacultyList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=FacultyRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a faculty member",
)
def create_faculty(
    payload: FacultyCreate,
    db: Annotated[Session, Depends(get_db)],
) -> FacultyRead:
    service = FacultyService(db)
    try:
        faculty = service.create(payload)
    except (DuplicateFacultyError, DepartmentNotFoundError) as exc:
        raise _to_http_error(exc) from exc
    return FacultyRead.model_validate(faculty)


@router.get("/{faculty_id}", response_model=FacultyRead, summary="Get a faculty member")
def get_faculty(
    faculty_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> FacultyRead:
    service = FacultyService(db)
    try:
        faculty = service.get(faculty_id)
    except FacultyNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return FacultyRead.model_validate(faculty)


@router.put(
    "/{faculty_id}",
    response_model=FacultyRead,
    summary="Update a faculty member",
)
def update_faculty(
    faculty_id: UUID,
    payload: FacultyUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> FacultyRead:
    service = FacultyService(db)
    try:
        faculty = service.update(faculty_id, payload)
    except (FacultyNotFoundError, DuplicateFacultyError, DepartmentNotFoundError) as exc:
        raise _to_http_error(exc) from exc
    return FacultyRead.model_validate(faculty)


@router.delete(
    "/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (deactivate) a faculty member",
)
def delete_faculty(
    faculty_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = FacultyService(db)
    try:
        service.delete(faculty_id)
    except FacultyNotFoundError as exc:
        raise _to_http_error(exc) from exc