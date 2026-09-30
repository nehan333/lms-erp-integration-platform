"""Pydantic v2 schemas for the Enrollment module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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