"""Pydantic v2 schemas for the Grade module."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GradeCreate(BaseModel):
    """Payload for creating a grade record."""

    student_id: UUID
    course_id: UUID
    internal_marks: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    external_marks: Decimal = Field(..., ge=0, le=100, decimal_places=2)
    final_grade: str = Field(..., min_length=1, max_length=5)


class GradeUpdate(BaseModel):
    """Payload for updating a grade record. Only provided fields are applied."""

    internal_marks: Decimal | None = Field(None, ge=0, le=100, decimal_places=2)
    external_marks: Decimal | None = Field(None, ge=0, le=100, decimal_places=2)
    final_grade: str | None = Field(None, min_length=1, max_length=5)


class GradeRead(BaseModel):
    """Response schema for a single grade record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    course_id: UUID
    internal_marks: Decimal
    external_marks: Decimal
    final_grade: str
    created_at: datetime
    updated_at: datetime


class GradeList(BaseModel):
    """Paginated response for a list of grade records."""

    items: list[GradeRead]
    total: int
    limit: int
    offset: int