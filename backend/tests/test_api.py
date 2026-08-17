"""API-layer tests for the Student module."""

from __future__ import annotations

import uuid

from tests.conftest import student_data


def _seed_department(db_session, code="CSE", name="Computer Science and Engineering"):
    from app.models.department import Department

    dept = Department(department_code=code, department_name=name)
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


def test_health_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_student(client, db_session):
    dept = _seed_department(db_session)
    payload = student_data(department_id=str(dept.id))

    response = client.post("/students", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["roll_number"] == "CS25001"
    assert body["status"] is True
    assert body["department_id"] == str(dept.id)
    assert body["id"] is not None


def test_create_student_defaults_status_true(client, db_session):
    dept = _seed_department(db_session)
    payload = student_data(department_id=str(dept.id))

    response = client.post("/students", json=payload)

    assert response.status_code == 201
    assert response.json()["status"] is True


def test_create_student_invalid_email(client, db_session):
    dept = _seed_department(db_session)
    payload = student_data(department_id=str(dept.id), email="not-an-email")

    response = client.post("/students", json=payload)

    assert response.status_code == 422


def test_create_student_missing_required_field(client, db_session):
    dept = _seed_department(db_session)
    payload = student_data(department_id=str(dept.id))
    del payload["name"]

    response = client.post("/students", json=payload)

    assert response.status_code == 422


def test_create_student_invalid_department(client):
    payload = student_data(department_id=str(uuid.uuid4()))

    response = client.post("/students", json=payload)

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_create_duplicate_email_conflict(client, db_session):
    dept = _seed_department(db_session)
    payload = student_data(department_id=str(dept.id))
    assert client.post("/students", json=payload).status_code == 201

    second = student_data(department_id=str(dept.id), roll_number="CS25002", email="test.student@student.college.edu")
    response = client.post("/students", json=second)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_duplicate_roll_number_conflict(client, db_session):
    dept = _seed_department(db_session)
    payload = student_data(department_id=str(dept.id))
    assert client.post("/students", json=payload).status_code == 201

    second = student_data(department_id=str(dept.id), email="other@college.edu")
    response = client.post("/students", json=second)

    assert response.status_code == 409
    assert "roll_number" in response.json()["detail"]


def test_get_student(client, db_session):
    dept = _seed_department(db_session)
    created = client.post("/students", json=student_data(department_id=str(dept.id))).json()

    response = client.get(f"/students/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_student_not_found(client):
    response = client.get(f"/students/{uuid.uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_students(client, db_session):
    dept = _seed_department(db_session)
    for roll in ["CS25001", "CS25002", "CS25003"]:
        client.post(
            "/students",
            json=student_data(department_id=str(dept.id), roll_number=roll, email=f"{roll}@college.edu"),
        )

    response = client.get("/students")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["limit"] == 10
    assert body["offset"] == 0


def test_list_students_pagination(client, db_session):
    dept = _seed_department(db_session)
    for roll in ["CS25001", "CS25002", "CS25003"]:
        client.post(
            "/students",
            json=student_data(department_id=str(dept.id), roll_number=roll, email=f"{roll}@college.edu"),
        )

    page_one = client.get("/students", params={"limit": 2, "offset": 0}).json()
    page_two = client.get("/students", params={"limit": 2, "offset": 2}).json()

    assert page_one["total"] == 3
    assert len(page_one["items"]) == 2
    assert len(page_two["items"]) == 1
    assert page_one["items"][0]["id"] != page_two["items"][0]["id"]


def test_list_students_filters(client, db_session):
    dept_a = _seed_department(db_session, "CSE", "Computer Science")
    dept_b = _seed_department(db_session, "ECE", "Electronics")
    client.post("/students", json=student_data(department_id=str(dept_a.id), roll_number="CS25001", email="a@college.edu"))
    client.post(
        "/students",
        json=student_data(
            department_id=str(dept_a.id),
            roll_number="CS25002",
            email="b@college.edu",
            semester=4,
            status=False,
            name="Filterable Student",
        ),
    )
    client.post("/students", json=student_data(department_id=str(dept_b.id), roll_number="EC25001", email="c@college.edu"))

    by_department = client.get("/students", params={"department_id": str(dept_a.id)}).json()
    assert by_department["total"] == 2

    by_semester = client.get("/students", params={"semester": 4}).json()
    assert by_semester["total"] == 1
    assert by_semester["items"][0]["roll_number"] == "CS25002"

    by_status = client.get("/students", params={"status": "false"}).json()
    assert by_status["total"] == 1

    by_search = client.get("/students", params={"search": "filterable"}).json()
    assert by_search["total"] == 1


def test_update_student(client, db_session):
    dept = _seed_department(db_session)
    created = client.post("/students", json=student_data(department_id=str(dept.id))).json()

    response = client.put(
        f"/students/{created['id']}",
        json={"name": "Renamed", "semester": 3, "section": "B"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["semester"] == 3
    assert body["section"] == "B"


def test_update_student_duplicate_email_conflict(client, db_session):
    dept = _seed_department(db_session)
    first = client.post("/students", json=student_data(department_id=str(dept.id), email="a@college.edu")).json()
    client.post("/students", json=student_data(department_id=str(dept.id), roll_number="CS25002", email="b@college.edu"))

    response = client.put(f"/students/{first['id']}", json={"email": "b@college.edu"})

    assert response.status_code == 409


def test_update_student_invalid_department(client, db_session):
    dept = _seed_department(db_session)
    created = client.post("/students", json=student_data(department_id=str(dept.id))).json()

    response = client.put(f"/students/{created['id']}", json={"department_id": str(uuid.uuid4())})

    assert response.status_code == 400


def test_update_student_not_found(client):
    response = client.put(f"/students/{uuid.uuid4()}", json={"name": "X"})

    assert response.status_code == 404


def test_delete_student_deactivates(client, db_session):
    dept = _seed_department(db_session)
    created = client.post("/students", json=student_data(department_id=str(dept.id))).json()

    response = client.delete(f"/students/{created['id']}")

    assert response.status_code == 204

    fetched = client.get(f"/students/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["status"] is False

    listed = client.get("/students", params={"status": "false"})
    assert listed.json()["total"] == 1


def test_delete_student_not_found(client):
    response = client.delete(f"/students/{uuid.uuid4()}")

    assert response.status_code == 404


def test_openapi_documents_students(client):
    schema = client.get("/openapi.json").json()

    assert "/students" in schema["paths"]
    assert "/students/{student_id}" in schema["paths"]
    for name in ["StudentCreate", "StudentUpdate", "StudentRead", "StudentList"]:
        assert name in schema["components"]["schemas"]
