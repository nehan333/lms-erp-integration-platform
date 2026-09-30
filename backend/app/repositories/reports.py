"""Data-access layer for Reports.

Contains all SQLAlchemy queries for report aggregates.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.grade import Grade


class ReportsRepository:
    """Read-only aggregate queries for the ERP reports."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def enrollments_by_course(self) -> list[tuple[str, str, str, int]]:
        """Return per-course ``(id, code, name, enrollment_count)`` tuples."""
        rows = self.db.execute(
            select(
                Course.id,
                Course.course_code,
                Course.course_name,
                func.count(Enrollment.id).label("c"),
            )
            .outerjoin(Enrollment, Enrollment.course_id == Course.id)
            .group_by(Course.id, Course.course_code, Course.course_name)
            .order_by(Course.course_name)
        ).all()
        return [(str(cid), code, name, count) for cid, code, name, count in rows]

    def attendance_summary(self) -> tuple[int, int, int, float]:
        """Return ``(total, present, absent, present_percent)``."""
        total = self.db.scalar(select(func.count()).select_from(Attendance)) or 0
        rows = self.db.execute(
            select(Attendance.status, func.count()).group_by(Attendance.status)
        ).all()
        counts = {"Present": 0, "Absent": 0}
        for status, count in rows:
            counts[status] = count
        present, absent = counts["Present"], counts["Absent"]
        percent = (present / total) * 100 if total else 0.0
        return total, present, absent, round(percent, 2)

    def grade_distribution(self) -> list[tuple[str, int]]:
        """Return ``(final_grade, count)`` tuples ordered by count desc."""
        rows = self.db.execute(
            select(Grade.final_grade, func.count().label("c"))
            .group_by(Grade.final_grade)
            .order_by(func.count().desc(), Grade.final_grade)
        ).all()
        return [(grade, count) for grade, count in rows]

    def courses_by_department(self) -> list[tuple[str, str, str, int]]:
        """Return per-department ``(id, code, name, course_count)`` tuples."""
        rows = self.db.execute(
            select(
                Department.id,
                Department.department_code,
                Department.department_name,
                func.count(Course.id).label("c"),
            )
            .outerjoin(Course, Course.department_id == Department.id)
            .group_by(Department.id, Department.department_code, Department.department_name)
            .order_by(Department.department_name)
        ).all()
        return [(str(did), code, name, count) for did, code, name, count in rows]