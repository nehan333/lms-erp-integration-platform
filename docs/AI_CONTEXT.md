# AI Context

This file gives any AI agent (or engineer) a complete snapshot of the project so it can continue development safely. **Read this file first.**

## Project Status

- **Project**: LMS–ERP Integration Platform — a College ERP integrated with Moodle LMS.
- **Status**: Sprint 3 completed. Sprint 4 (Faculty & Department Modules) is next.
- **Motto**: The ERP is the source of truth. Moodle is only the LMS.

## Completed Sprints

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 1 | Backend Foundation (FastAPI, SQLAlchemy, Alembic, config, logging, health) | Completed |
| Sprint 2 | Database Design & Foundation (models, migration, seed, docs) | Completed |
| Sprint 3 | Student Management Module (schemas, repository, service, router, API, tests) | Completed |

## Current Sprint

- **Sprint 4 — Faculty & Department Modules** (see `docs/SPRINT.md`).
- Not started. **Do not start it until instructed.**

## Current Module

- Sprint 4 target modules: **Faculty** and **Departments**.
- Reuse the Student-module patterns from Sprint 3 (`schemas/<entity>.py`, `repositories/<entity>.py`, `services/<entity>.py`, `api/<entity>.py`).

## Tech Stack

- **Language**: Python 3.13+ (runtime venv is 3.14)
- **Package manager**: uv
- **Web framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2 + pydantic-settings
- **Database**: PostgreSQL (psycopg v3)
- **Migrations**: Alembic
- **Testing**: pytest + httpx (dev dependencies, added in Sprint 3)
- **Deployment**: Render
- **Frontend**: Next.js (future, Sprint 8)

## Folder Structure

```
backend/
├── app/
│   ├── api/               # routers (health, students)
│   ├── core/              # settings + logging
│   ├── db/                # engine, session, declarative base
│   ├── integrations/moodle/  # future
│   ├── middlewares/       # future
│   ├── models/            # SQLAlchemy models (8 tables)
│   ├── repositories/      # student.py implemented; others future
│   ├── schemas/           # student.py implemented; others future
│   ├── services/          # student.py implemented; others future
│   ├── utils/             # future
│   └── main.py
├── alembic/               # migrations (0001_create_core_tables)
├── scripts/               # seed.py
├── tests/                 # Sprint 3 test suite (conftest, repository, service, API)
├── pyproject.toml
├── alembic.ini
├── .env.example
└── README.md
docs/
├── PROJECT.md             # master spec
├── SPRINTS.md             # roadmap (all sprints)
├── SPRINT.md              # active sprint only
├── DATABASE.md            # database design
├── ERD.md                 # mermaid ER diagram
├── ARCHITECTURE.md        # system architecture
├── AI_CONTEXT.md          # this file
├── CHANGELOG.md
├── DECISIONS.md
├── TASKS.md
├── PROMPTS.md
├── INFRASTRUCTURE.md
├── API.md
├── CONTRIBUTING.md
└── HANDOVER.md
```

## Important Architectural Decisions

- **ERP is the source of truth**; Moodle is downstream.
- **Layered backend**: API → Service → Repository → Database.
- **UUID primary keys** on all tables.
- **8-table schema** in Sprint 2 (no `users` table — deferred to auth sprint).
- **Uniform `created_at` / `updated_at`** on every table.
- **Check constraints over enum types** for status columns.
- **Named constraints/indexes** (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`).
- **Soft delete** for students (D19); **limit/offset pagination** (D20); **tests run against a dedicated PostgreSQL database** via dependency override (D21); **regex email validation without an extra dependency** (D22).
- Full list with reasons: see `docs/DECISIONS.md`.

## Implemented Student Module (Sprint 3)

- **Schemas** — `backend/app/schemas/student.py`: `StudentCreate`, `StudentUpdate`, `StudentRead`, `StudentList`.
- **Repository** — `backend/app/repositories/student.py`: `StudentRepository` (CRUD + filters + pagination).
- **Service** — `backend/app/services/student.py`: `StudentService` with domain exceptions (`StudentNotFoundError`, `DuplicateStudentError`, `DepartmentNotFoundError`).
- **Router** — `backend/app/api/students.py`, registered in `app/main.py`.
- **Endpoints**:
  - `GET /students` — list (filters: `limit`, `offset`, `department_id`, `semester`, `status`, `search`)
  - `POST /students` — create (`201`)
  - `GET /students/{student_id}` — read
  - `PUT /students/{student_id}` — partial update
  - `DELETE /students/{student_id}` — soft delete (`204`)
- **Tests** — `backend/tests/` (45 passing): repository, service, API layers.

## Current Database Status

- Schema: 8 tables (`departments, faculty, students, courses, enrollments, attendance, grades, sync_logs`).
- Migration `0001_create_core_tables` **has been executed** (still at head — Sprint 3 added no migration).
- Database **has been seeded**:
  - 5 departments, 10 faculty, 50 students, 20 courses, 120 enrollments, 500 attendance records, 120 grades.
- `sync_logs` is empty (used by the future Synchronization Engine).
- **Test database**: `lms_erp_test` is created automatically by the test suite (override with `TEST_DATABASE_URL`). The dev database is never touched by tests.

## Current Limitations

- No authentication or authorization (future sprint).
- Only `GET /health` and the Student module have endpoints. Faculty/Department/Course/Enrollment/Attendance/Grades have no CRUD yet.
- No Moodle integration.
- No frontend integration.
- `grades` allows one final grade per student–course; retake/reexam handling is future work.
- `DELETE /students` is a **soft delete** (`status=false`); records are never hard-deleted.
- `StudentRead` does not include department details (kept minimal in Sprint 3).

## Future Roadmap

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 3 | Student Management Module | ✅ Completed |
| Sprint 4 | Faculty & Department Modules | ⏳ Next |
| Sprint 5 | Course & Enrollment Modules (incl. attendance, grades) | Pending |
| Sprint 6 | Dashboard & Reports | Pending |
| Sprint 7 | Moodle Integration | Pending |
| Sprint 8 | Frontend Integration (Next.js) | Pending |
| Sprint 9 | Testing & Deployment (Render) | Pending |

## Rules for AI Agents

- Read `docs/PROJECT.md`, `docs/HANDOVER.md`, `docs/SPRINT.md` before any work.
- Implement **only the current sprint**.
- Never generate code for future sprints.
- Never introduce technologies outside the approved stack.
- Never modify files outside the scope of the current sprint.
- Run `uv run pytest` from `backend/` after changes to ensure the suite still passes.
- Use Alembic migrations for any schema change; confirm whether a schema change is actually needed before creating one.
