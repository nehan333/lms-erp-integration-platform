"""Business logic for the Dashboard / statistics module."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import (
    DepartmentStudentCount,
    GradeDistributionEntry,
    OverviewStatistics,
)


class DashboardService:
    """Coordinates aggregate queries for the ERP dashboard."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DashboardRepository(db)

    def overview(self) -> OverviewStatistics:
        """Return aggregate counts and summaries for the dashboard."""
        present, absent = self.repo.attendance_counts()
        distribution = [
            GradeDistributionEntry(grade=grade, count=count)
            for grade, count in self.repo.grade_distribution()
        ]
        by_department = [
            DepartmentStudentCount(
                department_id=did,
                department_code=code,
                department_name=name,
                student_count=count,
            )
            for did, code, name, count in self.repo.students_by_department()
        ]
        return OverviewStatistics(
            departments=self.repo.department_count(),
            faculty=self.repo.faculty_count(),
            students=self.repo.student_count(),
            courses=self.repo.course_count(),
            enrollments=self.repo.enrollment_count(),
            attendance_present=present,
            attendance_absent=absent,
            grades=self.repo.grade_count(),
            grade_distribution=distribution,
            students_by_department=by_department,
        )