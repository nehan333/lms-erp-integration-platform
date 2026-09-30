"""Pydantic v2 schemas for the Faculty module."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FacultyEmailMixin:
    """Shared email validation for faculty create/update payloads."""

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValueError("Invalid email address")
        return normalized


class FacultyCreate(FacultyEmailMixin, BaseModel):
    """Payload for creating a faculty member."""

    employee_id: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    designation: str = Field(..., min_length=1, max_length=100)
    department_id: UUID
    status: bool = True


class FacultyUpdate(FacultyEmailMixin, BaseModel):
    """Payload for updating a faculty member. Only provided fields are applied."""

    employee_id: str | None = Field(None, min_length=1, max_length=20)
    name: str | None = Field(None, min_length=1, max_length=100)
    email: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    designation: str | None = Field(None, min_length=1, max_length=100)
    department_id: UUID | None = None
    status: bool | None = None


class FacultyRead(BaseModel):
    """Response schema for a single faculty member."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: str
    name: str
    email: str
    phone: str | None
    designation: str
    department_id: UUID
    status: bool
    created_at: datetime
    updated_at: datetime


class FacultyList(BaseModel):
    """Paginated response for a list of faculty members."""

    items: list[FacultyRead]
    total: int
    limit: int
    offset: int