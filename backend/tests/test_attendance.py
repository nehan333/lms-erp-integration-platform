"""Sprint 5 — Attendance module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.attendance import AttendanceRepository
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from app.services.attendance import (
    AttendanceNotFoundError,
    AttendanceService,
    CourseNotFoundError,
    DuplicateAttendanceError,
    StudentNotFoundError,
)
from tests.conftest import attendance_data, seed_student_and_course


# --------------------------------------------------------------------------- #
# Repository layer
# --------------------------------------------------------------------------- #


def test_repo_create_and_get(db_session):
    ctx = seed_student_and_course(db_session)
    repo = AttendanceRepository(db_session)
    record = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "date": date(2025, 8, 1),
            "status": "Present",
        }
    )
    db_session.commit()
    fetched = repo.get(record.id)
    assert fetched is not None
    assert fetched.status == "Present"


def test_repo_get_by_unique(db_session):
    ctx = seed_student_and_course(db_session)
    repo = AttendanceRepository(db_session)
    repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "date": date(2025, 8, 1),
            "status": "Present",
        }
    )
    db_session.commit()
    assert repo.get_by_unique(ctx["student"].id, ctx["course"].id, date(2025, 8, 1)) is not None
    assert repo.get_by_unique(ctx["student"].id, ctx["course"].id, date(2025, 8, 2)) is None


def test_repo_exists_helpers(db_session):
    ctx = seed_student_and_course(db_session)
    repo = AttendanceRepository(db_session)
    assert repo.student_exists(ctx["student"].id) is True
    assert repo.course_exists(ctx["course"].id) is True
    assert repo.course_exists(uuid.uuid4()) is False


def test_repo_list_pagination_and_filters(db_session):
    ctx = seed_student_and_course(db_session)
    repo = AttendanceRepository(db_session)
    for day, status in [(date(2025, 8, 1), "Present"), (date(2025, 8, 2), "Absent")]:
        repo.create(
            {
                "student_id": ctx["student"].id,
                "course_id": ctx["course"].id,
                "date": day,
                "status": status,
            }
        )
        db_session.commit()

    items, total = repo.list(limit=10, offset=0)
    assert total == 2

    items, total = repo.list(limit=1, offset=0)
    assert len(items) == 1

    items, total = repo.list(limit=10, offset=0, status="Absent")
    assert total == 1

    items, total = repo.list(limit=10, offset=0, date=date(2025, 8, 1))
    assert total == 1


def test_repo_unique_violation_raises(db_session):
    ctx = seed_student_and_course(db_session)
    repo = AttendanceRepository(db_session)
    repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "date": date(2025, 8, 1),
            "status": "Present",
        }
    )
    db_session.flush()
    with pytest.raises(IntegrityError):
        repo.create(
            {
                "student_id": ctx["student"].id,
                "course_id": ctx["course"].id,
                "date": date(2025, 8, 1),
                "status": "Absent",
            }
        )
        db_session.flush()
    db_session.rollback()


def test_repo_delete(db_session):
    ctx = seed_student_and_course(db_session)
    repo = AttendanceRepository(db_session)
    record = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "date": date(2025, 8, 1),
            "status": "Present",
        }
    )
    db_session.commit()
    repo.delete(record)
    db_session.commit()
    assert repo.get(record.id) is None


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_create_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    record = service.create(
        AttendanceCreate(
            **attendance_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    assert record.id is not None


def test_service_create_invalid_student(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    with pytest.raises(StudentNotFoundError):
        service.create(
            AttendanceCreate(
                **attendance_data(student_id=uuid.uuid4(), course_id=ctx["course"].id)
            )
        )


def test_service_create_invalid_course(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    with pytest.raises(CourseNotFoundError):
        service.create(
            AttendanceCreate(
                **attendance_data(student_id=ctx["student"].id, course_id=uuid.uuid4())
            )
        )


def test_service_create_duplicate_date(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    service.create(
        AttendanceCreate(
            **attendance_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    with pytest.raises(DuplicateAttendanceError):
        service.create(
            AttendanceCreate(
                **attendance_data(
                    student_id=ctx["student"].id, course_id=ctx["course"].id, status="Absent"
                )
            )
        )


def test_service_get_and_list(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    created = service.create(
        AttendanceCreate(
            **attendance_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    assert service.get(created.id).id == created.id
    with pytest.raises(AttendanceNotFoundError):
        service.get(uuid.uuid4())
    items, total = service.list_attendance(limit=10, offset=0)
    assert total == 1


def test_service_update_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    created = service.create(
        AttendanceCreate(
            **attendance_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    updated = service.update(created.id, AttendanceUpdate(status="Absent"))
    assert updated.status == "Absent"


def test_service_update_duplicate_date(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    created = service.create(
        AttendanceCreate(
            **attendance_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    service.create(
        AttendanceCreate(
            **attendance_data(
                student_id=ctx["student"].id,
                course_id=ctx["course"].id,
                date="2025-08-02",
            )
        )
    )
    with pytest.raises(DuplicateAttendanceError):
        service.update(created.id, AttendanceUpdate(date="2025-08-02"))


def test_service_delete(db_session):
    ctx = seed_student_and_course(db_session)
    service = AttendanceService(db_session)
    created = service.create(
        AttendanceCreate(
            **attendance_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    service.delete(created.id)
    with pytest.raises(AttendanceNotFoundError):
        service.get(created.id)


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_create_attendance(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    )
    assert response.status_code == 201
    assert response.json()["status"] == "Present"


def test_api_create_attendance_invalid_status(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id), status="Late"),
    )
    assert response.status_code == 422


def test_api_create_attendance_duplicate(client, db_session):
    ctx = seed_student_and_course(db_session)
    payload = attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id))
    assert client.post("/attendance", json=payload).status_code == 201
    response = client.post("/attendance", json=payload)
    assert response.status_code == 409


def test_api_get_attendance(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.get(f"/attendance/{created['id']}")
    assert response.status_code == 200


def test_api_get_attendance_not_found(client):
    response = client.get(f"/attendance/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_list_attendance_filters(client, db_session):
    ctx = seed_student_and_course(db_session)
    client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    )
    client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id), date="2025-08-02", status="Absent"),
    )
    response = client.get("/attendance", params={"status": "Absent"})
    assert response.json()["total"] == 1


def test_api_update_attendance(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.put(f"/attendance/{created['id']}", json={"status": "Absent"})
    assert response.status_code == 200
    assert response.json()["status"] == "Absent"


def test_api_delete_attendance(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/attendance",
        json=attendance_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.delete(f"/attendance/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/attendance/{created['id']}").status_code == 404


def test_openapi_documents_attendance(client):
    schema = client.get("/openapi.json").json()
    assert "/attendance" in schema["paths"]
    assert "/attendance/{attendance_id}" in schema["paths"]
    for name in ["AttendanceCreate", "AttendanceUpdate", "AttendanceRead", "AttendanceList"]:
        assert name in schema["components"]["schemas"]

# --------------------------------------------------------------------------- #
# Per-student attendance summary (student detail page)
# --------------------------------------------------------------------------- #


def _seed_two_course_attendance(db_session):
    """One student with attendance in two courses + an empty third course."""
    import datetime as dt

    from app.models.attendance import Attendance
    from app.models.course import Course
    from app.models.department import Department
    from app.models.student import Student

    dept = Department(department_code="CSE", department_name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    student = Student(
        roll_number="CS25001", name="Summary Student",
        email="summary@student.edu", department_id=dept.id,
        semester=1, section="A",
    )
    db_session.add(student)
    db_session.flush()

    courses = []
    for code, name in [("CS101", "Data Structures"), ("CS102", "Algorithms"),
                       ("CS103", "Databases")]:
        course = Course(
            course_code=code, course_name=name, credits=3,
            semester=1, department_id=dept.id,
        )
        db_session.add(course)
        courses.append(course)
    db_session.flush()

    # CS101: 2 present + 1 absent = 66.7%
    for offset, status in enumerate(["Present", "Present", "Absent"]):
        db_session.add(Attendance(
            student_id=student.id, course_id=courses[0].id,
            date=dt.date(2025, 8, 1 + offset), status=status,
        ))
    # CS102: 1 present = 100%
    db_session.add(Attendance(
        student_id=student.id, course_id=courses[1].id,
        date=dt.date(2025, 8, 1), status="Present",
    ))
    # CS103: no records
    db_session.commit()
    return {"dept": dept, "student": student, "courses": courses}


def test_student_attendance_summary_breakdown(db_session):
    from app.services.attendance import AttendanceService

    ctx = _seed_two_course_attendance(db_session)
    summary = AttendanceService(db_session).student_summary(ctx["student"].id)

    assert summary.student_id == ctx["student"].id
    assert [c.course_code for c in summary.courses] == ["CS101", "CS102"]
    cs101, cs102 = summary.courses
    assert (cs101.present, cs101.total, cs101.percentage) == (2, 3, 66.7)
    assert (cs102.present, cs102.total, cs102.percentage) == (1, 1, 100.0)
    # Overall: 3 of 4
    assert summary.present == 3
    assert summary.total == 4
    assert summary.percentage == 75.0


def test_student_attendance_summary_no_records(db_session):
    from app.models.student import Student
    from app.services.attendance import AttendanceService

    ctx = _seed_two_course_attendance(db_session)
    summary = AttendanceService(db_session).student_summary(ctx["student"].id)
    assert summary.percentage is not None

    # A student with zero attendance anywhere.
    empty = Student(
        roll_number="CS25002", name="No Records",
        email="empty@student.edu", department_id=ctx["dept"].id,
        semester=1, section="A",
    )
    db_session.add(empty)
    db_session.commit()

    zero = AttendanceService(db_session).student_summary(empty.id)
    assert zero.courses == []
    assert zero.total == 0
    assert zero.percentage is None  # no guessing on division by zero


def test_student_attendance_summary_unknown_student(db_session):
    import uuid

    import pytest

    from app.services.attendance import AttendanceService, StudentNotFoundError

    with pytest.raises(StudentNotFoundError):
        AttendanceService(db_session).student_summary(uuid.uuid4())


def test_api_student_attendance_summary(client, db_session):
    ctx = _seed_two_course_attendance(db_session)
    response = client.get(f"/students/{ctx['student'].id}/attendance-summary")
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == str(ctx["student"].id)
    assert len(body["courses"]) == 2
    assert body["total"] == 4
    assert body["percentage"] == 75.0
    codes = [c["course_code"] for c in body["courses"]]
    assert codes == ["CS101", "CS102"]


def test_api_student_attendance_summary_unknown_student_is_404(client, db_session):
    import uuid

    response = client.get(f"/students/{uuid.uuid4()}/attendance-summary")
    assert response.status_code == 404


def test_openapi_documents_student_attendance_summary(client):
    schema = client.get("/openapi.json").json()
    assert "/students/{student_id}/attendance-summary" in schema["paths"]
    for name in ["StudentAttendanceSummary", "StudentAttendanceCourse"]:
        assert name in schema["components"]["schemas"]
