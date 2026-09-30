"""Data-access layer for the Grade module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.grade import Grade
from app.models.student import Student


class GradeRepository:
    """CRUD and query operations for ``Grade`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, grade_id: UUID) -> Grade | None:
        """Return the grade record with ``grade_id`` or ``None``."""
        return self.db.get(Grade, grade_id)

    def get_by_unique(self, student_id: UUID, course_id: UUID) -> Grade | None:
        """Return the grade record matching the unique student/course pair."""
        stmt = select(Grade).where(
            Grade.student_id == student_id,
            Grade.course_id == course_id,
        )
        return self.db.scalar(stmt)

    def student_exists(self, student_id: UUID) -> bool:
        """Return ``True`` if the referenced student exists."""
        return self.db.get(Student, student_id) is not None

    def course_exists(self, course_id: UUID) -> bool:
        """Return ``True`` if the referenced course exists."""
        return self.db.get(Course, course_id) is not None

    def list(
        self,
        *,
        limit: int,
        offset: int,
        student_id: UUID | None = None,
        course_id: UUID | None = None,
    ) -> tuple[list[Grade], int]:
        """Return a page of grades and the total number of matching rows."""
        conditions = []
        if student_id is not None:
            conditions.append(Grade.student_id == student_id)
        if course_id is not None:
            conditions.append(Grade.course_id == course_id)

        count_stmt = select(func.count()).select_from(Grade)
        items_stmt = select(Grade)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(Grade.created_at.desc(), Grade.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Grade:
        """Create and flush a new grade record from field values."""
        grade = Grade(**data)
        self.db.add(grade)
        self.db.flush()
        return grade

    def update(self, grade: Grade, data: Mapping[str, object]) -> Grade:
        """Apply field updates to an existing grade record and flush."""
        for field, value in data.items():
            setattr(grade, field, value)
        self.db.add(grade)
        self.db.flush()
        return grade

    def delete(self, grade: Grade) -> None:
        """Hard-delete a grade record."""
        self.db.delete(grade)
        self.db.flush()