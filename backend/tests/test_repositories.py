"""Repository-layer tests for the Student module."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.department import Department
from app.models.student import Student
from app.repositories.student import StudentRepository


def _create_department(db_session, code="CSE", name="Computer Science and Engineering") -> Department:
    dept = Department(department_code=code, department_name=name)
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


def _create_student(db_session, dept, roll="CS25001", email="repo.student@student.college.edu", name="Repo Student") -> Student:
    student = Student(
        roll_number=roll,
        name=name,
        email=email,
        department_id=dept.id,
        semester=1,
        section="A",
        status=True,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def test_create_and_get(db_session):
    dept = _create_department(db_session)
    student = _create_student(db_session, dept)
    repo = StudentRepository(db_session)

    fetched = repo.get(student.id)
    assert fetched is not None
    assert fetched.id == student.id
    assert fetched.roll_number == "CS25001"
    assert fetched.status is True


def test_get_missing_returns_none(db_session):
    _create_department(db_session)
    repo = StudentRepository(db_session)
    assert repo.get(__import__("uuid").uuid4()) is None


def test_get_by_email_case_insensitive(db_session):
    dept = _create_department(db_session)
    _create_student(db_session, dept, email="Repo.Student@College.Edu")
    repo = StudentRepository(db_session)

    assert repo.get_by_email("repo.student@college.edu") is not None
    assert repo.get_by_email("nobody@college.edu") is None


def test_get_by_roll_number(db_session):
    dept = _create_department(db_session)
    _create_student(db_session, dept)
    repo = StudentRepository(db_session)

    assert repo.get_by_roll_number("CS25001") is not None
    assert repo.get_by_roll_number("CS99999") is None


def test_department_exists(db_session):
    dept = _create_department(db_session)
    repo = StudentRepository(db_session)
    assert repo.department_exists(dept.id) is True
    assert repo.department_exists(__import__("uuid").uuid4()) is False


def test_list_pagination_and_filters(db_session):
    dept_a = _create_department(db_session, "CSE", "Computer Science")
    dept_b = _create_department(db_session, "ECE", "Electronics")
    for i in range(5):
        _create_student(db_session, dept_a, roll=f"CSE{i:04d}", name=f"Student {i}", email=f"s{i}@college.edu")
    _create_student(db_session, dept_b, roll="ECE0001", name="Other Student", email="other@college.edu")

    repo = StudentRepository(db_session)

    items, total = repo.list(limit=10, offset=0)
    assert total == 6
    assert len(items) == 6

    items, total = repo.list(limit=2, offset=0)
    assert total == 6
    assert len(items) == 2

    items, total = repo.list(limit=2, offset=4)
    assert total == 6
    assert len(items) == 2

    items, total = repo.list(limit=10, offset=0, department_id=dept_b.id)
    assert total == 1
    assert items[0].roll_number == "ECE0001"

    items, total = repo.list(limit=10, offset=0, semester=1)
    assert total == 6

    items, total = repo.list(limit=10, offset=0, search="student 3")
    assert total == 1
    assert items[0].roll_number == "CSE0003"

    items, total = repo.list(limit=10, offset=0, search="s2@college.edu")
    assert total == 1


def test_create_via_repository(db_session):
    dept = _create_department(db_session)
    repo = StudentRepository(db_session)
    student = repo.create(
        {
            "roll_number": "CS26001",
            "name": "New Student",
            "email": "new.student@college.edu",
            "department_id": dept.id,
            "semester": 2,
            "section": "B",
            "status": True,
        }
    )
    db_session.commit()
    assert student.id is not None
    assert repo.get(student.id) is not None


def test_unique_constraint_violation_raises(db_session):
    dept = _create_department(db_session)
    repo = StudentRepository(db_session)
    repo.create(
        {
            "roll_number": "CS27001",
            "name": "First",
            "email": "first@college.edu",
            "department_id": dept.id,
            "semester": 1,
            "section": "A",
            "status": True,
        }
    )
    db_session.flush()

    with pytest.raises(IntegrityError):
        repo.create(
            {
                "roll_number": "CS27001",
                "name": "Second",
                "email": "second@college.edu",
                "department_id": dept.id,
                "semester": 1,
                "section": "A",
                "status": True,
            }
        )
        db_session.flush()
    db_session.rollback()


def test_update_and_soft_delete(db_session):
    dept = _create_department(db_session)
    student = _create_student(db_session, dept)
    repo = StudentRepository(db_session)

    updated = repo.update(student, {"name": "Renamed Student", "semester": 3})
    db_session.commit()
    assert updated.name == "Renamed Student"
    assert updated.semester == 3

    repo.soft_delete(updated)
    db_session.commit()
    assert updated.status is False
    assert repo.get(student.id).status is False
