"""Pydantic v2 schemas for the Student module."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
