"""Pydantic v2 schemas for the Attendance module."""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

AttendanceStatus = Literal["Present", "Absent"]


class AttendanceCreate(BaseModel):
    """Payload for creating an attendance record."""

    student_id: UUID
    course_id: UUID
    date: date_type
    status: AttendanceStatus


class AttendanceUpdate(BaseModel):
    """Payload for updating an attendance record. Only provided fields are applied."""

    student_id: UUID | None = None
    course_id: UUID | None = None
    date: date_type | None = None
    status: AttendanceStatus | None = None


class AttendanceRead(BaseModel):
    """Response schema for a single attendance record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    course_id: UUID
    date: date_type
    status: str
    created_at: datetime
    updated_at: datetime


class AttendanceList(BaseModel):
    """Paginated response for a list of attendance records."""

    items: list[AttendanceRead]
    total: int
    limit: int
    offset: int