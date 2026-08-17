"""Service-layer tests for the Student module."""

from __future__ import annotations

import uuid

import pytest

from app.models.department import Department
from app.schemas.student import StudentCreate, StudentUpdate
from app.services.student import (
    DepartmentNotFoundError,
    DuplicateStudentError,
    StudentNotFoundError,
    StudentService,
)
from tests.conftest import student_data


def _department(db_session, code="CSE", name="Computer Science and Engineering") -> Department:
    dept = Department(department_code=code, department_name=name)
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


def _payload(**overrides) -> StudentCreate:
    return StudentCreate(**student_data(**overrides))


def test_create_success(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)

    student = service.create(_payload(department_id=dept.id))

    assert student.id is not None
    assert student.roll_number == "CS25001"
    assert student.status is True


def test_create_duplicate_email(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    service.create(_payload(department_id=dept.id, email="dup@college.edu", roll_number="CS25001"))

    with pytest.raises(DuplicateStudentError) as exc:
        service.create(_payload(department_id=dept.id, email="dup@college.edu", roll_number="CS25002"))
    assert exc.value.field == "email"


def test_create_duplicate_email_case_insensitive(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    service.create(_payload(department_id=dept.id, email="dup@college.edu", roll_number="CS25001"))

    with pytest.raises(DuplicateStudentError):
        service.create(_payload(department_id=dept.id, email="DUP@College.Edu", roll_number="CS25002"))


def test_create_duplicate_roll_number(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    service.create(_payload(department_id=dept.id, email="first@college.edu", roll_number="CS26001"))

    with pytest.raises(DuplicateStudentError) as exc:
        service.create(_payload(department_id=dept.id, email="second@college.edu", roll_number="CS26001"))
    assert exc.value.field == "roll_number"


def test_create_invalid_department(db_session):
    service = StudentService(db_session)
    with pytest.raises(DepartmentNotFoundError):
        service.create(_payload(department_id=uuid.uuid4()))


def test_get_existing_and_missing(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    created = service.create(_payload(department_id=dept.id))

    assert service.get(created.id).id == created.id

    with pytest.raises(StudentNotFoundError):
        service.get(uuid.uuid4())


def test_list_students(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    service.create(_payload(department_id=dept.id, roll_number="CS25001", email="a@college.edu"))
    service.create(_payload(department_id=dept.id, roll_number="CS25002", email="b@college.edu"))

    items, total = service.list_students(limit=10, offset=0)
    assert total == 2
    assert len(items) == 2

    items, total = service.list_students(limit=1, offset=0)
    assert total == 2
    assert len(items) == 1


def test_update_success(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    created = service.create(_payload(department_id=dept.id))

    updated = service.update(
        created.id,
        StudentUpdate(name="Updated Name", semester=4, section="B"),
    )
    assert updated.name == "Updated Name"
    assert updated.semester == 4
    assert updated.section == "B"


def test_update_no_changes_is_noop(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    created = service.create(_payload(department_id=dept.id))

    updated = service.update(created.id, StudentUpdate())
    assert updated.name == "Test Student"


def test_update_duplicate_email_with_other_student(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    first = service.create(_payload(department_id=dept.id, email="a@college.edu", roll_number="CS25001"))
    service.create(_payload(department_id=dept.id, email="b@college.edu", roll_number="CS25002"))

    with pytest.raises(DuplicateStudentError):
        service.update(first.id, StudentUpdate(email="b@college.edu"))


def test_update_keeps_own_email(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    created = service.create(_payload(department_id=dept.id, email="a@college.edu", roll_number="CS25001"))

    updated = service.update(created.id, StudentUpdate(email="a@college.edu"))
    assert updated.email == "a@college.edu"


def test_update_duplicate_roll_number(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    first = service.create(_payload(department_id=dept.id, email="a@college.edu", roll_number="CS25001"))
    service.create(_payload(department_id=dept.id, email="b@college.edu", roll_number="CS25002"))

    with pytest.raises(DuplicateStudentError):
        service.update(first.id, StudentUpdate(roll_number="CS25002"))


def test_update_invalid_department(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    created = service.create(_payload(department_id=dept.id))

    with pytest.raises(DepartmentNotFoundError):
        service.update(created.id, StudentUpdate(department_id=uuid.uuid4()))


def test_update_missing_student(db_session):
    service = StudentService(db_session)
    with pytest.raises(StudentNotFoundError):
        service.update(uuid.uuid4(), StudentUpdate(name="X"))


def test_delete_soft_deactivates(db_session):
    dept = _department(db_session)
    service = StudentService(db_session)
    created = service.create(_payload(department_id=dept.id))

    service.delete(created.id)

    fetched = service.get(created.id)
    assert fetched.status is False


def test_delete_missing_student(db_session):
    service = StudentService(db_session)
    with pytest.raises(StudentNotFoundError):
        service.delete(uuid.uuid4())
