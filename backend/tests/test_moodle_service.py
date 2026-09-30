"""Sprint 7 — MoodleSyncService tests (success, failure, idempotency, logging).

Uses a fake client so no real Moodle is contacted. The fake honours
``MoodleError`` semantics the same way ``MoodleClient`` does.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.integrations.moodle.errors import (
    MoodleAPIError,
    MoodleError,
    MoodleNotConfiguredError,
)
from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student
from app.services.moodle import MoodleSyncService


class FakeMoodleClient:
    """Scripted stand-in for ``MoodleClient`` used by the sync service."""

    def __init__(self, *, is_configured: bool = True) -> None:
        self.is_configured = is_configured
        self.calls: list[tuple[str, dict]] = []
        self.default_response: object = []
        self.response_overrides: dict[str, object] = {}
        self.error_overrides: dict[str, list[MoodleError]] = {}

    def call(self, wsfunction: str, params: dict) -> object:
        self.calls.append((wsfunction, params))
        if wsfunction in self.error_overrides:
            errors = self.error_overrides[wsfunction]
            if errors:
                raise errors.pop(0)
        if wsfunction in self.response_overrides:
            return self.response_overrides[wsfunction]
        return self.default_response


def _seed_erp(db_session):
    dept = Department(department_code="CSE", department_name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    faculty = Faculty(
        employee_id="F1", name="Prof A", email="a@college.edu",
        designation="Professor", department_id=dept.id,
    )
    db_session.add(faculty)
    db_session.flush()

    students = [
        Student(
            roll_number=f"CS{i:04d}", name=f"Student {i}", email=f"s{i}@student.college.edu",
            department_id=dept.id, semester=1, section="A",
        )
        for i in range(1, 3)
    ]
    db_session.add_all(students)
    db_session.flush()

    course = Course(
        course_code="CS101", course_name="Data Structures", credits=4,
        semester=1, department_id=dept.id, faculty_id=faculty.id,
    )
    db_session.add(course)
    db_session.flush()

    enrollment = Enrollment(
        student_id=students[0].id, course_id=course.id,
        academic_year="2025-2026", semester=1,
    )
    db_session.add(enrollment)
    db_session.flush()

    grade = Grade(
        student_id=students[0].id, course_id=course.id,
        internal_marks=35, external_marks=45, final_grade="B+",
    )
    db_session.add(grade)
    attendance = Attendance(
        student_id=students[0].id, course_id=course.id,
        date=date(2025, 8, 1), status="Present",
    )
    db_session.add(attendance)
    db_session.commit()

    return {
        "dept": dept, "faculty": faculty, "students": students,
        "course": course, "enrollment": enrollment, "grade": grade,
        "attendance": attendance,
    }


def _success_client() -> FakeMoodleClient:
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = [{"id": 1}]
    client.response_overrides["core_course_get_courses_by_field"] = {
        "courses": [{"id": 2}]
    }
    client.response_overrides["core_user_create_users"] = [{"id": 1}]
    client.response_overrides["core_course_create_courses"] = [{"id": 2}]
    client.response_overrides["enrol_manual_enrol_users"] = []
    client.response_overrides["core_grades_update_grades"] = {
        "result": True, "failures": [],
    }
    client.response_overrides["mod_attendance_add_take"] = []
    return client


# --------------------------------------------------------------------------- #
# sync_students
# --------------------------------------------------------------------------- #


def test_sync_students_creates_new_users(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = []
    client.response_overrides["core_user_create_users"] = [{"id": 1}]

    log = MoodleSyncService(db_session, client).sync_students()
    assert log.module == "moodle"
    assert log.action == "sync_students"
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_user_create_users"]
    assert len(created) == 2


def test_sync_students_skips_existing_users(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = [{"id": 5}]

    log = MoodleSyncService(db_session, client).sync_students()
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_user_create_users"]
    assert created == []


def test_sync_students_partial_failure(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = []
    client.error_overrides["core_user_create_users"] = [
        MoodleAPIError("invalidparameter", "bad email")
    ]

    log = MoodleSyncService(db_session, client).sync_students()
    assert log.status == "Failed"
    assert "1 of 2 students failed" in log.message
    assert "bad email" in log.message


# --------------------------------------------------------------------------- #
# sync_courses
# --------------------------------------------------------------------------- #


def test_sync_courses_creates_new_courses(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_course_get_courses_by_field"] = {"courses": []}
    client.response_overrides["core_course_create_courses"] = [{"id": 9}]

    log = MoodleSyncService(db_session, client).sync_courses()
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_course_create_courses"]
    assert len(created) == 1


def test_sync_courses_skips_existing_courses(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_course_get_courses_by_field"] = {
        "courses": [{"id": 9}]
    }

    log = MoodleSyncService(db_session, client).sync_courses()
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_course_create_courses"]
    assert created == []


# --------------------------------------------------------------------------- #
# sync_enrollments
# --------------------------------------------------------------------------- #


def test_sync_enrollments_success(db_session):
    _seed_erp(db_session)
    client = _success_client()
    log = MoodleSyncService(db_session, client).sync_enrollments()
    assert log.status == "Success"
    enrolled = [c for c in client.calls if c[0] == "enrol_manual_enrol_users"]
    assert len(enrolled) == 1


def test_sync_enrollments_failure_when_user_missing(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.response_overrides["core_user_get_users_by_field"] = []

    log = MoodleSyncService(db_session, client).sync_enrollments()
    assert log.status == "Failed"
    assert "not found in Moodle" in log.message
    assert "1 of 1 enrollments failed" in log.message


# --------------------------------------------------------------------------- #
# sync_grades
# --------------------------------------------------------------------------- #


def test_sync_grades_success(db_session):
    _seed_erp(db_session)
    client = _success_client()
    log = MoodleSyncService(db_session, client).sync_grades()
    assert log.status == "Success"
    graded = [c for c in client.calls if c[0] == "core_grades_update_grades"]
    assert len(graded) == 1
    assert graded[0][1]["grades[0][str_grade]"] == "B+"


def test_sync_grades_failure_when_result_not_true(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.response_overrides["core_grades_update_grades"] = {"result": False}

    log = MoodleSyncService(db_session, client).sync_grades()
    assert log.status == "Failed"
    assert "result not true" in log.message


# --------------------------------------------------------------------------- #
# sync_attendance
# --------------------------------------------------------------------------- #


def test_sync_attendance_success(db_session):
    _seed_erp(db_session)
    client = _success_client()
    log = MoodleSyncService(db_session, client).sync_attendance()
    assert log.status == "Success"
    submitted = [c for c in client.calls if c[0] == "mod_attendance_add_take"]
    assert len(submitted) == 1
    assert submitted[0][1]["status"] == "Present"


def test_sync_attendance_failure(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.error_overrides["mod_attendance_add_take"] = [
        MoodleAPIError("nopermissions", "not allowed")
    ]
    log = MoodleSyncService(db_session, client).sync_attendance()
    assert log.status == "Failed"
    assert "1 of 1 records failed" in log.message


# --------------------------------------------------------------------------- #
# Connection / orchestration
# --------------------------------------------------------------------------- #


def test_check_connection_returns_site_info(db_session):
    client = FakeMoodleClient()
    client.response_overrides["core_webservice_get_site_info"] = {
        "sitename": "Test LMS", "version": "2024042200",
    }
    info = MoodleSyncService(db_session, client).check_connection()
    assert info["sitename"] == "Test LMS"


def test_sync_all_records_five_logs(db_session):
    _seed_erp(db_session)
    client = _success_client()
    logs = MoodleSyncService(db_session, client).sync_all()
    assert len(logs) == 5
    assert all(log.status == "Success" for log in logs)


def test_sync_all_raises_when_not_configured(db_session):
    client = FakeMoodleClient(is_configured=False)
    with pytest.raises(MoodleNotConfiguredError):
        MoodleSyncService(db_session, client).sync_all()