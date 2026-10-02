"""Sprint 9 — cross-cutting integration tests.

Verifies the modules work together (full data chain -> dashboard/report
aggregates), OpenAPI route completeness, and Moodle orchestration boundaries
that are not covered by the individual module suites.
"""

from __future__ import annotations

from datetime import date

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student
from app.services.dashboard import DashboardService
from app.services.moodle import MoodleSyncService


def _seed_chain(db_session):
    """Create department -> faculty -> student -> course -> enrollment ->
    grade -> attendance and return the objects."""
    dept = Department(department_code="CSE", department_name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    faculty = Faculty(
        employee_id="F1", name="Prof A", email="a@college.edu",
        designation="Professor", department_id=dept.id,
    )
    db_session.add(faculty)
    db_session.flush()

    student = Student(
        roll_number="CS25001", name="Chain Student",
        email="chain@student.college.edu", department_id=dept.id,
        semester=1, section="A",
    )
    db_session.add(student)
    db_session.flush()

    course = Course(
        course_code="CS101", course_name="Data Structures", credits=4,
        semester=1, department_id=dept.id, faculty_id=faculty.id,
    )
    db_session.add(course)
    db_session.flush()

    enrollment = Enrollment(
        student_id=student.id, course_id=course.id,
        academic_year="2025-2026", semester=1,
    )
    db_session.add(enrollment)
    db_session.flush()

    grade = Grade(
        student_id=student.id, course_id=course.id,
        internal_marks=40, external_marks=45, final_grade="A",
    )
    db_session.add(grade)
    attendance = Attendance(
        student_id=student.id, course_id=course.id,
        date=date(2025, 8, 1), status="Present",
    )
    db_session.add(attendance)
    db_session.commit()

    return {
        "dept": dept, "faculty": faculty, "student": student,
        "course": course, "enrollment": enrollment, "grade": grade,
        "attendance": attendance,
    }


def test_openapi_route_completeness(client):
    schema = client.get("/openapi.json").json()
    paths = set(schema["paths"].keys())
    expected = {
        "/health",
        "/students", "/students/{student_id}",
        "/students/bulk", "/students/{student_id}/attendance-summary",
        "/departments", "/departments/{department_id}",
        "/faculty", "/faculty/{faculty_id}",
        "/courses", "/courses/{course_id}",
        "/enrollments", "/enrollments/{enrollment_id}",
        "/enrollments/bulk", "/enrollments/bulk/preview",
        "/attendance", "/attendance/{attendance_id}",
        "/grades", "/grades/{grade_id}",
        "/dashboard/overview",
        "/reports/enrollments-by-course",
        "/reports/attendance-summary",
        "/reports/grade-distribution",
        "/reports/courses-by-department",
        "/sync-logs", "/sync-logs/{sync_log_id}",
        "/integrations/moodle/status", "/integrations/moodle/sync",
    }
    assert expected <= paths


def test_full_chain_reflected_in_dashboard(db_session):
    _seed_chain(db_session)
    overview = DashboardService(db_session).overview()
    assert overview.departments == 1
    assert overview.faculty == 1
    assert overview.students == 1
    assert overview.courses == 1
    assert overview.enrollments == 1
    assert overview.attendance_present == 1
    assert overview.attendance_absent == 0
    assert overview.grades == 1
    assert len(overview.grade_distribution) == 1
    assert overview.grade_distribution[0].grade == "A"
    assert overview.grade_distribution[0].count == 1


def test_sync_all_partial_failure_records_failed(db_session):
    from app.integrations.moodle.errors import MoodleAPIError
    from tests.test_moodle_service import FakeMoodleClient, _success_client

    _seed_chain(db_session)
    client = _success_client()
    client.error_overrides["enrol_manual_enrol_users"] = [
        MoodleAPIError("nopermissions", "cannot enrol")
    ]
    logs = MoodleSyncService(db_session, client).sync_all()
    assert len(logs) == 5
    by_action = {log.action: log.status for log in logs}
    assert by_action["sync_enrollments"] == "Failed"
    assert by_action["sync_students"] == "Success"
    assert len([l for l in logs if l.status == "Failed"]) == 1


def test_grade_update_failed_when_result_missing(db_session):
    """Honest validation: a grade response without ``result: true`` is NOT a success."""
    from tests.test_moodle_service import FakeMoodleClient, _success_client

    _seed_chain(db_session)
    client = _success_client()
    client.response_overrides["core_grades_update_grades"] = {}
    log = MoodleSyncService(db_session, client).sync_grades()
    assert log.status == "Failed"


def test_moodle_sync_logs_persisted_and_listable(db_session):
    from tests.test_moodle_service import _success_client

    _seed_chain(db_session)
    service = MoodleSyncService(db_session, _success_client())
    logs = service.sync_all()
    assert len(logs) == 5
    persisted, total = service.logger.list_logs(limit=10, offset=0, module="moodle")
    assert total == 5
    assert all(log.module == "moodle" for log in persisted)