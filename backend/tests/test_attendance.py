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