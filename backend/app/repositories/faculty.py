"""Data-access layer for the Faculty module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.faculty import Faculty
from app.repositories.department import DepartmentRepository


class FacultyRepository:
    """CRUD and query operations for ``Faculty`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, faculty_id: UUID) -> Faculty | None:
        """Return the faculty member with ``faculty_id`` or ``None``."""
        return self.db.get(Faculty, faculty_id)

    def get_by_employee_id(self, employee_id: str) -> Faculty | None:
        """Return the first faculty member with the exact employee id."""
        stmt = select(Faculty).where(Faculty.employee_id == employee_id)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> Faculty | None:
        """Return the first faculty member with a case-insensitive email match."""
        stmt = select(Faculty).where(func.lower(Faculty.email) == email.lower())
        return self.db.scalar(stmt)

    def department_exists(self, department_id: UUID) -> bool:
        """Return ``True`` if the referenced department exists."""
        return DepartmentRepository(self.db).exists(department_id)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        department_id: UUID | None = None,
        status: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Faculty], int]:
        """Return a page of faculty and the total number of matching rows."""
        conditions = []
        if department_id is not None:
            conditions.append(Faculty.department_id == department_id)
        if status is not None:
            conditions.append(Faculty.status == status)
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    Faculty.name.ilike(pattern),
                    Faculty.email.ilike(pattern),
                    Faculty.employee_id.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Faculty)
        items_stmt = select(Faculty)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(Faculty.name, Faculty.employee_id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Faculty:
        """Create and flush a new faculty member from field values."""
        faculty = Faculty(**data)
        self.db.add(faculty)
        self.db.flush()
        return faculty

    def update(self, faculty: Faculty, data: Mapping[str, object]) -> Faculty:
        """Apply field updates to an existing faculty member and flush."""
        for field, value in data.items():
            setattr(faculty, field, value)
        self.db.add(faculty)
        self.db.flush()
        return faculty

    def soft_delete(self, faculty: Faculty) -> Faculty:
        """Deactivate a faculty member by setting ``status`` to ``False``."""
        faculty.status = False
        self.db.add(faculty)
        self.db.flush()
        return faculty