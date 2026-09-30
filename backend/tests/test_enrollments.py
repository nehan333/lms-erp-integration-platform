"""Sprint 5 — Enrollment module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enrollment import Enrollment
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.services.enrollment import (
    CourseNotFoundError,
    DuplicateEnrollmentError,
    EnrollmentNotFoundError,
    EnrollmentService,
    StudentNotFoundError,
)
from tests.conftest import enrollment_data, seed_student_and_course


# --------------------------------------------------------------------------- #
# Repository layer
# --------------------------------------------------------------------------- #


def test_repo_create_and_get(db_session):
    ctx = seed_student_and_course(db_session)
    repo = EnrollmentRepository(db_session)
    enrollment = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "academic_year": "2025-2026",
            "semester": 1,
        }
    )
    db_session.commit()
    fetched = repo.get(enrollment.id)
    assert fetched is not None
    assert fetched.student_id == ctx["student"].id


def test_repo_get_by_unique(db_session):
    ctx = seed_student_and_course(db_session)
    repo = EnrollmentRepository(db_session)
    enrollment = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "academic_year": "2025-2026",
            "semester": 1,
        }
    )
    db_session.commit()
    assert repo.get_by_unique(ctx["student"].id, ctx["course"].id, "2025-2026", 1) is not None
    assert repo.get_by_unique(ctx["student"].id, ctx["course"].id, "2026-2027", 1) is None


def test_repo_exists_helpers(db_session):
    ctx = seed_student_and_course(db_session)
    repo = EnrollmentRepository(db_session)
    assert repo.student_exists(ctx["student"].id) is True
    assert repo.student_exists(uuid.uuid4()) is False
    assert repo.course_exists(ctx["course"].id) is True
    assert repo.course_exists(uuid.uuid4()) is False


def test_repo_list_pagination_and_filters(db_session):
    ctx = seed_student_and_course(db_session)
    repo = EnrollmentRepository(db_session)
    for year in ["2025-2026", "2026-2027"]:
        repo.create(
            {
                "student_id": ctx["student"].id,
                "course_id": ctx["course"].id,
                "academic_year": year,
                "semester": 1,
            }
        )
        db_session.commit()

    items, total = repo.list(limit=10, offset=0)
    assert total == 2

    items, total = repo.list(limit=1, offset=0)
    assert len(items) == 1

    items, total = repo.list(limit=10, offset=0, academic_year="2025-2026")
    assert total == 1

    items, total = repo.list(limit=10, offset=0, student_id=ctx["student"].id)
    assert total == 2


def test_repo_unique_violation_raises(db_session):
    ctx = seed_student_and_course(db_session)
    repo = EnrollmentRepository(db_session)
    repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "academic_year": "2025-2026",
            "semester": 1,
        }
    )
    db_session.flush()
    with pytest.raises(IntegrityError):
        repo.create(
            {
                "student_id": ctx["student"].id,
                "course_id": ctx["course"].id,
                "academic_year": "2025-2026",
                "semester": 1,
            }
        )
        db_session.flush()
    db_session.rollback()


def test_repo_delete(db_session):
    ctx = seed_student_and_course(db_session)
    repo = EnrollmentRepository(db_session)
    enrollment = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "academic_year": "2025-2026",
            "semester": 1,
        }
    )
    db_session.commit()
    repo.delete(enrollment)
    db_session.commit()
    assert repo.get(enrollment.id) is None


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_create_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    enrollment = service.create(
        EnrollmentCreate(
            **enrollment_data(
                student_id=ctx["student"].id, course_id=ctx["course"].id
            )
        )
    )
    assert enrollment.id is not None


def test_service_create_invalid_student(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    with pytest.raises(StudentNotFoundError):
        service.create(
            EnrollmentCreate(
                **enrollment_data(student_id=uuid.uuid4(), course_id=ctx["course"].id)
            )
        )


def test_service_create_invalid_course(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    with pytest.raises(CourseNotFoundError):
        service.create(
            EnrollmentCreate(
                **enrollment_data(student_id=ctx["student"].id, course_id=uuid.uuid4())
            )
        )


def test_service_create_duplicate(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    service.create(
        EnrollmentCreate(
            **enrollment_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    with pytest.raises(DuplicateEnrollmentError):
        service.create(
            EnrollmentCreate(
                **enrollment_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
            )
        )


def test_service_get_and_list(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    created = service.create(
        EnrollmentCreate(
            **enrollment_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    assert service.get(created.id).id == created.id
    with pytest.raises(EnrollmentNotFoundError):
        service.get(uuid.uuid4())
    items, total = service.list_enrollments(limit=10, offset=0)
    assert total == 1


def test_service_update_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    created = service.create(
        EnrollmentCreate(
            **enrollment_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    updated = service.update(created.id, EnrollmentUpdate(academic_year="2026-2027"))
    assert updated.academic_year == "2026-2027"


def test_service_update_duplicate(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    first = service.create(
        EnrollmentCreate(
            **enrollment_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    service.create(
        EnrollmentCreate(
            **enrollment_data(
                student_id=ctx["student"].id, course_id=ctx["course"].id, academic_year="2026-2027"
            )
        )
    )
    with pytest.raises(DuplicateEnrollmentError):
        service.update(first.id, EnrollmentUpdate(academic_year="2026-2027"))


def test_service_delete(db_session):
    ctx = seed_student_and_course(db_session)
    service = EnrollmentService(db_session)
    created = service.create(
        EnrollmentCreate(
            **enrollment_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    service.delete(created.id)
    with pytest.raises(EnrollmentNotFoundError):
        service.get(created.id)


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_create_enrollment(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["student_id"] == str(ctx["student"].id)
    assert body["id"] is not None


def test_api_create_enrollment_duplicate(client, db_session):
    ctx = seed_student_and_course(db_session)
    payload = enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id))
    assert client.post("/enrollments", json=payload).status_code == 201
    response = client.post("/enrollments", json=payload)
    assert response.status_code == 409


def test_api_create_enrollment_invalid_student(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(uuid.uuid4()), course_id=str(ctx["course"].id)),
    )
    assert response.status_code == 400


def test_api_get_enrollment(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.get(f"/enrollments/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_api_get_enrollment_not_found(client):
    response = client.get(f"/enrollments/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_list_enrollments_filter(client, db_session):
    ctx = seed_student_and_course(db_session)
    client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    )
    response = client.get("/enrollments", params={"academic_year": "2025-2026"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_api_update_enrollment(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.put(f"/enrollments/{created['id']}", json={"academic_year": "2026-2027"})
    assert response.status_code == 200
    assert response.json()["academic_year"] == "2026-2027"


def test_api_update_enrollment_duplicate(client, db_session):
    ctx = seed_student_and_course(db_session)
    base = enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id))
    first = client.post("/enrollments", json=base).json()
    client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id), academic_year="2026-2027"),
    )
    response = client.put(f"/enrollments/{first['id']}", json={"academic_year": "2026-2027"})
    assert response.status_code == 409


def test_api_delete_enrollment(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/enrollments",
        json=enrollment_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.delete(f"/enrollments/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/enrollments/{created['id']}").status_code == 404


def test_openapi_documents_enrollments(client):
    schema = client.get("/openapi.json").json()
    assert "/enrollments" in schema["paths"]
    assert "/enrollments/{enrollment_id}" in schema["paths"]
    for name in ["EnrollmentCreate", "EnrollmentUpdate", "EnrollmentRead", "EnrollmentList"]:
        assert name in schema["components"]["schemas"]