"""HTTP router for the Student module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.moodle import get_moodle_client
from app.db.session import get_db
from app.integrations.moodle.client import MoodleClient
from app.schemas.student import (
    BulkStudentImportRequest,
    BulkStudentImportResult,
    StudentAttendanceSummary,
    StudentCreate,
    StudentList,
    StudentRead,
    StudentUpdate,
)
from app.schemas.sync_log import SyncLogRead
from app.services.attendance import (
    AttendanceService,
    StudentNotFoundError as AttendanceStudentNotFoundError,
)
from app.services.moodle import MoodleSyncService
from app.services.student import (
    BulkImportFormatError,
    DepartmentNotFoundError,
    DuplicateStudentError,
    StudentNotFoundError,
    StudentService,
)

router = APIRouter(prefix="/students", tags=["students"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, StudentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, DuplicateStudentError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    if isinstance(exc, BulkImportFormatError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    if isinstance(exc, DepartmentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


@router.get("", response_model=StudentList, summary="List students")
def list_students(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    department_id: Annotated[UUID | None, Query()] = None,
    semester: Annotated[int | None, Query(ge=1, le=10)] = None,
    status_filter: Annotated[bool | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query(min_length=1)] = None,
) -> StudentList:
    service = StudentService(db)
    items, total = service.list_students(
        limit=limit,
        offset=offset,
        department_id=department_id,
        semester=semester,
        status=status_filter,
        search=search,
    )
    return StudentList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a student",
)
def create_student(
    payload: StudentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> StudentRead:
    service = StudentService(db)
    try:
        student = service.create(payload)
    except (StudentNotFoundError, DuplicateStudentError, DepartmentNotFoundError) as exc:
        raise _to_http_error(exc) from exc
    return StudentRead.model_validate(student)


@router.post(
    "/bulk",
    response_model=BulkStudentImportResult,
    status_code=status.HTTP_201_CREATED,
    summary="Import students from CSV (body is JSON with csv text)",
)
def bulk_import_students(
    payload: BulkStudentImportRequest,
    db: Annotated[Session, Depends(get_db)],
    client: Annotated[MoodleClient, Depends(get_moodle_client)],
) -> BulkStudentImportResult:
    service = StudentService(db)
    try:
        result, created_ids = service.bulk_import(payload)
    except (BulkImportFormatError, DepartmentNotFoundError) as exc:
        raise _to_http_error(exc) from exc

    if (
        created_ids
        and payload.sync_moodle
        and not payload.dry_run
    ):
        sync_log = MoodleSyncService(db, client).sync_students(
            student_ids=created_ids
        )
        result.sync_log = SyncLogRead.model_validate(sync_log)
    return result


@router.get(
    "/{student_id}/attendance-summary",
    response_model=StudentAttendanceSummary,
    summary="Attendance-by-course breakdown for a student",
)
def student_attendance_summary(
    student_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> StudentAttendanceSummary:
    service = AttendanceService(db)
    try:
        return service.student_summary(student_id)
    except AttendanceStudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/{student_id}", response_model=StudentRead, summary="Get a student")
def get_student(
    student_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> StudentRead:
    service = StudentService(db)
    try:
        student = service.get(student_id)
    except StudentNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return StudentRead.model_validate(student)


@router.put(
    "/{student_id}",
    response_model=StudentRead,
    summary="Update a student",
)
def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> StudentRead:
    service = StudentService(db)
    try:
        student = service.update(student_id, payload)
    except (StudentNotFoundError, DuplicateStudentError, DepartmentNotFoundError) as exc:
        raise _to_http_error(exc) from exc
    return StudentRead.model_validate(student)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete (deactivate) a student",
)
def delete_student(
    student_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = StudentService(db)
    try:
        service.delete(student_id)
    except StudentNotFoundError as exc:
        raise _to_http_error(exc) from exc
