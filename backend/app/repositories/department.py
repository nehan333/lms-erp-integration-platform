"""Data-access layer for the Department module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.student import Student


class DepartmentRepository:
    """CRUD and query operations for ``Department`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, department_id: UUID) -> Department | None:
        """Return the department with ``department_id`` or ``None``."""
        return self.db.get(Department, department_id)

    def get_by_code(self, code: str) -> Department | None:
        """Return the first department with the exact code."""
        stmt = select(Department).where(Department.department_code == code)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Department | None:
        """Return the first department with the exact (case-insensitive) name."""
        stmt = select(Department).where(func.lower(Department.department_name) == name.lower())
        return self.db.scalar(stmt)

    def exists(self, department_id: UUID) -> bool:
        """Return ``True`` if a department with ``department_id`` exists."""
        stmt = select(Department.id).where(Department.id == department_id)
        return self.db.scalar(stmt) is not None

    def has_children(self, department_id: UUID) -> bool:
        """Return ``True`` if any faculty, student, or course references the department."""
        checks = [
            select(Faculty.id).where(Faculty.department_id == department_id),
            select(Student.id).where(Student.department_id == department_id),
            select(Course.id).where(Course.department_id == department_id),
        ]
        return any(self.db.scalar(stmt.limit(1)) is not None for stmt in checks)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> tuple[list[Department], int]:
        """Return a page of departments and the total number of matching rows."""
        conditions = []
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    Department.department_name.ilike(pattern),
                    Department.department_code.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Department)
        items_stmt = select(Department)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(Department.department_name, Department.department_code)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Department:
        """Create and flush a new department from field values."""
        department = Department(**data)
        self.db.add(department)
        self.db.flush()
        return department

    def update(self, department: Department, data: Mapping[str, object]) -> Department:
        """Apply field updates to an existing department and flush."""
        for field, value in data.items():
            setattr(department, field, value)
        self.db.add(department)
        self.db.flush()
        return department

    def delete(self, department: Department) -> None:
        """Hard-delete a department."""
        self.db.delete(department)
        self.db.flush()