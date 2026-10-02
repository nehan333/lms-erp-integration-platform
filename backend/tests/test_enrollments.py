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

# --------------------------------------------------------------------------- #
# Bulk enrollment
# --------------------------------------------------------------------------- #


def _seed_cohort(db_session, *, students: int = 2):
    """Create a department, N active students, and two courses in it."""
    from app.models.course import Course
    from app.models.department import Department
    from app.models.student import Student

    dept = Department(department_code="CSE", department_name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    roster = [
        Student(
            roll_number=f"CS25{i:03d}",
            name=f"Cohort Student {i}",
            email=f"cohort{i}@student.college.edu",
            department_id=dept.id,
            semester=3,
            section="A",
        )
        for i in range(students)
    ]
    inactive = Student(
        roll_number="CS25999",
        name="Inactive Student",
        email="inactive@student.college.edu",
        department_id=dept.id,
        semester=3,
        section="A",
        status=False,
    )
    courses = [
        Course(
            course_code=code,
            course_name=name,
            credits=3,
            semester=3,
            department_id=dept.id,
        )
        for code, name in [("CS301", "Algorithms"), ("CS302", "Databases")]
    ]
    db_session.add_all(roster + [inactive] + courses)
    db_session.commit()
    return {"dept": dept, "students": roster, "inactive": inactive, "courses": courses}


def _bulk_payload(ctx, **overrides):
    payload = {
        "department_id": str(ctx["dept"].id),
        "semester": 3,
        "academic_year": "2025-2026",
        "course_ids": [str(c.id) for c in ctx["courses"]],
    }
    payload.update(overrides)
    return payload


def test_bulk_preview_counts(db_session):
    from app.schemas.enrollment import BulkEnrollmentRequest
    from app.services.enrollment import EnrollmentService

    ctx = _seed_cohort(db_session, students=3)
    service = EnrollmentService(db_session)
    payload = BulkEnrollmentRequest(**_bulk_payload(ctx))

    preview = service.bulk_preview(payload)
    assert preview.students_total == 3
    assert len(preview.courses) == 2
    assert preview.total_to_create == 6
    assert preview.total_already_enrolled == 0


def test_bulk_preview_excludes_existing_and_inactive(db_session):
    from app.schemas.enrollment import BulkEnrollmentRequest, EnrollmentCreate
    from app.services.enrollment import EnrollmentService

    ctx = _seed_cohort(db_session, students=3)
    service = EnrollmentService(db_session)
    # Pre-enroll one student in the first course.
    service.create(
        EnrollmentCreate(
            student_id=ctx["students"][0].id,
            course_id=ctx["courses"][0].id,
            academic_year="2025-2026",
            semester=3,
        )
    )

    preview = service.bulk_preview(BulkEnrollmentRequest(**_bulk_payload(ctx)))
    assert preview.students_total == 3  # inactive student not counted
    assert preview.total_already_enrolled == 1
    assert preview.total_to_create == 5
    assert preview.courses[0].to_create == 2
    assert preview.courses[0].already_enrolled == 1


def test_bulk_create_is_idempotent(db_session):
    from app.schemas.enrollment import BulkEnrollmentRequest
    from app.services.enrollment import EnrollmentService

    ctx = _seed_cohort(db_session, students=2)
    service = EnrollmentService(db_session)
    payload = BulkEnrollmentRequest(**_bulk_payload(ctx))

    result, created_ids = service.bulk_create(payload)
    assert result.created == 4
    assert result.skipped == 0
    assert len(created_ids) == 4
    assert [c.created for c in result.courses] == [2, 2]

    # Second run: everything already exists.
    result2, created_ids2 = service.bulk_create(payload)
    assert result2.created == 0
    assert result2.skipped == 4
    assert created_ids2 == []


def test_bulk_create_department_not_found(db_session):
    import uuid as uuid_mod

    from app.schemas.enrollment import BulkEnrollmentRequest
    from app.services.enrollment import DepartmentNotFoundError, EnrollmentService

    ctx = _seed_cohort(db_session)
    service = EnrollmentService(db_session)
    payload = BulkEnrollmentRequest(**_bulk_payload(ctx, department_id=str(uuid_mod.uuid4())))
    with pytest.raises(DepartmentNotFoundError):
        service.bulk_create(payload)


def test_bulk_create_course_not_found(db_session):
    import uuid as uuid_mod

    from app.schemas.enrollment import BulkEnrollmentRequest
    from app.services.enrollment import CourseNotFoundError, EnrollmentService

    ctx = _seed_cohort(db_session)
    service = EnrollmentService(db_session)
    payload = BulkEnrollmentRequest(**_bulk_payload(ctx, course_ids=[str(uuid_mod.uuid4())]))
    with pytest.raises(CourseNotFoundError):
        service.bulk_preview(payload)


def test_bulk_create_course_from_other_department(db_session):
    from app.models.course import Course
    from app.models.department import Department
    from app.schemas.enrollment import BulkEnrollmentRequest
    from app.services.enrollment import CourseNotInDepartmentError, EnrollmentService

    ctx = _seed_cohort(db_session)
    other = Department(department_code="ECE", department_name="Electronics")
    db_session.add(other)
    db_session.flush()
    foreign = Course(
        course_code="EC101", course_name="Circuits", credits=3,
        semester=3, department_id=other.id,
    )
    db_session.add(foreign)
    db_session.commit()

    service = EnrollmentService(db_session)
    payload = BulkEnrollmentRequest(
        **_bulk_payload(ctx, course_ids=[str(foreign.id)])
    )
    with pytest.raises(CourseNotInDepartmentError):
        service.bulk_preview(payload)


def test_api_bulk_preview(client, db_session):
    ctx = _seed_cohort(db_session, students=2)
    response = client.post("/enrollments/bulk/preview", json=_bulk_payload(ctx))
    assert response.status_code == 200
    body = response.json()
    assert body["students_total"] == 2
    assert body["total_to_create"] == 4
    assert body["total_already_enrolled"] == 0


def test_api_bulk_create_and_sync(client, db_session):
    from app.api import moodle as moodle_api
    from tests.test_moodle_service import _success_client

    ctx = _seed_cohort(db_session, students=2)
    fake = _success_client()
    app = client.app
    app.dependency_overrides[moodle_api.get_moodle_client] = lambda: fake

    response = client.post("/enrollments/bulk", json=_bulk_payload(ctx))
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 4
    assert body["skipped"] == 0
    assert body["sync_log"] is not None
    assert body["sync_log"]["action"] == "sync_enrollments"
    assert body["sync_log"]["status"] == "Success"
    enrol_calls = [c for c in fake.calls if c[0] == "enrol_manual_enrol_users"]
    assert len(enrol_calls) == 4
    app.dependency_overrides.pop(moodle_api.get_moodle_client, None)


def test_api_bulk_create_pending_sync_when_not_configured(client, db_session):
    from app.api import moodle as moodle_api
    from tests.test_moodle_service import FakeMoodleClient

    ctx = _seed_cohort(db_session, students=1)
    fake = FakeMoodleClient(is_configured=False)
    app = client.app
    app.dependency_overrides[moodle_api.get_moodle_client] = lambda: fake

    response = client.post("/enrollments/bulk", json=_bulk_payload(ctx))
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 2
    assert body["sync_log"]["status"] == "Failed"
    assert "pending sync" in body["sync_log"]["message"]
    app.dependency_overrides.pop(moodle_api.get_moodle_client, None)


def test_api_bulk_preview_validation_errors(client, db_session):
    import uuid as uuid_mod

    ctx = _seed_cohort(db_session)
    # Unknown department -> 404
    response = client.post(
        "/enrollments/bulk/preview",
        json=_bulk_payload(ctx, department_id=str(uuid_mod.uuid4())),
    )
    assert response.status_code == 404
    # Unknown course -> 400
    response = client.post(
        "/enrollments/bulk/preview",
        json=_bulk_payload(ctx, course_ids=[str(uuid_mod.uuid4())]),
    )
    assert response.status_code == 400
    # Empty course list -> 422 (schema validation)
    response = client.post(
        "/enrollments/bulk/preview", json=_bulk_payload(ctx, course_ids=[])
    )
    assert response.status_code == 422


def test_openapi_documents_bulk_enrollments(client):
    schema = client.get("/openapi.json").json()
    assert "/enrollments/bulk" in schema["paths"]
    assert "/enrollments/bulk/preview" in schema["paths"]
    for name in [
        "BulkEnrollmentRequest",
        "BulkEnrollmentPreview",
        "BulkEnrollmentResult",
    ]:
        assert name in schema["components"]["schemas"]
