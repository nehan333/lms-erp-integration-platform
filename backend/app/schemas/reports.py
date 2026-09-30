"""Pydantic v2 schemas for the Reports module."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CourseEnrollmentReport(BaseModel):
    """A course and the number of students enrolled in it."""

    model_config = ConfigDict(from_attributes=True)

    course_id: str
    course_code: str
    course_name: str
    enrollment_count: int


class AttendanceSummaryReport(BaseModel):
    """Overall attendance totals and present percentage."""

    total: int
    present: int
    absent: int
    present_percent: float


class GradeDistributionReport(BaseModel):
    """Distribution of final grades across all grade records."""

    grade: str
    count: int


class DepartmentCourseReport(BaseModel):
    """A department and the number of courses it offers."""

    model_config = ConfigDict(from_attributes=True)

    department_id: str
    department_code: str
    department_name: str
    course_count: int