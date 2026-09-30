"""Pydantic v2 schemas for the Course module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    """Payload for creating a course."""

    course_code: str = Field(..., min_length=1, max_length=20)
    course_name: str = Field(..., min_length=1, max_length=150)
    credits: int = Field(..., ge=1, le=10)
    semester: int = Field(..., ge=1, le=10)
    department_id: UUID
    faculty_id: UUID | None = None


class CourseUpdate(BaseModel):
    """Payload for updating a course. Only provided fields are applied."""

    course_code: str | None = Field(None, min_length=1, max_length=20)
    course_name: str | None = Field(None, min_length=1, max_length=150)
    credits: int | None = Field(None, ge=1, le=10)
    semester: int | None = Field(None, ge=1, le=10)
    department_id: UUID | None = None
    faculty_id: UUID | None = None


class CourseRead(BaseModel):
    """Response schema for a single course."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_code: str
    course_name: str
    credits: int
    semester: int
    department_id: UUID
    faculty_id: UUID | None
    created_at: datetime
    updated_at: datetime


class CourseList(BaseModel):
    """Paginated response for a list of courses."""

    items: list[CourseRead]
    total: int
    limit: int
    offset: int