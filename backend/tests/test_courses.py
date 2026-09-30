"""Sprint 5 — Course module tests (repository, service, and API layers)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.student import Student
from app.repositories.course import CourseRepository
from app.schemas.course import CourseCreate, CourseUpdate
from app.services.course import (
    CourseInUseError,
    CourseNotFoundError,
    CourseService,
    DepartmentNotFoundError,
    DuplicateCourseError,
    FacultyNotFoundError,
)
from tests.conftest import course_data, seed_student_and_course


def _department(db_session, code="CSE", name="Computer Science") -> Department:
    dept = Department(department_code=code, department_name=name)
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


def _faculty(db_session, dept, emp="FAC001") -> Faculty:
    faculty = Faculty(
        employee_id=emp,
        name="Prof A",
        email=f"{emp}@college.edu",
        designation="Professor",
        department_id=dept.id,
    )
    db_session.add(faculty)
    db_session.commit()
    db_session.refresh(faculty)
    return faculty


def _course(db_session, dept, faculty, code="CS101") -> Course:
    course = Course(
        course_code=code,
        course_name="Data Structures",
        credits=4,
        semester=1,
        department_id=dept.id,
        faculty_id=faculty.id,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


# --------------------------------------------------------------------------- #
# Repository layer
# --------------------------------------------------------------------------- #


def test_repo_create_and_get(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    course = _course(db_session, dept, faculty)
    repo = CourseRepository(db_session)

    fetched = repo.get(course.id)
    assert fetched is not None
    assert fetched.course_code == "CS101"
    assert fetched.faculty_id == faculty.id


def test_repo_get_by_code(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    _course(db_session, dept, faculty)
    repo = CourseRepository(db_session)
    assert repo.get_by_code("CS101") is not None
    assert repo.get_by_code("NOPE") is None


def test_repo_exists_helpers(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    repo = CourseRepository(db_session)
    assert repo.department_exists(dept.id) is True
    assert repo.department_exists(uuid.uuid4()) is False
    assert repo.faculty_exists(faculty.id) is True
    assert repo.faculty_exists(uuid.uuid4()) is False


def test_repo_list_pagination_and_filters(db_session):
    dept_a = _department(db_session, "CSE", "Computer Science")
    dept_b = _department(db_session, "ECE", "Electronics")
    fa = _faculty(db_session, dept_a, "FA")
    fb = _faculty(db_session, dept_b, "FB")
    _course(db_session, dept_a, fa, "CS101")
    _course(db_session, dept_a, fa, "CS102")
    _course(db_session, dept_b, fb, "EC101")
    repo = CourseRepository(db_session)

    items, total = repo.list(limit=10, offset=0)
    assert total == 3

    items, total = repo.list(limit=1, offset=0)
    assert len(items) == 1

    items, total = repo.list(limit=10, offset=0, department_id=dept_a.id)
    assert total == 2

    items, total = repo.list(limit=10, offset=0, faculty_id=fa.id)
    assert total == 2

    items, total = repo.list(limit=10, offset=0, semester=1)
    assert total == 3

    items, total = repo.list(limit=10, offset=0, search="data")
    assert total == 3


def test_repo_has_children(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    course = _course(db_session, dept, faculty)
    repo = CourseRepository(db_session)
    assert repo.has_children(course.id) is False

    student = Student(
        roll_number="CS25001",
        name="S",
        email="s@student.college.edu",
        department_id=dept.id,
        semester=1,
        section="A",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    db_session.add(
        Enrollment(
            student_id=student.id,
            course_id=course.id,
            academic_year="2025-2026",
            semester=1,
        )
    )
    db_session.commit()
    assert repo.has_children(course.id) is True


def test_repo_delete(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    course = _course(db_session, dept, faculty)
    repo = CourseRepository(db_session)
    repo.delete(course)
    db_session.commit()
    assert repo.get(course.id) is None


def test_repo_unique_violation_raises(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    _course(db_session, dept, faculty, "CS101")
    repo = CourseRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create(
            {
                "course_code": "CS101",
                "course_name": "Other",
                "credits": 3,
                "semester": 2,
                "department_id": dept.id,
                "faculty_id": None,
            }
        )
        db_session.flush()
    db_session.rollback()


# --------------------------------------------------------------------------- #
# Service layer
# --------------------------------------------------------------------------- #


def test_service_create_success(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    service = CourseService(db_session)
    course = service.create(
        CourseCreate(**course_data(department_id=dept.id, faculty_id=faculty.id))
    )
    assert course.id is not None
    assert course.faculty_id == faculty.id


def test_service_create_duplicate_code(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    _course(db_session, dept, faculty, "CS101")
    service = CourseService(db_session)
    with pytest.raises(DuplicateCourseError):
        service.create(
            CourseCreate(**course_data(department_id=dept.id, faculty_id=faculty.id))
        )


def test_service_create_invalid_department(db_session):
    service = CourseService(db_session)
    with pytest.raises(DepartmentNotFoundError):
        service.create(CourseCreate(**course_data(department_id=uuid.uuid4())))


def test_service_create_invalid_faculty(db_session):
    dept = _department(db_session)
    service = CourseService(db_session)
    with pytest.raises(FacultyNotFoundError):
        service.create(
            CourseCreate(**course_data(department_id=dept.id, faculty_id=uuid.uuid4()))
        )


def test_service_get_and_list(db_session):
    ctx = seed_student_and_course(db_session)
    service = CourseService(db_session)
    assert service.get(ctx["course"].id).id == ctx["course"].id
    with pytest.raises(CourseNotFoundError):
        service.get(uuid.uuid4())
    items, total = service.list_courses(limit=10, offset=0)
    assert total == 1


def test_service_update_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = CourseService(db_session)
    updated = service.update(ctx["course"].id, CourseUpdate(course_name="Renamed", credits=3))
    assert updated.course_name == "Renamed"
    assert updated.credits == 3


def test_service_update_duplicate_code(db_session):
    dept = _department(db_session)
    fa = _faculty(db_session, dept, "F1")
    _course(db_session, dept, fa, "CS101")
    other = _course(db_session, dept, fa, "CS102")
    service = CourseService(db_session)
    with pytest.raises(DuplicateCourseError):
        service.update(other.id, CourseUpdate(course_code="CS101"))


def test_service_update_invalid_department(db_session):
    ctx = seed_student_and_course(db_session)
    service = CourseService(db_session)
    with pytest.raises(DepartmentNotFoundError):
        service.update(ctx["course"].id, CourseUpdate(department_id=uuid.uuid4()))


def test_service_update_invalid_faculty(db_session):
    ctx = seed_student_and_course(db_session)
    service = CourseService(db_session)
    with pytest.raises(FacultyNotFoundError):
        service.update(ctx["course"].id, CourseUpdate(faculty_id=uuid.uuid4()))


def test_service_delete_in_use(db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    course = _course(db_session, dept, faculty)
    student = Student(
        roll_number="CS25001",
        name="S",
        email="s@student.college.edu",
        department_id=dept.id,
        semester=1,
        section="A",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    db_session.add(
        Enrollment(
            student_id=student.id, course_id=course.id, academic_year="2025-2026", semester=1
        )
    )
    db_session.commit()
    service = CourseService(db_session)
    with pytest.raises(CourseInUseError):
        service.delete(course.id)


def test_service_delete_success(db_session):
    ctx = seed_student_and_course(db_session)
    service = CourseService(db_session)
    service.delete(ctx["course"].id)
    with pytest.raises(CourseNotFoundError):
        service.get(ctx["course"].id)


# --------------------------------------------------------------------------- #
# API layer
# --------------------------------------------------------------------------- #


def test_api_create_course(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.post(
        "/courses",
        json=course_data(course_code="CS102", department_id=str(ctx["dept"].id), faculty_id=str(ctx["faculty"].id)),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["course_code"] == "CS102"
    assert body["id"] is not None


def test_api_create_course_duplicate(client, db_session):
    ctx = seed_student_and_course(db_session)
    payload = course_data(course_code="CS102", department_id=str(ctx["dept"].id), faculty_id=str(ctx["faculty"].id))
    assert client.post("/courses", json=payload).status_code == 201
    response = client.post("/courses", json=payload)
    assert response.status_code == 409


def test_api_create_course_invalid_department(client, db_session):
    response = client.post("/courses", json=course_data(department_id=str(uuid.uuid4())))
    assert response.status_code == 400


def test_api_get_course(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.get(f"/courses/{ctx['course'].id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(ctx["course"].id)


def test_api_get_course_not_found(client):
    response = client.get(f"/courses/{uuid.uuid4()}")
    assert response.status_code == 404


def test_api_list_courses_filters(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.get("/courses", params={"department_id": str(ctx["dept"].id)})
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/courses", params={"search": "data"})
    assert response.json()["total"] == 1


def test_api_update_course(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.put(
        f"/courses/{ctx['course'].id}", json={"course_name": "Renamed", "credits": 3}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["course_name"] == "Renamed"
    assert body["credits"] == 3


def test_api_update_course_duplicate(client, db_session):
    ctx = seed_student_and_course(db_session)
    second = client.post(
        "/courses",
        json=course_data(course_code="CS102", department_id=str(ctx["dept"].id), faculty_id=str(ctx["faculty"].id)),
    ).json()
    response = client.put(f"/courses/{second['id']}", json={"course_code": "CS101"})
    assert response.status_code == 409


def test_api_delete_course(client, db_session):
    ctx = seed_student_and_course(db_session)
    response = client.delete(f"/courses/{ctx['course'].id}")
    assert response.status_code == 204
    assert client.get(f"/courses/{ctx['course'].id}").status_code == 404


def test_api_delete_course_in_use(client, db_session):
    dept = _department(db_session)
    faculty = _faculty(db_session, dept)
    course = _course(db_session, dept, faculty)
    student = Student(
        roll_number="CS25001",
        name="S",
        email="s@student.college.edu",
        department_id=dept.id,
        semester=1,
        section="A",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    db_session.add(
        Enrollment(
            student_id=student.id, course_id=course.id, academic_year="2025-2026", semester=1
        )
    )
    db_session.commit()
    response = client.delete(f"/courses/{course.id}")
    assert response.status_code == 409


def test_openapi_documents_courses(client):
    schema = client.get("/openapi.json").json()
    assert "/courses" in schema["paths"]
    assert "/courses/{course_id}" in schema["paths"]
    for name in ["CourseCreate", "CourseUpdate", "CourseRead", "CourseList"]:
        assert name in schema["components"]["schemas"]