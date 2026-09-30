"""Data-access layer for the Moodle synchronization engine.

Contains the SQLAlchemy queries that read ERP records to be pushed to Moodle.
No business logic lives here.
"""

from __future__ import annotations

from sqlalchemy import select
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

    def list_students(self) -> list[Student]:
        """Return all active students (source of truth for Moodle users)."""
        return list(
            self.db.scalars(
                select(Student).where(Student.status.is_(True))
            ).all()
        )

    def list_courses(self) -> list[Course]:
        return list(self.db.scalars(select(Course)).all())

    def list_enrollments(self) -> list[Enrollment]:
        return list(self.db.scalars(select(Enrollment)).all())

    def list_grades(self) -> list[Grade]:
        return list(self.db.scalars(select(Grade)).all())

    def list_attendance(self) -> list[Attendance]:
        return list(self.db.scalars(select(Attendance)).all())