"""Sprint 4 — Department module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.department import (
    DepartmentInUseError,
    DepartmentNotFoundError,
    DepartmentService,
    DuplicateDepartmentError,
)
from tests.conftest import department_data


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
    repo = DepartmentRepository(db_session)

    fetched = repo.get(dept.id)
    assert fetched is not None
    assert fetched.department_code == "CSE"
    assert fetched.department_name == "Computer Science"


def test_repo_get_by_code_and_name(db_session):
    _department(db_session)
    repo = DepartmentRepository(db_session)

    assert repo.get_by_code("CSE") is not None
    assert repo.get_by_code("EEE") is None
    assert repo.get_by_name("computer science") is not None
    assert repo.get_by_name("nonexistent") is None


def test_repo_exists(db_session):
    dept = _department(db_session)
    repo = DepartmentRepository(db_session)

    assert repo.exists(dept.id) is True
    assert repo.exists(uuid.uuid4()) is False


def test_repo_list_pagination_and_search(db_session):
    _department(db_session, "CSE", "Computer Science")
    _department(db_session, "ECE", "Electronics")
    _department(db_session, "CIV", "Civil Engineering")

    repo = DepartmentRepository(db_session)

    items, total = repo.list(limit=10, offset=0)
    assert total == 3
    assert len(items) == 3

    items, total = repo.list(limit=2, offset=0)
    assert total == 3
    assert len(items) == 2

    items, total = repo.list(limit=10, offset=0, search="science")
    assert total == 1
    assert items[0].department_code == "CSE"


def test_repo_has_children(db_session):
    dept = _department(db_session)
    repo = DepartmentRepository(db_session)
    assert repo.has_children(dept.id) is False

    from app.models.faculty import Faculty

    db_session.add(
        Faculty(
            employee_id="F1",
            name="Prof A",
            email="a@college.edu",
            designation="Professor",
            department_id=dept.id,
        )
    )
    db_session.commit()
    assert repo.has_children(dept.id) is True


def test_repo_create_update_delete(db_session):
    repo = DepartmentRepository(db_session)
    dept = repo.create({"department_code": "MEC", "department_name": "Mechanical"})
    db_session.commit()
    assert dept.id is not None

    repo.update(dept, {"department_name": "Mechanical Engineering"})
    db_session.commit()
    assert repo.get(dept.id).department_name == "Mechanical Engineering"

    repo.delete(dept)
    db_session.commit()
    assert repo.get(dept.id) is None


def test_repo_unique_violation_raises(db_session):
    _department(db_session, "CSE", "Computer Science")
    repo = DepartmentRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create({"department_code": "CSE", "department_name": "Other"})
        db_session.flush()
    db_session.rollback()


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_create_success(db_session):
    service = DepartmentService(db_session)
    dept = service.create(DepartmentCreate(**department_data()))
    assert dept.id is not None
    assert dept.department_code == "CSE"


def test_service_create_duplicate_code(db_session):
    _department(db_session, "CSE", "Computer Science")
    service = DepartmentService(db_session)
    with pytest.raises(DuplicateDepartmentError):
        service.create(DepartmentCreate(**department_data()))


def test_service_create_duplicate_name(db_session):
    _department(db_session, "ECE", "Computer Science and Engineering")
    service = DepartmentService(db_session)
    with pytest.raises(DuplicateDepartmentError):
        service.create(DepartmentCreate(**department_data(department_code="XXX")))


def test_service_get_existing_and_missing(db_session):
    dept = _department(db_session)
    service = DepartmentService(db_session)
    assert service.get(dept.id).id == dept.id
    with pytest.raises(DepartmentNotFoundError):
        service.get(uuid.uuid4())


def test_service_list(db_session):
    _department(db_session, "CSE", "Computer Science")
    _department(db_session, "ECE", "Electronics")
    service = DepartmentService(db_session)
    items, total = service.list_departments(limit=10, offset=0)
    assert total == 2
    assert len(items) == 2


def test_service_update_success(db_session):
    dept = _department(db_session)
    service = DepartmentService(db_session)
    updated = service.update(dept.id, DepartmentUpdate(department_name="Comps Science"))
    assert updated.department_name == "Comps Science"


def test_service_update_duplicate(db_session):
    _department(db_session, "CSE", "Computer Science")
    other = _department(db_session, "ECE", "Electronics")
    service = DepartmentService(db_session)
    with pytest.raises(DuplicateDepartmentError):
        service.update(other.id, DepartmentUpdate(department_code="CSE"))


def test_service_delete_in_use(db_session):
    dept = _department(db_session)
    from app.models.faculty import Faculty

    db_session.add(
        Faculty(
            employee_id="F1",
            name="Prof A",
            email="a@college.edu",
            designation="Professor",
            department_id=dept.id,
        )
    )
    db_session.commit()

    service = DepartmentService(db_session)
    with pytest.raises(DepartmentInUseError):
        service.delete(dept.id)


def test_service_delete_success(db_session):
    dept = _department(db_session)
    service = DepartmentService(db_session)
    service.delete(dept.id)
    with pytest.raises(DepartmentNotFoundError):
        service.get(dept.id)


def test_service_delete_missing(db_session):
    service = DepartmentService(db_session)
    with pytest.raises(DepartmentNotFoundError):
        service.delete(uuid.uuid4())


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_list_departments(client):
    response = client.get("/departments")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body and "total" in body


def test_api_create_department(client):
    response = client.post("/departments", json=department_data())
    assert response.status_code == 201
    body = response.json()
    assert body["department_code"] == "CSE"
    assert body["id"] is not None


def test_api_create_duplicate_department(client, db_session):
    _department(db_session)
    response = client.post("/departments", json=department_data())
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_api_get_department(client, db_session):
    dept = _department(db_session)
    response = client.get(f"/departments/{dept.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(dept.id)


def test_api_get_department_not_found(client):
    response = client.get(f"/departments/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_update_department(client, db_session):
    dept = _department(db_session)
    response = client.put(
        f"/departments/{dept.id}", json={"department_name": "Renamed"}
    )
    assert response.status_code == 200
    assert response.json()["department_name"] == "Renamed"


def test_api_update_department_duplicate(client, db_session):
    _department(db_session, "CSE", "Computer Science")
    other = _department(db_session, "ECE", "Electronics")
    response = client.put(
        f"/departments/{other.id}", json={"department_code": "CSE"}
    )
    assert response.status_code == 409


def test_api_delete_department(client, db_session):
    dept = _department(db_session)
    response = client.delete(f"/departments/{dept.id}")
    assert response.status_code == 204
    assert client.get(f"/departments/{dept.id}").status_code == 404


def test_api_delete_department_in_use(client, db_session):
    dept = _department(db_session)
    from app.models.faculty import Faculty

    db_session.add(
        Faculty(
            employee_id="F1",
            name="Prof A",
            email="a@college.edu",
            designation="Professor",
            department_id=dept.id,
        )
    )
    db_session.commit()
    response = client.delete(f"/departments/{dept.id}")
    assert response.status_code == 409


def test_api_delete_department_not_found(client):
    response = client.delete(f"/departments/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_list_departments_search(client, db_session):
    _department(db_session, "CSE", "Computer Science")
    _department(db_session, "ECE", "Electronics")
    response = client.get("/departments", params={"search": "electronics"})
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["department_code"] == "ECE"


def test_openapi_documents_departments(client):
    schema = client.get("/openapi.json").json()
    assert "/departments" in schema["paths"]
    assert "/departments/{department_id}" in schema["paths"]
    for name in ["DepartmentCreate", "DepartmentUpdate", "DepartmentRead", "DepartmentList"]:
        assert name in schema["components"]["schemas"]