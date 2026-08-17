# Changelog

All notable changes are documented here. Format follows the current sprint lifecycle.

---

## Sprint 3 - Student Management Module — 2026-08-10

### Added

- **Pydantic v2 schemas** (`app/schemas/student.py`):
  - `StudentCreate`, `StudentUpdate` (partial), `StudentRead` (from ORM), `StudentList` (paginated).
  - Email format validation via regex (no extra dependency) and normalization to lowercase.
- **Student repository** (`app/repositories/student.py`):
  - `StudentRepository` with `get`, `get_by_roll_number`, `get_by_email` (case-insensitive), `department_exists`, `list` (filtering + limit/offset pagination), `create`, `update`, `soft_delete`.
- **Student service** (`app/services/student.py`):
  - `StudentService` coordinating repository operations and validation.
  - Domain exceptions: `StudentNotFoundError`, `DuplicateStudentError`, `DepartmentNotFoundError`.
  - Duplicate email/roll_number and department existence are validated before writes; `IntegrityError` is translated to a domain error and rolled back (raw DB errors never reach clients).
- **Student API router** (`app/api/students.py`):
  - `GET /students` — paginated list with `limit`, `offset`, `department_id`, `semester`, `status`, `search` filters.
  - `POST /students` — create (`201`).
  - `GET /students/{student_id}` — read.
  - `PUT /students/{student_id}` — partial update.
  - `DELETE /students/{student_id}` — **soft delete** (sets `status=false`, `204`).
  - Registered in `app/main.py`.
- **Test suite** (`backend/tests/`):
  - `conftest.py` — dedicated PostgreSQL test database (`lms_erp_test`, overridable via `TEST_DATABASE_URL`), schema created from ORM models, `get_db` dependency override, shared data helpers.
  - `test_repositories.py` — repository CRUD, filters, pagination, unique-constraint violation.
  - `test_services.py` — service validation, duplicate handling, invalid department, soft delete.
  - `test_api.py` — API endpoints, HTTP status codes, duplicate conflicts, pagination, filters, OpenAPI registration.
  - **45 tests, all passing.**
- **Dependencies (dev)**: `pytest` and `httpx` added via `uv add --dev`.
- **pytest configuration**: `[tool.pytest.ini_options]` with `testpaths` and `pythonpath` in `backend/pyproject.toml`.

### Notes

- No database schema change was required; migration `0001` remains at head and no new migration was created.
- `DELETE` is a soft delete by design (decision D19) to preserve academic history and avoid FK violations with enrollments/attendance/grades.
- `PUT /students/{id}` applies only the fields provided (partial-update semantics, decision D20).
- `StudentRead` includes all model fields plus `id` and audit timestamps; department name resolution is intentionally not included (kept minimal for this sprint).

---

## Sprint 2 - Database Design & Foundation — 2026-08-05

### Added

- **SQLAlchemy 2.0 ORM models** for all 8 core tables:
  - `departments`, `faculty`, `students`, `courses`, `enrollments`, `attendance`, `grades`, `sync_logs`
  - UUID primary keys, `created_at` / `updated_at` audit timestamps, named constraints and indexes.
- **Initial Alembic migration** `0001_create_core_tables` (executed).
- **Seed script** `backend/scripts/seed.py`:
  - 5 departments, 10 faculty, 50 students, 20 courses, 120 enrollments, 500 attendance records, 120 grades.
- **Documentation**:
  - `docs/DATABASE.md` — full database design.
  - `docs/ERD.md` — Mermaid entity relationship diagram.
- **Backend updates**:
  - `alembic/env.py` — registers ORM models for autogenerate.
  - `backend/README.md` — database migration and seed instructions.

### Notes

- Schema intentionally excludes a `users` table (deferred to the Authentication sprint).

---

## Sprint 1 - Backend Foundation — 2026-08-05

### Added

- **Project structure** under `backend/`:
  - `app/api`, `app/core`, `app/db`, `app/integrations/moodle`, `app/middlewares`, `app/models`, `app/repositories`, `app/schemas`, `app/services`, `app/utils`.
- **FastAPI application** (`app/main.py`) with:
  - CORS middleware.
  - Lifespan management (engine disposal).
  - `GET /health` endpoint.
- **Configuration** (`app/core/config.py`) via pydantic-settings:
  - `PROJECT_NAME`, `ENVIRONMENT`, `DEBUG`, `LOG_LEVEL`, `DATABASE_URL`, `CORS_ORIGINS`.
- **Logging** (`app/core/logging.py`) — stdout, level from settings.
- **Database layer** (`app/db/`):
  - Engine (`pool_pre_ping`, echo from `DEBUG`).
  - Session factory and `get_db` dependency.
  - Declarative `Base`.
- **Alembic configuration** (`alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`).
- **uv project** (`pyproject.toml`) — Python 3.13+, psycopg v3, SQLAlchemy 2.0, FastAPI, Pydantic v2, pydantic-settings, uvicorn.
- **`.env.example`** — documented environment variables.
- **Documentation** — `backend/README.md`.

---

## Unreleased

- Sprint 4 — Faculty & Department Modules (see `docs/SPRINT.md`).
