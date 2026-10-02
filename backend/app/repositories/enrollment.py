"""Data-access layer for the Enrollment module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student


class EnrollmentRepository:
    """CRUD and query operations for ``Enrollment`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, enrollment_id: UUID) -> Enrollment | None:
        """Return the enrollment with ``enrollment_id`` or ``None``."""
        return self.db.get(Enrollment, enrollment_id)

    def get_by_unique(
        self,
        student_id: UUID,
        course_id: UUID,
        academic_year: str,
        semester: int,
    ) -> Enrollment | None:
        """Return the enrollment matching the unique student/course/year/semester."""
        stmt = select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.academic_year == academic_year,
            Enrollment.semester == semester,
        )
        return self.db.scalar(stmt)

    def student_exists(self, student_id: UUID) -> bool:
        """Return ``True`` if the referenced student exists."""
        return self.db.get(Student, student_id) is not None

    def course_exists(self, course_id: UUID) -> bool:
        """Return ``True`` if the referenced course exists."""
        return self.db.get(Course, course_id) is not None

    def list_students_for_cohort(
        self, department_id: UUID, semester: int
    ) -> list[Student]:
        """Return active students of a department at a given semester."""
        stmt = (
            select(Student)
            .where(
                Student.department_id == department_id,
                Student.semester == semester,
                Student.status.is_(True),
            )
            .order_by(Student.roll_number)
        )
        return list(self.db.scalars(stmt).all())

    def list_courses_by_ids(self, course_ids: list[UUID]) -> list[Course]:
        """Return the courses matching ``course_ids`` (order unspecified)."""
        if not course_ids:
            return []
        stmt = select(Course).where(Course.id.in_(course_ids))
        return list(self.db.scalars(stmt).all())

    def existing_pairs(
        self,
        student_ids: list[UUID],
        course_ids: list[UUID],
        academic_year: str,
        semester: int,
    ) -> set[tuple[UUID, UUID]]:
        """Return ``(student_id, course_id)`` pairs already enrolled."""
        if not student_ids or not course_ids:
            return set()
        stmt = select(Enrollment.student_id, Enrollment.course_id).where(
            Enrollment.student_id.in_(student_ids),
            Enrollment.course_id.in_(course_ids),
            Enrollment.academic_year == academic_year,
            Enrollment.semester == semester,
        )
        return {(row[0], row[1]) for row in self.db.execute(stmt).all()}

    def list(
        self,
        *,
        limit: int,
        offset: int,
        student_id: UUID | None = None,
        course_id: UUID | None = None,
        academic_year: str | None = None,
        semester: int | None = None,
    ) -> tuple[list[Enrollment], int]:
        """Return a page of enrollments and the total number of matching rows."""
        conditions = []
        if student_id is not None:
            conditions.append(Enrollment.student_id == student_id)
        if course_id is not None:
            conditions.append(Enrollment.course_id == course_id)
        if academic_year is not None:
            conditions.append(Enrollment.academic_year == academic_year)
        if semester is not None:
            conditions.append(Enrollment.semester == semester)

        count_stmt = select(func.count()).select_from(Enrollment)
        items_stmt = select(Enrollment)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(Enrollment.created_at.desc(), Enrollment.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Enrollment:
        """Create and flush a new enrollment from field values."""
        enrollment = Enrollment(**data)
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def update(self, enrollment: Enrollment, data: Mapping[str, object]) -> Enrollment:
        """Apply field updates to an existing enrollment and flush."""
        for field, value in data.items():
            setattr(enrollment, field, value)
        self.db.add(enrollment)
        self.db.flush()
        return enrollment

    def delete(self, enrollment: Enrollment) -> None:
        """Hard-delete an enrollment."""
        self.db.delete(enrollment)
        self.db.flush()