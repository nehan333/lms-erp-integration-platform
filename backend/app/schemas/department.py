"""Pydantic v2 schemas for the Department module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    """Payload for creating a department."""

    department_code: str = Field(..., min_length=1, max_length=10)
    department_name: str = Field(..., min_length=1, max_length=100)


class DepartmentUpdate(BaseModel):
    """Payload for updating a department. Only provided fields are applied."""

    department_code: str | None = Field(None, min_length=1, max_length=10)
    department_name: str | None = Field(None, min_length=1, max_length=100)


class DepartmentRead(BaseModel):
    """Response schema for a single department."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_code: str
    department_name: str
    created_at: datetime
    updated_at: datetime


class DepartmentList(BaseModel):
    """Paginated response for a list of departments."""

    items: list[DepartmentRead]
    total: int
    limit: int
    offset: int