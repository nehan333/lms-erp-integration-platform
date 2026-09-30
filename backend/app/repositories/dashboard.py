"""Data-access layer for Dashboard / statistics.

Contains all SQLAlchemy queries for aggregate counts and summaries.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student


class DashboardRepository:
    """Read-only aggregate queries for the ERP dashboard."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def count(self, model) -> int:
        """Return the row count for ``model``."""
        return self.db.scalar(select(func.count()).select_from(model)) or 0

    def department_count(self) -> int:
        return self.count(Department)

    def faculty_count(self) -> int:
        return self.count(Faculty)

    def student_count(self) -> int:
        return self.count(Student)

    def course_count(self) -> int:
        return self.count(Course)

    def enrollment_count(self) -> int:
        return self.count(Enrollment)

    def attendance_counts(self) -> tuple[int, int]:
        """Return ``(present, absent)`` totals."""
        rows = self.db.execute(
            select(Attendance.status, func.count()).group_by(Attendance.status)
        ).all()
        counts = {"Present": 0, "Absent": 0}
        for status, count in rows:
            counts[status] = count
        return counts["Present"], counts["Absent"]

    def grade_count(self) -> int:
        return self.count(Grade)

    def grade_distribution(self) -> list[tuple[str, int]]:
        """Return a list of ``(final_grade, count)`` tuples ordered by count desc."""
        rows = self.db.execute(
            select(Grade.final_grade, func.count().label("c"))
            .group_by(Grade.final_grade)
            .order_by(func.count().desc(), Grade.final_grade)
        ).all()
        return [(grade, count) for grade, count in rows]

    def students_by_department(self) -> list[tuple[str, str, str, int]]:
        """Return per-department ``(id, code, name, student_count)`` tuples."""
        rows = self.db.execute(
            select(
                Department.id,
                Department.department_code,
                Department.department_name,
                func.count(Student.id).label("c"),
            )
            .outerjoin(Student, Student.department_id == Department.id)
            .group_by(Department.id, Department.department_code, Department.department_name)
            .order_by(Department.department_name)
        ).all()
        return [
            (str(dept_id), code, name, count)
            for dept_id, code, name, count in rows
        ]