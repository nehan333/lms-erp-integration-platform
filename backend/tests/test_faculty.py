"""Sprint 4 — Faculty module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid

import pytest

from app.models.department import Department
from app.models.faculty import Faculty
from app.repositories.faculty import FacultyRepository
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.services.faculty import (
    DepartmentNotFoundError,
    DuplicateFacultyError,
    FacultyNotFoundError,
    FacultyService,
)
from tests.conftest import faculty_data


def _department(db_session, code="CSE", name="Computer Science") -> Department:
    dept = Department(department_code=code, department_name=name)
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


# --------------------------------------------------------------------------- #
# Repository layer
# --------------------------------------------------------------------------- #


def test_repo_create_and_get(db_session):
    dept = _department(db_session)
    repo = FacultyRepository(db_session)
    faculty = repo.create(
        {
            "employee_id": "FAC001",
            "name": "Prof A",
            "email": "a@college.edu",
            "designation": "Professor",
            "department_id": dept.id,
        }
    )
    db_session.commit()
    fetched = repo.get(faculty.id)
    assert fetched is not None
    assert fetched.employee_id == "FAC001"
    assert fetched.status is True


def test_repo_get_by_email_and_employee_id(db_session):
    dept = _department(db_session)
    db_session.add(
        Faculty(
            employee_id="FAC001",
            name="Prof A",
            email="Prof.A@College.Edu",
            designation="Professor",
            department_id=dept.id,
        )
    )
    db_session.commit()
    repo = FacultyRepository(db_session)
    assert repo.get_by_email("prof.a@college.edu") is not None
    assert repo.get_by_employee_id("FAC001") is not None
    assert repo.get_by_employee_id("NOPE") is None


def test_repo_department_exists(db_session):
    dept = _department(db_session)
    repo = FacultyRepository(db_session)
    assert repo.department_exists(dept.id) is True
    assert repo.department_exists(uuid.uuid4()) is False


def test_repo_list_pagination_and_filters(db_session):
    dept_a = _department(db_session, "CSE", "Computer Science")
    dept_b = _department(db_session, "ECE", "Electronics")
    repo = FacultyRepository(db_session)
    for i in range(3):
        repo.create(
            {
                "employee_id": f"FAC{i}",
                "name": f"Prof {i}",
                "email": f"p{i}@college.edu",
                "designation": "Professor",
                "department_id": dept_a.id,
            }
        )
        db_session.commit()
    repo.create(
        {
            "employee_id": "FACE",
            "name": "Other Prof",
            "email": "other@college.edu",
            "designation": "Assoc Professor",
            "department_id": dept_b.id,
        }
    )
    db_session.commit()

    items, total = repo.list(limit=10, offset=0)
    assert total == 4

    items, total = repo.list(limit=2, offset=0)
    assert total == 4
    assert len(items) == 2

    items, total = repo.list(limit=10, offset=0, department_id=dept_b.id)
    assert total == 1
    assert items[0].employee_id == "FACE"

    items, total = repo.list(limit=10, offset=0, search="prof 2")
    assert total == 1

    items, total = repo.list(limit=10, offset=0, search="other@college.edu")
    assert total == 1


def test_repo_update_and_soft_delete(db_session):
    dept = _department(db_session)
    repo = FacultyRepository(db_session)
    faculty = repo.create(
        {
            "employee_id": "FAC001",
            "name": "Prof A",
            "email": "a@college.edu",
            "designation": "Professor",
            "department_id": dept.id,
        }
    )
    db_session.commit()

    repo.update(faculty, {"name": "Prof Renamed", "designation": "Head"})
    db_session.commit()
    assert faculty.name == "Prof Renamed"
    assert faculty.designation == "Head"

    repo.soft_delete(faculty)
    db_session.commit()
    assert repo.get(faculty.id).status is False


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_create_success(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    faculty = service.create(FacultyCreate(**faculty_data(department_id=dept.id)))
    assert faculty.id is not None
    assert faculty.status is True


def test_service_create_invalid_department(db_session):
    service = FacultyService(db_session)
    with pytest.raises(DepartmentNotFoundError):
        service.create(FacultyCreate(**faculty_data(department_id=uuid.uuid4())))


def test_service_create_duplicate_email(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    service.create(FacultyCreate(**faculty_data(department_id=dept.id, email="dup@college.edu")))
    with pytest.raises(DuplicateFacultyError):
        service.create(
            FacultyCreate(
                **faculty_data(
                    department_id=dept.id,
                    email="dup@college.edu",
                    employee_id="FAC002",
                )
            )
        )


def test_service_create_duplicate_employee_id(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    service.create(FacultyCreate(**faculty_data(department_id=dept.id)))
    with pytest.raises(DuplicateFacultyError):
        service.create(
            FacultyCreate(
                **faculty_data(department_id=dept.id, email="other@college.edu")
            )
        )


def test_service_get_and_list(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    created = service.create(FacultyCreate(**faculty_data(department_id=dept.id)))
    assert service.get(created.id).id == created.id
    with pytest.raises(FacultyNotFoundError):
        service.get(uuid.uuid4())

    items, total = service.list_faculty(limit=10, offset=0)
    assert total == 1
    assert len(items) == 1


def test_service_update_success(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    created = service.create(FacultyCreate(**faculty_data(department_id=dept.id)))
    updated = service.update(created.id, FacultyUpdate(name="Renamed", designation="Dean"))
    assert updated.name == "Renamed"
    assert updated.designation == "Dean"


def test_service_update_duplicate_email(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    first = service.create(FacultyCreate(**faculty_data(department_id=dept.id, email="a@college.edu")))
    service.create(
        FacultyCreate(
            **faculty_data(department_id=dept.id, email="b@college.edu", employee_id="FAC002")
        )
    )
    with pytest.raises(DuplicateFacultyError):
        service.update(first.id, FacultyUpdate(email="b@college.edu"))


def test_service_update_invalid_department(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    created = service.create(FacultyCreate(**faculty_data(department_id=dept.id)))
    with pytest.raises(DepartmentNotFoundError):
        service.update(created.id, FacultyUpdate(department_id=uuid.uuid4()))


def test_service_update_missing(db_session):
    service = FacultyService(db_session)
    with pytest.raises(FacultyNotFoundError):
        service.update(uuid.uuid4(), FacultyUpdate(name="X"))


def test_service_delete_soft_deactivates(db_session):
    dept = _department(db_session)
    service = FacultyService(db_session)
    created = service.create(FacultyCreate(**faculty_data(department_id=dept.id)))
    service.delete(created.id)
    fetched = service.get(created.id)
    assert fetched.status is False


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_create_faculty(client, db_session):
    dept = _department(db_session)
    response = client.post("/faculty", json=faculty_data(department_id=str(dept.id)))
    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == "FAC001"
    assert body["status"] is True
    assert body["department_id"] == str(dept.id)


def test_api_create_faculty_invalid_email(client, db_session):
    dept = _department(db_session)
    response = client.post(
        "/faculty", json=faculty_data(department_id=str(dept.id), email="bad-email")
    )
    assert response.status_code == 422


def test_api_create_faculty_invalid_department(client):
    response = client.post(
        "/faculty", json=faculty_data(department_id=str(uuid.uuid4()))
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_api_create_duplicate_employee_id_conflict(client, db_session):
    dept = _department(db_session)
    assert client.post("/faculty", json=faculty_data(department_id=str(dept.id))).status_code == 201
    response = client.post(
        "/faculty",
        json=faculty_data(department_id=str(dept.id), email="other@college.edu"),
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_api_create_duplicate_email_conflict(client, db_session):
    dept = _department(db_session)
    assert client.post("/faculty", json=faculty_data(department_id=str(dept.id))).status_code == 201
    response = client.post(
        "/faculty",
        json=faculty_data(department_id=str(dept.id), email="test.faculty@college.edu", employee_id="FAC002"),
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_api_get_faculty(client, db_session):
    dept = _department(db_session)
    created = client.post("/faculty", json=faculty_data(department_id=str(dept.id))).json()
    response = client.get(f"/faculty/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_api_get_faculty_not_found(client):
    response = client.get(f"/faculty/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_list_faculty_filters(client, db_session):
    dept_a = _department(db_session, "CSE", "Computer Science")
    dept_b = _department(db_session, "ECE", "Electronics")
    client.post("/faculty", json=faculty_data(department_id=str(dept_a.id), employee_id="F1", email="a@college.edu"))
    client.post(
        "/faculty",
        json=faculty_data(department_id=str(dept_a.id), employee_id="F2", email="b@college.edu", status=False, name="Inactive Prof"),
    )
    client.post("/faculty", json=faculty_data(department_id=str(dept_b.id), employee_id="F3", email="c@college.edu"))

    by_dept = client.get("/faculty", params={"department_id": str(dept_a.id)}).json()
    assert by_dept["total"] == 2

    by_status = client.get("/faculty", params={"status": "false"}).json()
    assert by_status["total"] == 1

    by_search = client.get("/faculty", params={"search": "inactive"}).json()
    assert by_search["total"] == 1


def test_api_update_faculty(client, db_session):
    dept = _department(db_session)
    created = client.post("/faculty", json=faculty_data(department_id=str(dept.id))).json()
    response = client.put(f"/faculty/{created['id']}", json={"name": "Renamed", "designation": "Dean"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["designation"] == "Dean"


def test_api_update_faculty_duplicate_conflict(client, db_session):
    dept = _department(db_session)
    first = client.post("/faculty", json=faculty_data(department_id=str(dept.id), email="a@college.edu")).json()
    client.post("/faculty", json=faculty_data(department_id=str(dept.id), email="b@college.edu", employee_id="F2"))
    response = client.put(f"/faculty/{first['id']}", json={"email": "b@college.edu"})
    assert response.status_code == 409


def test_api_update_faculty_invalid_department(client, db_session):
    dept = _department(db_session)
    created = client.post("/faculty", json=faculty_data(department_id=str(dept.id))).json()
    response = client.put(f"/faculty/{created['id']}", json={"department_id": str(uuid.uuid4())})
    assert response.status_code == 400


def test_api_update_faculty_not_found(client):
    response = client.put(f"/faculty/{uuid.uuid4()}", json={"name": "X"})
    assert response.status_code == 404


def test_api_delete_faculty_deactivates(client, db_session):
    dept = _department(db_session)
    created = client.post("/faculty", json=faculty_data(department_id=str(dept.id))).json()
    response = client.delete(f"/faculty/{created['id']}")
    assert response.status_code == 204
    fetched = client.get(f"/faculty/{created['id']}")
    assert fetched.json()["status"] is False


def test_api_delete_faculty_not_found(client):
    response = client.delete(f"/faculty/{uuid.uuid4()}")
    assert response.status_code == 404


def test_openapi_documents_faculty(client):
    schema = client.get("/openapi.json").json()
    assert "/faculty" in schema["paths"]
    assert "/faculty/{faculty_id}" in schema["paths"]
    for name in ["FacultyCreate", "FacultyUpdate", "FacultyRead", "FacultyList"]:
        assert name in schema["components"]["schemas"]