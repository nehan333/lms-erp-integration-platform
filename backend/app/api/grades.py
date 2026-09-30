"""HTTP router for the Grade module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.grade import GradeCreate, GradeList, GradeRead, GradeUpdate
from app.services.grade import (
    CourseNotFoundError,
    DuplicateGradeError,
    GradeNotFoundError,
    GradeService,
    StudentNotFoundError,
)

router = APIRouter(prefix="/grades", tags=["grades"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, GradeNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, DuplicateGradeError):
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


@router.get("", response_model=GradeList, summary="List grades")
def list_grades(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    student_id: Annotated[UUID | None, Query()] = None,
    course_id: Annotated[UUID | None, Query()] = None,
) -> GradeList:
    service = GradeService(db)
    items, total = service.list_grades(
        limit=limit,
        offset=offset,
        student_id=student_id,
        course_id=course_id,
    )
    return GradeList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=GradeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a grade record",
)
def create_grade(
    payload: GradeCreate,
    db: Annotated[Session, Depends(get_db)],
) -> GradeRead:
    service = GradeService(db)
    try:
        grade = service.create(payload)
    except (DuplicateGradeError, StudentNotFoundError, CourseNotFoundError) as exc:
        raise _to_http_error(exc) from exc
    return GradeRead.model_validate(grade)


@router.get("/{grade_id}", response_model=GradeRead, summary="Get a grade record")
def get_grade(
    grade_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> GradeRead:
    service = GradeService(db)
    try:
        grade = service.get(grade_id)
    except GradeNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return GradeRead.model_validate(grade)


@router.put(
    "/{grade_id}",
    response_model=GradeRead,
    summary="Update a grade record",
)
def update_grade(
    grade_id: UUID,
    payload: GradeUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> GradeRead:
    service = GradeService(db)
    try:
        grade = service.update(grade_id, payload)
    except GradeNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return GradeRead.model_validate(grade)


@router.delete(
    "/{grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a grade record",
)
def delete_grade(
    grade_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = GradeService(db)
    try:
        service.delete(grade_id)
    except GradeNotFoundError as exc:
        raise _to_http_error(exc) from exc