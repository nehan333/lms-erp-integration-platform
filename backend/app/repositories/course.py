"""Data-access layer for the Course module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.repositories.department import DepartmentRepository


class CourseRepository:
    """CRUD and query operations for ``Course`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, course_id: UUID) -> Course | None:
        """Return the course with ``course_id`` or ``None``."""
        return self.db.get(Course, course_id)

    def get_by_code(self, code: str) -> Course | None:
        """Return the first course with the exact code."""
        stmt = select(Course).where(Course.course_code == code)
        return self.db.scalar(stmt)

    def department_exists(self, department_id: UUID) -> bool:
        """Return ``True`` if the referenced department exists."""
        return DepartmentRepository(self.db).exists(department_id)

    def faculty_exists(self, faculty_id: UUID) -> bool:
        """Return ``True`` if the referenced faculty member exists."""
        stmt = select(Faculty.id).where(Faculty.id == faculty_id)
        return self.db.scalar(stmt) is not None

    def has_children(self, course_id: UUID) -> bool:
        """Return ``True`` if any enrollment, attendance, or grade references the course."""
        checks = [
            select(Enrollment.id).where(Enrollment.course_id == course_id),
            select(Attendance.id).where(Attendance.course_id == course_id),
            select(Grade.id).where(Grade.course_id == course_id),
        ]
        return any(self.db.scalar(stmt.limit(1)) is not None for stmt in checks)

    def list(
        self,
        *,
        limit: int,
        offset: int,
        department_id: UUID | None = None,
        faculty_id: UUID | None = None,
        semester: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Course], int]:
        """Return a page of courses and the total number of matching rows."""
        conditions = []
        if department_id is not None:
            conditions.append(Course.department_id == department_id)
        if faculty_id is not None:
            conditions.append(Course.faculty_id == faculty_id)
        if semester is not None:
            conditions.append(Course.semester == semester)
        if search:
            pattern = f"%{search}%"
            conditions.append(
                or_(
                    Course.course_name.ilike(pattern),
                    Course.course_code.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Course)
        items_stmt = select(Course)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(Course.course_name, Course.course_code)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Course:
        """Create and flush a new course from field values."""
        course = Course(**data)
        self.db.add(course)
        self.db.flush()
        return course

    def update(self, course: Course, data: Mapping[str, object]) -> Course:
        """Apply field updates to an existing course and flush."""
        for field, value in data.items():
            setattr(course, field, value)
        self.db.add(course)
        self.db.flush()
        return course

    def delete(self, course: Course) -> None:
        """Hard-delete a course."""
        self.db.delete(course)
        self.db.flush()