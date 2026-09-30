"""Shared fixtures for the Sprint 3 test suite.

Tests run against a dedicated PostgreSQL database (``lms_erp_test`` by
default, overridable via ``TEST_DATABASE_URL``). The schema is created
directly from the ORM models, which match migration ``0001``.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  (registers all ORM models on Base.metadata)
from app.db.base import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp_test",
)


def _ensure_test_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    if url.database is None:
        raise RuntimeError("TEST_DATABASE_URL must include a database name")
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def test_engine():
    _ensure_test_database()
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(test_engine):
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
    yield


@pytest.fixture
def db_session(test_engine):
    session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def student_data(**overrides) -> dict:
    data = {
        "roll_number": "CS25001",
        "name": "Test Student",
        "email": "test.student@student.college.edu",
        "phone": "+91 9000000000",
        "department_id": None,
        "semester": 1,
        "section": "A",
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_student_data():
    return student_data


def department_data(**overrides) -> dict:
    data = {
        "department_code": "CSE",
        "department_name": "Computer Science and Engineering",
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_department_data():
    return department_data


def faculty_data(**overrides) -> dict:
    data = {
        "employee_id": "FAC001",
        "name": "Test Faculty",
        "email": "test.faculty@college.edu",
        "phone": "+91 9000000001",
        "designation": "Assistant Professor",
        "department_id": None,
        "status": True,
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_faculty_data():
    return faculty_data


def course_data(**overrides) -> dict:
    data = {
        "course_code": "CS101",
        "course_name": "Data Structures",
        "credits": 4,
        "semester": 1,
        "department_id": None,
        "faculty_id": None,
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_course_data():
    return course_data


def enrollment_data(**overrides) -> dict:
    data = {
        "student_id": None,
        "course_id": None,
        "academic_year": "2025-2026",
        "semester": 1,
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_enrollment_data():
    return enrollment_data


def attendance_data(**overrides) -> dict:
    data = {
        "student_id": None,
        "course_id": None,
        "date": "2025-08-01",
        "status": "Present",
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_attendance_data():
    return attendance_data


def grade_data(**overrides) -> dict:
    data = {
        "student_id": None,
        "course_id": None,
        "internal_marks": "35.50",
        "external_marks": "45.00",
        "final_grade": "B+",
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_grade_data():
    return grade_data


def seed_student_and_course(db_session):
    """Create a department, faculty, student, and course; return their ids+pks."""
    from app.models.course import Course
    from app.models.department import Department
    from app.models.faculty import Faculty
    from app.models.student import Student

    dept = Department(department_code="CSE", department_name="Computer Science")
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)

    faculty = Faculty(
        employee_id="FAC001",
        name="Prof A",
        email="a@college.edu",
        designation="Professor",
        department_id=dept.id,
    )
    db_session.add(faculty)
    db_session.commit()
    db_session.refresh(faculty)

    student = Student(
        roll_number="CS25001",
        name="Test Student",
        email="test.student@student.college.edu",
        department_id=dept.id,
        semester=1,
        section="A",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    course = Course(
        course_code="CS101",
        course_name="Data Structures",
        credits=4,
        semester=1,
        department_id=dept.id,
        faculty_id=faculty.id,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    return {"dept": dept, "faculty": faculty, "student": student, "course": course}
