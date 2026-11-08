"""Data-access layer for the Moodle synchronization engine.

Contains the SQLAlchemy queries that read ERP records to be pushed to Moodle.
No business logic lives here.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.student import Student


class MoodleSyncRepository:
    """Reads ERP records needed by the synchronization engine."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_students(
        self, student_ids: list[UUID] | None = None
    ) -> list[Student]:
        """Return active students, optionally limited to the given ids."""
        statement = select(Student).where(Student.status.is_(True))
        if student_ids is not None:
            if not student_ids:
                return []
            statement = statement.where(Student.id.in_(student_ids))
        return list(self.db.scalars(statement).all())

    def list_courses(self) -> list[Course]:
        return list(self.db.scalars(select(Course)).all())

    def list_enrollments(
        self, enrollment_ids: list[UUID] | None = None
    ) -> list[Enrollment]:
        """Return enrollments, optionally limited to the given ids."""
        statement = select(Enrollment)
        if enrollment_ids is not None:
            if not enrollment_ids:
                return []
            statement = statement.where(Enrollment.id.in_(enrollment_ids))
        return list(self.db.scalars(statement).all())

    def list_grades(self) -> list[Grade]:
        return list(self.db.scalars(select(Grade)).all())

    def list_attendance(self) -> list[Attendance]:
        return list(self.db.scalars(select(Attendance)).all())

    def earliest_attendance_dates(self) -> dict[UUID, date]:
        """First ERP attendance date per course (empty when none recorded).

        Used to anchor Moodle course start dates so attendance sessions are
        never filtered out of the student's "This course" view.
        """
        statement = select(
            Attendance.course_id, func.min(Attendance.date)
        ).group_by(Attendance.course_id)
        return {course_id: min_date for course_id, min_date in self.db.execute(statement)}