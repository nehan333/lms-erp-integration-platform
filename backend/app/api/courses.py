"""HTTP router for the Course module."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.course import CourseCreate, CourseList, CourseRead, CourseUpdate
from app.services.course import (
    CourseInUseError,
    CourseNotFoundError,
    CourseService,
    DepartmentNotFoundError,
    DuplicateCourseError,
    FacultyNotFoundError,
)

router = APIRouter(prefix="/courses", tags=["courses"])


def _to_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, CourseNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    if isinstance(exc, (DuplicateCourseError, CourseInUseError)):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        )
    if isinstance(exc, (DepartmentNotFoundError, FacultyNotFoundError)):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )


@router.get("", response_model=CourseList, summary="List courses")
def list_courses(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    department_id: Annotated[UUID | None, Query()] = None,
    faculty_id: Annotated[UUID | None, Query()] = None,
    semester: Annotated[int | None, Query(ge=1, le=10)] = None,
    search: Annotated[str | None, Query(min_length=1)] = None,
) -> CourseList:
    service = CourseService(db)
    items, total = service.list_courses(
        limit=limit,
        offset=offset,
        department_id=department_id,
        faculty_id=faculty_id,
        semester=semester,
        search=search,
    )
    return CourseList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a course",
)
def create_course(
    payload: CourseCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CourseRead:
    service = CourseService(db)
    try:
        course = service.create(payload)
    except (
        DuplicateCourseError,
        DepartmentNotFoundError,
        FacultyNotFoundError,
    ) as exc:
        raise _to_http_error(exc) from exc
    return CourseRead.model_validate(course)


@router.get("/{course_id}", response_model=CourseRead, summary="Get a course")
def get_course(
    course_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CourseRead:
    service = CourseService(db)
    try:
        course = service.get(course_id)
    except CourseNotFoundError as exc:
        raise _to_http_error(exc) from exc
    return CourseRead.model_validate(course)


@router.put(
    "/{course_id}",
    response_model=CourseRead,
    summary="Update a course",
)
def update_course(
    course_id: UUID,
    payload: CourseUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> CourseRead:
    service = CourseService(db)
    try:
        course = service.update(course_id, payload)
    except (
        CourseNotFoundError,
        DuplicateCourseError,
        DepartmentNotFoundError,
        FacultyNotFoundError,
    ) as exc:
        raise _to_http_error(exc) from exc
    return CourseRead.model_validate(course)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a course",
)
def delete_course(
    course_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = CourseService(db)
    try:
        service.delete(course_id)
    except (CourseNotFoundError, CourseInUseError) as exc:
        raise _to_http_error(exc) from exc