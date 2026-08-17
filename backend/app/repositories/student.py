"""Data-access layer for the Student module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.student import Student


class StudentRepository:
    """CRUD and query operations for ``Student`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, student_id: UUID) -> Student | None:
        """Return the student with ``student_id`` or ``None``."""
        return self.db.get(Student, student_id)

    def get_by_roll_number(self, roll_number: str) -> Student | None:
        """Return the first student with the exact roll number."""
        stmt = select(Student).where(Student.roll_number == roll_number)
        return self.db.scalar(stmt)

    def get_by_email(self, email: str) -> Student | None:
        """Return the first student with a case-insensitive email match."""
        stmt = select(Student).where(func.lower(Student.email) == email.lower())
        return self.db.scalar(stmt)

    def department_exists(self, department_id: UUID) -> bool:
        """Return ``True`` if a department with ``department_id`` exists."""
        stmt = select(Department.id).where(Department.id == department_id)
        return self.db.scalar(stmt) is not None

    def list(
        self,
        *,
        limit: int,
        offset: int,
        department_id: UUID | None = None,
        semester: int | None = None,
        status: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Student], int]:
        """Return a page of students and the total number of matching rows."""
        conditions = []
        if department_id is not None:
            conditions.append(Student.department_id == department_id)
        if semester is not None:
            conditions.append(Student.semester == semester)
        if status is not None:
            conditions.append(Student.status == status)
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    Student.name.ilike(pattern),
                    Student.email.ilike(pattern),
                    Student.roll_number.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Student)
        items_stmt = select(Student)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = (
            self.db.scalars(
                items_stmt.order_by(Student.name, Student.roll_number)
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Student:
        """Create and flush a new student from field values."""
        student = Student(**data)
        self.db.add(student)
        self.db.flush()
        return student

    def update(self, student: Student, data: Mapping[str, object]) -> Student:
        """Apply field updates to an existing student and flush."""
        for field, value in data.items():
            setattr(student, field, value)
        self.db.add(student)
        self.db.flush()
        return student

    def soft_delete(self, student: Student) -> Student:
        """Deactivate a student by setting ``status`` to ``False``."""
        student.status = False
        self.db.add(student)
        self.db.flush()
        return student
