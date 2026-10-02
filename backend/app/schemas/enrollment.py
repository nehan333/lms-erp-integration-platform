"""Pydantic v2 schemas for the Enrollment module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sync_log import SyncLogRead


class EnrollmentCreate(BaseModel):
    """Payload for enrolling a student in a course."""

    student_id: UUID
    course_id: UUID
    academic_year: str = Field(..., min_length=1, max_length=20)
    semester: int = Field(..., ge=1, le=10)


class EnrollmentUpdate(BaseModel):
    """Payload for updating an enrollment. Only provided fields are applied."""

    student_id: UUID | None = None
    course_id: UUID | None = None
    academic_year: str | None = Field(None, min_length=1, max_length=20)
    semester: int | None = Field(None, ge=1, le=10)


class EnrollmentRead(BaseModel):
    """Response schema for a single enrollment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    course_id: UUID
    academic_year: str
    semester: int
    created_at: datetime
    updated_at: datetime


class EnrollmentList(BaseModel):
    """Paginated response for a list of enrollments."""

    items: list[EnrollmentRead]
    total: int
    limit: int
    offset: int


class BulkEnrollmentRequest(BaseModel):
    """Payload for previewing/creating enrollments for a whole cohort.

    Resolves every active student of ``department_id`` at ``semester`` and
    enrolls them into each course in ``course_ids``.
    """

    department_id: UUID
    semester: int = Field(..., ge=1, le=10)
    academic_year: str = Field(..., min_length=1, max_length=20)
    course_ids: list[UUID] = Field(..., min_length=1, max_length=50)


class BulkEnrollmentCoursePreview(BaseModel):
    """Per-course counts for a bulk enrollment preview."""

    course_id: UUID
    course_code: str
    course_name: str
    to_create: int
    already_enrolled: int


class BulkEnrollmentPreview(BaseModel):
    """Dry-run summary: what ``POST /enrollments/bulk`` would do."""

    department_id: UUID
    semester: int
    academic_year: str
    students_total: int
    courses: list[BulkEnrollmentCoursePreview]
    total_to_create: int
    total_already_enrolled: int


class BulkEnrollmentCourseResult(BaseModel):
    """Per-course outcome of a bulk enrollment run."""

    course_id: UUID
    course_code: str
    created: int
    skipped: int


class BulkEnrollmentResult(BaseModel):
    """Outcome of ``POST /enrollments/bulk`` including the Moodle sync log."""

    department_id: UUID
    semester: int
    academic_year: str
    students_total: int
    created: int
    skipped: int
    courses: list[BulkEnrollmentCourseResult]
    sync_log: SyncLogRead | None = None