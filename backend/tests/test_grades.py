"""Sprint 5 — Grade module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.grade import GradeRepository
from app.schemas.grade import GradeCreate, GradeUpdate
from app.services.grade import (
    CourseNotFoundError,
    DuplicateGradeError,
    GradeNotFoundError,
    GradeService,
    StudentNotFoundError,
)
from tests.conftest import grade_data, seed_student_and_course


# --------------------------------------------------------------------------- #
# Repository layer
# --------------------------------------------------------------------------- #


def test_repo_create_and_get(db_session):
    ctx = seed_student_and_course(db_session)
    repo = GradeRepository(db_session)
    grade = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "internal_marks": Decimal("35.50"),
            "external_marks": Decimal("45.00"),
            "final_grade": "B+",
        }
    )
    db_session.commit()
    fetched = repo.get(grade.id)
    assert fetched is not None
    assert fetched.final_grade == "B+"


def test_repo_get_by_unique(db_session):
    ctx = seed_student_and_course(db_session)
    repo = GradeRepository(db_session)
    repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "internal_marks": Decimal("35.50"),
            "external_marks": Decimal("45.00"),
            "final_grade": "B+",
        }
    )
    db_session.commit()
    assert repo.get_by_unique(ctx["student"].id, ctx["course"].id) is not None
    assert repo.get_by_unique(ctx["student"].id, uuid.uuid4()) is None


def test_repo_exists_helpers(db_session):
    ctx = seed_student_and_course(db_session)
    repo = GradeRepository(db_session)
    assert repo.student_exists(ctx["student"].id) is True
    assert repo.course_exists(ctx["course"].id) is True


def test_repo_list_pagination_and_filters(db_session):
    ctx = seed_student_and_course(db_session)
    repo = GradeRepository(db_session)
    repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "internal_marks": Decimal("35.50"),
            "external_marks": Decimal("45.00"),
            "final_grade": "B+",
        }
    )
    db_session.commit()

    items, total = repo.list(limit=10, offset=0)
    assert total == 1
    items, total = repo.list(limit=10, offset=0, student_id=ctx["student"].id)
    assert total == 1
    items, total = repo.list(limit=10, offset=0, course_id=ctx["course"].id)
    assert total == 1


def test_repo_unique_violation_raises(db_session):
    ctx = seed_student_and_course(db_session)
    repo = GradeRepository(db_session)
    repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "internal_marks": Decimal("35.50"),
            "external_marks": Decimal("45.00"),
            "final_grade": "B+",
        }
    )
    db_session.flush()
    with pytest.raises(IntegrityError):
        repo.create(
            {
                "student_id": ctx["student"].id,
                "course_id": ctx["course"].id,
                "internal_marks": Decimal("30.00"),
                "external_marks": Decimal("40.00"),
                "final_grade": "B",
            }
        )
        db_session.flush()
    db_session.rollback()


def test_repo_delete(db_session):
    ctx = seed_student_and_course(db_session)
    repo = GradeRepository(db_session)
    grade = repo.create(
        {
            "student_id": ctx["student"].id,
            "course_id": ctx["course"].id,
            "internal_marks": Decimal("35.50"),
            "external_marks": Decimal("45.00"),
            "final_grade": "B+",
        }
    )
    db_session.commit()
    repo.delete(grade)
    db_session.commit()
    assert repo.get(grade.id) is None


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_create_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    grade = service.create(
        GradeCreate(
            **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    assert grade.id is not None
    assert grade.final_grade == "B+"


def test_service_create_invalid_student(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    with pytest.raises(StudentNotFoundError):
        service.create(
            GradeCreate(
                **grade_data(student_id=uuid.uuid4(), course_id=ctx["course"].id)
            )
        )


def test_service_create_invalid_course(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    with pytest.raises(CourseNotFoundError):
        service.create(
            GradeCreate(
                **grade_data(student_id=ctx["student"].id, course_id=uuid.uuid4())
            )
        )


def test_service_create_duplicate(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    service.create(
        GradeCreate(
            **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    with pytest.raises(DuplicateGradeError):
        service.create(
            GradeCreate(
                **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
            )
        )


def test_service_get_and_list(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    created = service.create(
        GradeCreate(
            **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    assert service.get(created.id).id == created.id
    with pytest.raises(GradeNotFoundError):
        service.get(uuid.uuid4())
    items, total = service.list_grades(limit=10, offset=0)
    assert total == 1


def test_service_update_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    created = service.create(
        GradeCreate(
            **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    updated = service.update(created.id, GradeUpdate(external_marks=Decimal("60.00"), final_grade="A"))
    assert updated.external_marks == Decimal("60.00")
    assert updated.final_grade == "A"


def test_service_update_noop(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    created = service.create(
        GradeCreate(
            **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    updated = service.update(created.id, GradeUpdate())
    assert updated.final_grade == "B+"


def test_service_delete(db_session):
    ctx = seed_student_and_course(db_session)
    service = GradeService(db_session)
    created = service.create(
        GradeCreate(
            **grade_data(student_id=ctx["student"].id, course_id=ctx["course"].id)
        )
    )
    service.delete(created.id)
    with pytest.raises(GradeNotFoundError):
        service.get(created.id)


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_create_grade(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/grades",
        json=grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    )
    assert response.status_code == 201
    assert response.json()["final_grade"] == "B+"


def test_api_create_grade_missing_field(client, db_session):
    ctx = seed_student_and_course(db_session)
    payload = grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id))
    del payload["final_grade"]
    response = client.post("/grades", json=payload)
    assert response.status_code == 422


def test_api_create_grade_invalid_marks(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/grades",
        json=grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id), internal_marks="150"),
    )
    assert response.status_code == 422


def test_api_create_grade_duplicate(client, db_session):
    ctx = seed_student_and_course(db_session)
    payload = grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id))
    assert client.post("/grades", json=payload).status_code == 201
    response = client.post("/grades", json=payload)
    assert response.status_code == 409


def test_api_get_grade(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/grades",
        json=grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.get(f"/grades/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_api_get_grade_not_found(client):
    response = client.get(f"/grades/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_list_grades_filters(client, db_session):
    ctx = seed_student_and_course(db_session)
    client.post(
        "/grades",
        json=grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    )
    response = client.get("/grades", params={"course_id": str(ctx["course"].id)})
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_api_update_grade(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/grades",
        json=grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.put(f"/grades/{created['id']}", json={"final_grade": "A"})
    assert response.status_code == 200
    assert response.json()["final_grade"] == "A"


def test_api_delete_grade(client, db_session):
    ctx = seed_student_and_course(db_session)
    created = client.post(
        "/grades",
        json=grade_data(student_id=str(ctx["student"].id), course_id=str(ctx["course"].id)),
    ).json()
    response = client.delete(f"/grades/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/grades/{created['id']}").status_code == 404


def test_openapi_documents_grades(client):
    schema = client.get("/openapi.json").json()
    assert "/grades" in schema["paths"]
    assert "/grades/{grade_id}" in schema["paths"]
    for name in ["GradeCreate", "GradeUpdate", "GradeRead", "GradeList"]:
        assert name in schema["components"]["schemas"]