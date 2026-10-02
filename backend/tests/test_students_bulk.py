"""Bulk student CSV import tests (service + API layers)."""

from __future__ import annotations

import uuid

import pytest

from app.schemas.student import BulkStudentImportRequest
from app.services.student import (
    BulkImportFormatError,
    DepartmentNotFoundError,
    StudentService,
)
from tests.conftest import student_data

HEADER = "roll_number,name,email,semester,section,phone"


def _seed_department(db_session):
    from app.models.department import Department

    dept = Department(
        department_code="CSE", department_name="Computer Science"
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


def _csv_body(rows: list[str]) -> str:
    return "\n".join([HEADER, *rows])


def _payload(dept, csv_body: str, **overrides) -> BulkStudentImportRequest:
    data = {
        "csv": csv_body,
        "department_id": str(dept.id),
        "sync_moodle": False,
    }
    data.update(overrides)
    return BulkStudentImportRequest(**data)


GOOD_ROWS = [
    "CS25001,Ada Lovelace,ada@student.edu,1,A,+91 9000000001",
    "CS25002,Alan Turing,alan@student.edu,1,A,",
]


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_bulk_import_creates_all_rows(db_session):
    dept = _seed_department(db_session)
    result, created_ids = StudentService(db_session).bulk_import(
        _payload(dept, _csv_body(GOOD_ROWS))
    )
    assert result.total == 2
    assert result.created == 2
    assert result.skipped == 0
    assert result.failed == 0
    assert result.errors == []
    assert len(created_ids) == 2

    from app.models.student import Student
    from sqlalchemy import select

    rolls = set(db_session.scalars(select(Student.roll_number)).all())
    assert rolls == {"CS25001", "CS25002"}


def test_bulk_import_dry_run_writes_nothing(db_session):
    dept = _seed_department(db_session)
    result, created_ids = StudentService(db_session).bulk_import(
        _payload(dept, _csv_body(GOOD_ROWS), dry_run=True)
    )
    assert result.dry_run is True
    assert result.total == 2
    assert result.created == 0
    assert created_ids == []

    from app.models.student import Student
    from sqlalchemy import func, select

    count = db_session.scalar(select(func.count()).select_from(Student))
    assert count == 0


def test_bulk_import_skips_existing_students(db_session):
    dept = _seed_department(db_session)
    service = StudentService(db_session)
    existing = student_data(
        roll_number="CS25001", email="ada@student.edu", department_id=str(dept.id)
    )
    from app.schemas.student import StudentCreate

    service.create(StudentCreate(**existing))

    result, _ = service.bulk_import(
        _payload(dept, _csv_body(GOOD_ROWS))
    )
    assert result.total == 2
    assert result.created == 1
    assert result.skipped == 1
    assert result.failed == 0
    assert any("already exists" in e.error for e in result.errors)


def test_bulk_import_reports_row_errors(db_session):
    dept = _seed_department(db_session)
    csv_body = _csv_body([
        "CS25010,Grace Hopper,grace@student.edu,1,A,",  # good
        "CS25011,Bad Email,not-an-email,1,A,",            # invalid email
        "CS25012,,missing@student.edu,1,A,",              # missing name
        "CS25013,Bad Semester,sem@student.edu,X,A,",      # non-int semester
        "CS25014,Dup Roll,dupe1@student.edu,1,A,",        # in-file dup roll
        "CS25014,Dup Roll 2,dupe2@student.edu,1,A,",      # (second occurrence)
    ])
    result, created_ids = StudentService(db_session).bulk_import(
        _payload(dept, csv_body)
    )
    assert result.total == 6
    assert result.created == 2
    assert result.failed == 4
    assert len(result.errors) == 4
    rows = [e.row for e in result.errors]
    # header is row 1; row 6 (first CS25014) succeeds, row 7 is the in-file dup
    assert rows == [3, 4, 5, 7]
    assert len(created_ids) == 2


def test_bulk_import_partial_failure_keeps_good_rows(db_session):
    """A rejected row never poisons the rows around it (savepoints)."""
    dept = _seed_department(db_session)
    csv_body = _csv_body([
        "CS25020,Good One,one@student.edu,1,A,",
        "CS25021,Bad Email,not-an-email,1,A,",
        "CS25022,Good Two,two@student.edu,1,A,",
    ])
    result, created_ids = StudentService(db_session).bulk_import(
        _payload(dept, csv_body)
    )
    assert result.created == 2
    assert result.failed == 1
    assert len(created_ids) == 2


def test_bulk_import_rejects_missing_required_column(db_session):
    dept = _seed_department(db_session)
    bad = "roll_number,name,semester\nCS1,X,1"
    with pytest.raises(BulkImportFormatError) as exc:
        StudentService(db_session).bulk_import(_payload(dept, bad))
    assert "missing required column" in str(exc.value)


def test_bulk_import_rejects_header_only_csv(db_session):
    """Header with no data rows is a format error, not a silent success."""
    dept = _seed_department(db_session)
    with pytest.raises(BulkImportFormatError):
        StudentService(db_session).bulk_import(_payload(dept, HEADER))


def test_bulk_import_unknown_department(db_session):
    dept = _seed_department(db_session)
    payload = BulkStudentImportRequest(
        csv=_csv_body(GOOD_ROWS),
        department_id=str(uuid.uuid4()),
        sync_moodle=False,
    )
    with pytest.raises(DepartmentNotFoundError):
        StudentService(db_session).bulk_import(payload)


def test_bulk_import_handles_utf8_bom(db_session):
    dept = _seed_department(db_session)
    body = "﻿" + _csv_body(GOOD_ROWS)
    result, _ = StudentService(db_session).bulk_import(_payload(dept, body))
    assert result.created == 2


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_bulk_import_success(client, db_session):
    dept = _seed_department(db_session)
    response = client.post(
        "/students/bulk",
        json={
            "csv": _csv_body(GOOD_ROWS),
            "department_id": str(dept.id),
            "sync_moodle": False,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 2
    assert body["failed"] == 0
    assert body["sync_log"] is None
    assert body["dry_run"] is False


def test_api_bulk_import_dry_run(client, db_session):
    dept = _seed_department(db_session)
    response = client.post(
        "/students/bulk",
        json={
            "csv": _csv_body(GOOD_ROWS),
            "department_id": str(dept.id),
            "dry_run": True,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["dry_run"] is True
    assert body["created"] == 0
    assert body["total"] == 2
    # Nothing persisted.
    listed = client.get("/students").json()
    assert listed["total"] == 0


def test_api_bulk_import_with_moodle_sync(client, db_session):
    from app.api import moodle as moodle_api
    from tests.test_moodle_service import _success_client

    dept = _seed_department(db_session)
    fake = _success_client()
    # Lookups miss so the sync actually creates the two imported users.
    fake.response_overrides["core_user_get_users_by_field"] = []
    client.app.dependency_overrides[moodle_api.get_moodle_client] = (
        lambda: fake
    )

    response = client.post(
        "/students/bulk",
        json={
            "csv": _csv_body(GOOD_ROWS),
            "department_id": str(dept.id),
            "sync_moodle": True,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 2
    assert body["sync_log"] is not None
    assert body["sync_log"]["action"] == "sync_students"
    assert body["sync_log"]["status"] == "Success"
    created_calls = [c for c in fake.calls if c[0] == "core_user_create_users"]
    assert len(created_calls) == 2
    client.app.dependency_overrides.pop(moodle_api.get_moodle_client, None)


def test_api_bulk_import_bad_format_is_400(client, db_session):
    dept = _seed_department(db_session)
    response = client.post(
        "/students/bulk",
        json={"csv": "nope", "department_id": str(dept.id)},
    )
    assert response.status_code == 400


def test_api_bulk_import_unknown_department_is_400(client, db_session):
    response = client.post(
        "/students/bulk",
        json={
            "csv": _csv_body(GOOD_ROWS),
            "department_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 400


def test_openapi_documents_bulk_students(client):
    schema = client.get("/openapi.json").json()
    assert "/students/bulk" in schema["paths"]
    for name in [
        "BulkStudentImportRequest",
        "BulkStudentImportResult",
        "BulkStudentRowError",
    ]:
        assert name in schema["components"]["schemas"]
