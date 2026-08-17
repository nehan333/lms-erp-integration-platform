# Prompts

Summaries of the sprint prompts (instructions) used to drive development. Each new sprint should append its own section.

---

## Sprint 1 — Backend Foundation

### Prompt Summary

- **Scope**: Build only the backend foundation for Sprint 1.
- **Stack**: Python 3.13+, uv, FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL, Alembic, Render.
- **Generated**:
  - `backend/app/{api,core,db,models,schemas,services,integrations/moodle,utils}` + `main.py`
  - `backend/alembic/`, `alembic.ini`, `pyproject.toml`, `.env.example`, `README.md`
- **Configured**: FastAPI, SQLAlchemy, environment variables, database session, logging, CORS, `GET /health`, Alembic.
- **Forbidden**: auth, CRUD, routers (except `/health`), tables, models, schemas, business logic, modules, Moodle integration, dependency installs, command execution, files outside `backend/`.
- **Clarifications**: psycopg v3 (recommended); pydantic-settings (recommended).

## Sprint 2 — Database Design & Foundation

### Prompt Summary

- **Scope**: Complete the ERP database foundation only.
- **Generated**:
  - `docs/DATABASE.md` (comprehensive design) and `docs/ERD.md` (Mermaid).
  - SQLAlchemy 2.0 models (8 tables) with UUID PKs, relationships, FKs, constraints, `created_at`/`updated_at`.
  - Initial Alembic migration `0001_create_core_tables`.
  - `backend/scripts/seed.py` (5 departments, 10 faculty, 50 students, 20 courses, 120 enrollments, 500 attendance, 120 grades).
  - `backend/README.md` migration/seed instructions.
- **Forbidden**: auth, JWT, routers, CRUD, repositories, services, business logic, Moodle integration, dashboard/reports, Docker, CI/CD, tests, package installs, command execution, schema/architecture changes.
- **Clarifications**: no `users` table in this sprint; uniform `created_at`/`updated_at` on all tables.
- **Outcome**: PostgreSQL configured, migrations executed, database seeded successfully.

---

## Sprint 3 — Student Management Module

### Prompt Summary

- **Scope**: Implement only the Student Management module (approved in a full handover prompt).
- **Generated**:
  - `backend/app/schemas/student.py` — `StudentCreate`, `StudentUpdate`, `StudentRead`, `StudentList`.
  - `backend/app/repositories/student.py` — `StudentRepository` (CRUD + filters + pagination).
  - `backend/app/services/student.py` — `StudentService` + domain exceptions (`StudentNotFoundError`, `DuplicateStudentError`, `DepartmentNotFoundError`).
  - `backend/app/api/students.py` — `GET/POST /students`, `GET/PUT/DELETE /students/{student_id}`; registered in `app/main.py`.
  - `backend/tests/` — `conftest.py`, `test_repositories.py`, `test_services.py`, `test_api.py` (45 passing).
- **Configured**: `[tool.pytest.ini_options]` in `backend/pyproject.toml`; dev deps `pytest` and `httpx` via `uv add --dev`.
- **Decisions**: soft delete (D19), limit/offset pagination + partial PUT (D20), dedicated PostgreSQL test DB + dependency override (D21), regex email validation (D22).
- **Forbidden**: Faculty, Courses, Enrollments, Attendance, Grades, Departments CRUD; users table; auth/JWT; Moodle; sync engine; dashboard; reports; frontend; deployment; Docker; CI/CD; background workers; no new migrations (schema unchanged); no git operations.
- **Outcome**: All 5 student endpoints verified live against the seeded DB; test suite 45/45; migration `0001` still at head; `GET /health` unchanged.

---

## Sprint 4 — Faculty & Department Modules

### Ready for Next Prompt

- **Status**: Not started. Waiting for the Sprint 4 prompt.
- **Expected scope**: Department CRUD, Faculty CRUD, relationships, repository/service/router layers, schemas, validation, Swagger, tests.
- **Expected restrictions**: no Courses, no Enrollments, no Attendance/Grades, no Moodle, no Frontend.
- **After completing**: append the Sprint 4 prompt summary below, update `CHANGELOG.md`, `SPRINTS.md`, `AI_CONTEXT.md`, `TASKS.md`, `API.md`, and `HANDOVER.md`.
