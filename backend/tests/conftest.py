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
