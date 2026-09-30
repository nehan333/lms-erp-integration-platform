"""Pydantic v2 schemas for the Dashboard / statistics module."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GradeDistributionEntry(BaseModel):
    """A single final-grade bucket and its count."""

    model_config = ConfigDict(from_attributes=True)

    grade: str
    count: int


class DepartmentStudentCount(BaseModel):
    """A department and its number of students."""

    model_config = ConfigDict(from_attributes=True)

    department_id: str
    department_code: str
    department_name: str
    student_count: int


class OverviewStatistics(BaseModel):
    """Aggregate counts and summaries for the ERP dashboard."""

    departments: int
    faculty: int
    students: int
    courses: int
    enrollments: int
    attendance_present: int
    attendance_absent: int
    grades: int
    grade_distribution: list[GradeDistributionEntry]
    students_by_department: list[DepartmentStudentCount]