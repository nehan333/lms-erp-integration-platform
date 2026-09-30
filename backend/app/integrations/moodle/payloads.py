"""Payload builders mapping ERP records to Moodle Web Services request params.

These are pure functions (no I/O) so they are trivially unit-testable. Moodle
REST uses the ``param[i][field]`` convention for repeated structures.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.config import settings
from app.models.attendance import Attendance
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.student import Student


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    if not parts:
        return "", "Student"
    return parts[0], parts[1] if len(parts) > 1 else "Student"

def user_lookup_params(roll_number: str) -> dict[str, Any]:
    """Lookup a Moodle user by ERP roll number (mapped to lowercase username)."""
    return {
        "field": "username",
        "values[0]": roll_number.lower(),
    }


def user_create_params(student: Student) -> dict[str, Any]:
    """Create a Moodle user for an ERP student (``core_user_create_users``)."""
    firstname, lastname = _split_name(student.name)
    return {
        "users[0][username]": student.roll_number.lower(),
        "users[0][password]": settings.MOODLE_DEFAULT_PASSWORD,
        "users[0][firstname]": firstname,
        "users[0][lastname]": lastname,
        "users[0][email]": student.email,
    }



def course_lookup_params(course_code: str) -> dict[str, Any]:
    """Lookup a Moodle course by ERP course code (mapped to shortname)."""
    return {"field": "shortname", "value": course_code}


def course_create_params(course: Course, category_id: int) -> dict[str, Any]:
    """Create a Moodle course from an ERP course (``core_course_create_courses``)."""
    return {
        "courses[0][fullname]": course.course_name,
        "courses[0][shortname]": course.course_code,
        "courses[0][categoryid]": str(category_id),
    }


def enrollment_params(
    moodle_user_id: int, moodle_course_id: int, role_id: int
) -> dict[str, Any]:
    """Enrol a Moodle user in a Moodle course (``enrol_manual_enrol_users``)."""
    return {
        "enrolments[0][roleid]": str(role_id),
        "enrolments[0][userid]": str(moodle_user_id),
        "enrolments[0][courseid]": str(moodle_course_id),
    }


def grade_params(
    course_code: str, rows: list[tuple[int, str]]
) -> dict[str, Any]:
    """Push final grades for one course (``core_grades_update_grades``)."""
    params: dict[str, Any] = {
        "sourceidnumber": course_code,
        "gradeitemname": "Final Grade",
    }
    for index, (moodle_user_id, final_grade) in enumerate(rows):
        params[f"grades[{index}][studentid]"] = str(moodle_user_id)
        params[f"grades[{index}][str_grade]"] = final_grade
    return params


def attendance_params(
    moodle_user_id: int,
    moodle_course_id: int,
    record: Attendance,
) -> dict[str, Any]:
    """Submit one attendance record (configurable ``mod_attendance_*`` function)."""
    timestamp = int(
        datetime.combine(record.date, datetime.min.time()).timestamp()
    )
    return {
        "courseid": str(moodle_course_id),
        "userid": str(moodle_user_id),
        "status": record.status,
        "timetaken": str(timestamp),
    }
