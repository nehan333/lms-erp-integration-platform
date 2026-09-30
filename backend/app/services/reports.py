"""Business logic for the Reports module."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.reports import ReportsRepository
from app.schemas.reports import (
    AttendanceSummaryReport,
    CourseEnrollmentReport,
    DepartmentCourseReport,
    GradeDistributionReport,
)


class ReportsService:
    """Coordinates aggregate queries for the ERP reports."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ReportsRepository(db)

    def enrollments_by_course(self) -> list[CourseEnrollmentReport]:
        return [
            CourseEnrollmentReport(
                course_id=cid,
                course_code=code,
                course_name=name,
                enrollment_count=count,
            )
            for cid, code, name, count in self.repo.enrollments_by_course()
        ]

    def attendance_summary(self) -> AttendanceSummaryReport:
        total, present, absent, percent = self.repo.attendance_summary()
        return AttendanceSummaryReport(
            total=total,
            present=present,
            absent=absent,
            present_percent=percent,
        )

    def grade_distribution(self) -> list[GradeDistributionReport]:
        return [
            GradeDistributionReport(grade=grade, count=count)
            for grade, count in self.repo.grade_distribution()
        ]

    def courses_by_department(self) -> list[DepartmentCourseReport]:
        return [
            DepartmentCourseReport(
                department_id=did,
                department_code=code,
                department_name=name,
                course_count=count,
            )
            for did, code, name, count in self.repo.courses_by_department()
        ]