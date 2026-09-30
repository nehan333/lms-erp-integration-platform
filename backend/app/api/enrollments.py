"""HTTP router for the Enrollment module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentList,
    EnrollmentRead,
    EnrollmentUpdate,
)
from app.services.enrollment import (
    CourseNotFoundError,
    DuplicateEnrollmentError,
    EnrollmentNotFoundError,
    EnrollmentService,
    StudentNotFoundError,
)

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, EnrollmentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, DuplicateEnrollmentError):
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


@router.get("", response_model=EnrollmentList, summary="List enrollments")
def list_enrollments(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    student_id: Annotated[UUID | None, Query()] = None,
    course_id: Annotated[UUID | None, Query()] = None,
    academic_year: Annotated[str | None, Query(min_length=1)] = None,
    semester: Annotated[int | None, Query(ge=1, le=10)] = None,
) -> EnrollmentList:
    service = EnrollmentService(db)
    items, total = service.list_enrollments(
        limit=limit,
        offset=offset,
        student_id=student_id,
        course_id=course_id,
        academic_year=academic_year,
        semester=semester,
    )
    return EnrollmentList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an enrollment",
)
def create_enrollment(
    payload: EnrollmentCreate,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollmentRead:
    service = EnrollmentService(db)
    try:
        enrollment = service.create(payload)
    except (
        DuplicateEnrollmentError,
        StudentNotFoundError,
        CourseNotFoundError,
    ) as exc:
        raise _to_http_error(exc) from exc
    return EnrollmentRead.model_validate(enrollment)


@router.get("/{enrollment_id}", response_model=EnrollmentRead, summary="Get an enrollment")
def get_enrollment(
    enrollment_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollmentRead:
    service = EnrollmentService(db)
    try:
        enrollment = service.get(enrollment_id)
    except EnrollmentNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return EnrollmentRead.model_validate(enrollment)


@router.put(
    "/{enrollment_id}",
    response_model=EnrollmentRead,
    summary="Update an enrollment",
)
def update_enrollment(
    enrollment_id: UUID,
    payload: EnrollmentUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> EnrollmentRead:
    service = EnrollmentService(db)
    try:
        enrollment = service.update(enrollment_id, payload)
    except (
        EnrollmentNotFoundError,
        DuplicateEnrollmentError,
        StudentNotFoundError,
        CourseNotFoundError,
    ) as exc:
        raise _to_http_error(exc) from exc
    return EnrollmentRead.model_validate(enrollment)


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an enrollment",
)
def delete_enrollment(
    enrollment_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = EnrollmentService(db)
    try:
        service.delete(enrollment_id)
    except EnrollmentNotFoundError as exc:
        raise _to_http_error(exc) from exc