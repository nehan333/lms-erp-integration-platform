"""Sprint 6 — Dashboard & Reports tests (service and API layers)."""

from __future__ import annotations

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student
from app.services.dashboard import DashboardService
from app.services.reports import ReportsService


def _seed(db_session):
    dept_cse = Department(department_code="CSE", department_name="Computer Science")
    dept_ece = Department(department_code="ECE", department_name="Electronics")
    db_session.add_all([dept_cse, dept_ece])
    db_session.flush()

    faculty = Faculty(
        employee_id="F1", name="Prof A", email="a@college.edu",
        designation="Professor", department_id=dept_cse.id,
    )
    db_session.add(faculty)
    db_session.flush()

    students = [
        Student(
            roll_number=f"S{i}",
            name=f"Student {i}",
            email=f"s{i}@student.college.edu",
            department_id=dept_cse.id if i % 2 == 0 else dept_ece.id,
            semester=1,
            section="A",
        )
        for i in range(4)
    ]
    db_session.add_all(students)
    db_session.flush()

    course = Course(
        course_code="CS101", course_name="Data Structures", credits=4,
        semester=1, department_id=dept_cse.id, faculty_id=faculty.id,
    )
    db_session.add(course)
    db_session.flush()

    enrollments = [
        Enrollment(
            student_id=s.id, course_id=course.id,
            academic_year="2025-2026", semester=1,
        )
        for s in students
    ]
    db_session.add_all(enrollments)
    db_session.flush()

    attendance = [
        Attendance(student_id=students[0].id, course_id=course.id, date=__import__("datetime").date(2025, 8, 1), status="Present"),
        Attendance(student_id=students[0].id, course_id=course.id, date=__import__("datetime").date(2025, 8, 2), status="Absent"),
    ]
    db_session.add_all(attendance)
    grades = [
        Grade(student_id=students[0].id, course_id=course.id,
              internal_marks=35, external_marks=45, final_grade="B+"),
        Grade(student_id=students[1].id, course_id=course.id,
              internal_marks=45, external_marks=50, final_grade="A"),
    ]
    db_session.add_all(grades)
    db_session.commit()
    for obj in [dept_cse, dept_ece, faculty, course, *students, *enrollments, *attendance, *grades]:
        db_session.refresh(obj)
    return {
        "depts": [dept_cse, dept_ece], "faculty": faculty,
        "students": students, "course": course,
    }


# --------------------------------------------------------------------------- #
# Dashboard service
# --------------------------------------------------------------------------- #


def test_overview_counts(db_session):
    _seed(db_session)
    overview = DashboardService(db_session).overview()
    assert overview.departments == 2
    assert overview.faculty == 1
    assert overview.students == 4
    assert overview.courses == 1
    assert overview.enrollments == 4
    assert overview.attendance_present == 1
    assert overview.attendance_absent == 1
    assert overview.grades == 2


def test_overview_grade_distribution(db_session):
    _seed(db_session)
    overview = DashboardService(db_session).overview()
    grades = {g.grade: g.count for g in overview.grade_distribution}
    assert grades["B+"] == 1
    assert grades["A"] == 1


def test_overview_students_by_department(db_session):
    _seed(db_session)
    overview = DashboardService(db_session).overview()
    by_dept = {d.department_code: d.student_count for d in overview.students_by_department}
    assert by_dept["CSE"] == 2
    assert by_dept["ECE"] == 2


def test_overview_empty_database(db_session):
    overview = DashboardService(db_session).overview()
    assert overview.departments == 0
    assert overview.students == 0
    assert overview.grades == 0
    assert overview.attendance_present == 0
    assert overview.grade_distribution == []


# --------------------------------------------------------------------------- #
# Reports service
# --------------------------------------------------------------------------- #


def test_enrollments_by_course(db_session):
    _seed(db_session)
    rows = ReportsService(db_session).enrollments_by_course()
    assert len(rows) == 1
    assert rows[0].course_code == "CS101"
    assert rows[0].enrollment_count == 4


def test_attendance_summary(db_session):
    _seed(db_session)
    summary = ReportsService(db_session).attendance_summary()
    assert summary.total == 2
    assert summary.present == 1
    assert summary.absent == 1
    assert summary.present_percent == 50.0


def test_attendance_summary_empty(db_session):
    summary = ReportsService(db_session).attendance_summary()
    assert summary.total == 0
    assert summary.present == 0
    assert summary.absent == 0
    assert summary.present_percent == 0.0


def test_grade_distribution_report(db_session):
    _seed(db_session)
    rows = ReportsService(db_session).grade_distribution()
    order = {g.grade: g.count for g in rows}
    assert order["A"] == 1
    assert order["B+"] == 1


def test_courses_by_department(db_session):
    _seed(db_session)
    rows = ReportsService(db_session).courses_by_department()
    by_dept = {d.department_code: d.course_count for d in rows}
    assert by_dept["CSE"] == 1
    assert by_dept["ECE"] == 0


# --------------------------------------------------------------------------- #
# Dashboard + Reports API
# --------------------------------------------------------------------------- #


def test_api_dashboard_overview(client, db_session):
    _seed(db_session)
    response = client.get("/dashboard/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["departments"] == 2
    assert body["students"] == 4
    assert "grade_distribution" in body
    assert "students_by_department" in body


def test_api_enrollments_by_course(client, db_session):
    _seed(db_session)
    response = client.get("/reports/enrollments-by-course")
    assert response.status_code == 200
    assert response.json()[0]["course_code"] == "CS101"


def test_api_attendance_summary(client, db_session):
    _seed(db_session)
    response = client.get("/reports/attendance-summary")
    assert response.status_code == 200
    assert response.json()["present_percent"] == 50.0


def test_api_grade_distribution(client, db_session):
    _seed(db_session)
    response = client.get("/reports/grade-distribution")
    assert response.status_code == 200
    assert response.json()[0]["grade"] == "A"


def test_api_courses_by_department(client, db_session):
    _seed(db_session)
    response = client.get("/reports/courses-by-department")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_openapi_documents_dashboard_reports(client):
    schema = client.get("/openapi.json").json()
    assert "/dashboard/overview" in schema["paths"]
    assert "/reports/enrollments-by-course" in schema["paths"]
    assert "/reports/attendance-summary" in schema["paths"]
    assert "/reports/grade-distribution" in schema["paths"]
    assert "/reports/courses-by-department" in schema["paths"]
    for name in ["OverviewStatistics", "AttendanceSummaryReport", "GradeDistributionReport"]:
        assert name in schema["components"]["schemas"]