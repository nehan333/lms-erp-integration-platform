"""Business logic for the Attendance module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.repositories.attendance import AttendanceRepository
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


class AttendanceNotFoundError(Exception):
    """Raised when an attendance record does not exist."""

    def __init__(self, attendance_id: UUID) -> None:
        super().__init__(f"Attendance {attendance_id} not found")
        self.attendance_id = attendance_id


class DuplicateAttendanceError(Exception):
    """Raised when an attendance record for the same student/course/date exists."""

    def __init__(self, student_id: UUID, course_id: UUID, date: date) -> None:
        super().__init__(
            f"Attendance for student {student_id} in course {course_id} "
            f"on {date} already exists"
        )
        self.student_id = student_id
        self.course_id = course_id
        self.date = date


class StudentNotFoundError(Exception):
    """Raised when a referenced student does not exist."""

    def __init__(self, student_id: UUID) -> None:
        super().__init__(f"Student {student_id} not found")
        self.student_id = student_id


class CourseNotFoundError(Exception):
    """Raised when a referenced course does not exist."""

    def __init__(self, course_id: UUID) -> None:
        super().__init__(f"Course {course_id} not found")
        self.course_id = course_id


class AttendanceService:
    """Coordinates validation and repository operations for attendance."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AttendanceRepository(db)

    def create(self, payload: AttendanceCreate) -> Attendance:
        if not self.repo.student_exists(payload.student_id):
            raise StudentNotFoundError(payload.student_id)
        if not self.repo.course_exists(payload.course_id):
            raise CourseNotFoundError(payload.course_id)
        if self.repo.get_by_unique(payload.student_id, payload.course_id, payload.date):
            raise DuplicateAttendanceError(
                payload.student_id, payload.course_id, payload.date
            )

        try:
            attendance = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateAttendanceError(
                payload.student_id, payload.course_id, payload.date
            ) from exc
        self.db.refresh(attendance)
        return attendance

    def get(self, attendance_id: UUID) -> Attendance:
        attendance = self.repo.get(attendance_id)
        if attendance is None:
            raise AttendanceNotFoundError(attendance_id)
        return attendance

    def list_attendance(
        self,
        *,
        limit: int,
        offset: int,
        student_id: UUID | None = None,
        course_id: UUID | None = None,
        date: date | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Attendance], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            student_id=student_id,
            course_id=course_id,
            date=date,
            status=status,
        )

    def update(self, attendance_id: UUID, payload: AttendanceUpdate) -> Attendance:
        attendance = self.get(attendance_id)
        data = payload.model_dump(exclude_unset=True)

        new_student = data.get("student_id", attendance.student_id)
        new_course = data.get("course_id", attendance.course_id)
        new_date = data.get("date", attendance.date)

        if "student_id" in data and not self.repo.student_exists(data["student_id"]):
            raise StudentNotFoundError(data["student_id"])
        if "course_id" in data and not self.repo.course_exists(data["course_id"]):
            raise CourseNotFoundError(data["course_id"])

        existing = self.repo.get_by_unique(new_student, new_course, new_date)
        if existing is not None and existing.id != attendance.id:
            raise DuplicateAttendanceError(new_student, new_course, new_date)

        if not data:
            return attendance

        try:
            attendance = self.repo.update(attendance, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateAttendanceError(new_student, new_course, new_date) from exc
        self.db.refresh(attendance)
        return attendance

    def delete(self, attendance_id: UUID) -> None:
        attendance = self.get(attendance_id)
        self.repo.delete(attendance)
        self.db.commit()