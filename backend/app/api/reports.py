"""HTTP router for the Reports module."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import (
    AttendanceSummaryReport,
    CourseEnrollmentReport,
    DepartmentCourseReport,
    GradeDistributionReport,
)
from app.services.reports import ReportsService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/enrollments-by-course",
    response_model=list[CourseEnrollmentReport],
    summary="Enrollments per course",
)
def enrollments_by_course(
    db: Annotated[Session, Depends(get_db)],
) -> list[CourseEnrollmentReport]:
    return ReportsService(db).enrollments_by_course()


@router.get(
    "/attendance-summary",
    response_model=AttendanceSummaryReport,
    summary="Overall attendance summary",
)
def attendance_summary(
    db: Annotated[Session, Depends(get_db)],
) -> AttendanceSummaryReport:
    return ReportsService(db).attendance_summary()


@router.get(
    "/grade-distribution",
    response_model=list[GradeDistributionReport],
    summary="Grade distribution",
)
def grade_distribution(
    db: Annotated[Session, Depends(get_db)],
) -> list[GradeDistributionReport]:
    return ReportsService(db).grade_distribution()


@router.get(
    "/courses-by-department",
    response_model=list[DepartmentCourseReport],
    summary="Courses per department",
)
def courses_by_department(
    db: Annotated[Session, Depends(get_db)],
) -> list[DepartmentCourseReport]:
    return ReportsService(db).courses_by_department()