"""Pydantic v2 schemas for the Student module."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.sync_log import SyncLogRead

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class StudentEmailMixin:
    """Shared email validation for create/update payloads."""

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValueError("Invalid email address")
        return normalized


class StudentCreate(StudentEmailMixin, BaseModel):
    """Payload for creating a student."""

    roll_number: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    department_id: UUID
    semester: int = Field(..., ge=1, le=10)
    section: str = Field(..., min_length=1, max_length=10)
    status: bool = True


class StudentUpdate(StudentEmailMixin, BaseModel):
    """Payload for updating a student. Only provided fields are applied."""

    roll_number: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    department_id: UUID | None = None
    semester: int | None = Field(None, ge=1, le=10)
    section: str | None = Field(None, min_length=1, max_length=10)
    status: bool | None = None


class StudentRead(BaseModel):
    """Response schema for a single student."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roll_number: str
    name: str
    email: str
    phone: str | None
    department_id: UUID
    semester: int
    section: str
    status: bool
    created_at: datetime
    updated_at: datetime


class StudentList(BaseModel):
    """Paginated response for a list of students."""

    items: list[StudentRead]
    total: int
    limit: int
    offset: int


class BulkStudentImportRequest(BaseModel):
    """Payload for importing students from CSV text.

    The CSV body travels as JSON (``csv``) so no multipart upload is needed.
    Expected columns (header row, case-insensitive): ``roll_number``, ``name``,
    ``email``, ``semester``, ``section`` and optionally ``phone``. Every row is
    imported into ``department_id``.
    """

    csv: str = Field(..., min_length=1, max_length=1_000_000)
    department_id: UUID
    dry_run: bool = False
    sync_moodle: bool = True


class BulkStudentRowError(BaseModel):
    """One rejected CSV row (1-based, header included in the count)."""

    row: int
    error: str


class BulkStudentImportResult(BaseModel):
    """Outcome of a bulk student import run."""

    total: int
    created: int
    skipped: int
    failed: int
    dry_run: bool
    errors: list[BulkStudentRowError] = []
    sync_log: SyncLogRead | None = None


class StudentAttendanceCourse(BaseModel):
    """Attendance totals for one course of a student.

    ``percentage`` is ``None`` when the student has no attendance records in
    the course (division by zero is not a guess we make).
    """

    course_id: UUID
    course_code: str
    course_name: str
    present: int
    total: int
    percentage: float | None = None


class StudentAttendanceSummary(BaseModel):
    """Attendance-by-course breakdown for a student detail page."""

    student_id: UUID
    courses: list[StudentAttendanceCourse] = []
    present: int = 0
    total: int = 0
    percentage: float | None = None
