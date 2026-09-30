"""Data-access layer for the Attendance module.

Contains all SQLAlchemy queries. No business logic lives here.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.student import Student


class AttendanceRepository:
    """CRUD and query operations for ``Attendance`` records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, attendance_id: UUID) -> Attendance | None:
        """Return the attendance record with ``attendance_id`` or ``None``."""
        return self.db.get(Attendance, attendance_id)

    def get_by_unique(
        self,
        student_id: UUID,
        course_id: UUID,
        date: date,
    ) -> Attendance | None:
        """Return the attendance record matching the unique student/course/date."""
        stmt = select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.course_id == course_id,
            Attendance.date == date,
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
        date: date | None = None,
        status: str | None = None,
    ) -> tuple[list[Attendance], int]:
        """Return a page of attendance records and the total number of matching rows."""
        conditions = []
        if student_id is not None:
            conditions.append(Attendance.student_id == student_id)
        if course_id is not None:
            conditions.append(Attendance.course_id == course_id)
        if date is not None:
            conditions.append(Attendance.date == date)
        if status is not None:
            conditions.append(Attendance.status == status)

        count_stmt = select(func.count()).select_from(Attendance)
        items_stmt = select(Attendance)
        if conditions:
            count_stmt = count_stmt.where(*conditions)
            items_stmt = items_stmt.where(*conditions)

        total = self.db.scalar(count_stmt) or 0
        items = self.db.scalars(
            items_stmt.order_by(Attendance.date.desc(), Attendance.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return list(items), total

    def create(self, data: Mapping[str, object]) -> Attendance:
        """Create and flush a new attendance record from field values."""
        attendance = Attendance(**data)
        self.db.add(attendance)
        self.db.flush()
        return attendance

    def update(self, attendance: Attendance, data: Mapping[str, object]) -> Attendance:
        """Apply field updates to an existing attendance record and flush."""
        for field, value in data.items():
            setattr(attendance, field, value)
        self.db.add(attendance)
        self.db.flush()
        return attendance

    def delete(self, attendance: Attendance) -> None:
        """Hard-delete an attendance record."""
        self.db.delete(attendance)
        self.db.flush()