"""HTTP router for the Attendance module."""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceList,
    AttendanceRead,
    AttendanceUpdate,
)
from app.services.attendance import (
    AttendanceNotFoundError,
    AttendanceService,
    CourseNotFoundError,
    DuplicateAttendanceError,
    StudentNotFoundError,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AttendanceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, DuplicateAttendanceError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    if isinstance(exc, (StudentNotFoundError, CourseNotFoundError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


@router.get("", response_model=AttendanceList, summary="List attendance")
def list_attendance(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    student_id: Annotated[UUID | None, Query()] = None,
    course_id: Annotated[UUID | None, Query()] = None,
    date: Annotated[date | None, Query()] = None,
    status: Annotated[str | None, Query(pattern="^(Present|Absent)$")] = None,
) -> AttendanceList:
    service = AttendanceService(db)
    items, total = service.list_attendance(
        limit=limit,
        offset=offset,
        student_id=student_id,
        course_id=course_id,
        date=date,
        status=status,
    )
    return AttendanceList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=AttendanceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an attendance record",
)
def create_attendance(
    payload: AttendanceCreate,
    db: Annotated[Session, Depends(get_db)],
) -> AttendanceRead:
    service = AttendanceService(db)
    try:
        attendance = service.create(payload)
    except (
        DuplicateAttendanceError,
        StudentNotFoundError,
        CourseNotFoundError,
    ) as exc:
        raise _to_http_error(exc) from exc
    return AttendanceRead.model_validate(attendance)


@router.get(
    "/{attendance_id}",
    response_model=AttendanceRead,
    summary="Get an attendance record",
)
def get_attendance(
    attendance_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> AttendanceRead:
    service = AttendanceService(db)
    try:
        attendance = service.get(attendance_id)
    except AttendanceNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return AttendanceRead.model_validate(attendance)


@router.put(
    "/{attendance_id}",
    response_model=AttendanceRead,
    summary="Update an attendance record",
)
def update_attendance(
    attendance_id: UUID,
    payload: AttendanceUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> AttendanceRead:
    service = AttendanceService(db)
    try:
        attendance = service.update(attendance_id, payload)
    except (
        AttendanceNotFoundError,
        DuplicateAttendanceError,
        StudentNotFoundError,
        CourseNotFoundError,
    ) as exc:
        raise _to_http_error(exc) from exc
    return AttendanceRead.model_validate(attendance)


@router.delete(
    "/{attendance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an attendance record",
)
def delete_attendance(
    attendance_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = AttendanceService(db)
    try:
        service.delete(attendance_id)
    except AttendanceNotFoundError as exc:
        raise _to_http_error(exc) from exc