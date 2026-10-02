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

### Prompt Summary

- **Scope**: Implement the Faculty and Department management modules only.
- **Generated**:
  - `backend/app/schemas/department.py` — `DepartmentCreate`, `DepartmentUpdate`, `DepartmentRead`, `DepartmentList`.
  - `backend/app/schemas/faculty.py` — `FacultyCreate`, `FacultyUpdate`, `FacultyRead`, `FacultyList`.
  - `backend/app/repositories/department.py` — `DepartmentRepository` (CRUD + search + pagination + `has_children`).
  - `backend/app/repositories/faculty.py` — `FacultyRepository` (CRUD + filters + pagination; `department_exists` reuses `DepartmentRepository`).
  - `backend/app/services/department.py` — `DepartmentService` + domain exceptions (`DepartmentNotFoundError`, `DuplicateDepartmentError`, `DepartmentInUseError`).
  - `backend/app/services/faculty.py` — `FacultyService` + domain exceptions (`FacultyNotFoundError`, `DuplicateFacultyError`, `DepartmentNotFoundError`).
  - `backend/app/api/departments.py` and `backend/app/api/faculty.py`; registered in `app/main.py`.
  - `backend/tests/test_departments.py`, `backend/tests/test_faculty.py` + `department_data`/`faculty_data` helpers in `conftest.py` (59 new tests).
- **Forbidden**: Courses, Enrollments, Attendance, Grades; users table; auth/JWT; Moodle; sync engine; dashboard; reports; frontend; deployment; new migrations (schema unchanged).
- **Decisions**: D23 — department delete refused while the department has faculty/students/courses (`409`).
- **Outcome**: Full CRUD verified live against the seeded DB; test suite 104/104; migration `0001` still at head; `GET /health` unchanged.

---

## Sprint 5 — Course & Enrollment Modules

### Prompt Summary

- **Scope**: Implement the Course, Enrollment, Attendance, and Grades modules only.
- **Generated**:
  - `backend/app/schemas/{course,enrollment,attendance,grade}.py` — `*Create`, `*Update`, `*Read`, `*List`.
  - `backend/app/repositories/{course,enrollment,attendance,grade}.py` — CRUD + existence + unique lookups + filters.
  - `backend/app/services/{course,enrollment,attendance,grade}.py` — services + domain exceptions.
  - `backend/app/api/{courses,enrollments,attendance,grades}.py`; registered in `app/main.py`.
  - `backend/tests/test_{courses,enrollments,attendance,grades}.py` + `seed_student_and_course` helper in `conftest.py` (100 new tests).
- **Forbidden**: Dashboard/Reports/Statistics, Sync Logs API, Moodle, Frontend, Deployment, new migrations (schema unchanged), users table, auth/JWT.
- **Outcome**: All CRUD verified live against the seeded DB; test suite 204/204; migration `0001` still at head; no unrelated features added.

---

## Sprint 6 — Dashboard & Reports

### Ready for Next Prompt

- **Status**: Completed.
- **Scope**: Dashboard & statistic endpoints (counts + grade distribution + students per department), Reports endpoints (per-course enrollment, attendance summary, grade distribution, per-department course counts), Sync Logs read/list API, repository/service/router layers, schemas, Swagger, tests.
- **Forbidden**: Moodle integration (Sprint 7), Frontend, Deployment, new migrations (schema unchanged), writing to `sync_logs` from CRUD (only the Sprint 7 integration engine writes).
- **Outcome**: `GET /dashboard/overview`, four `/reports/*` endpoints, and `GET /sync-logs` + `GET /sync-logs/{id}` implemented and verified live against the seeded DB; test suite 230/230; migration `0001` still at head; `sync_logs` empty until Sprint 7 populates it.

---

## Sprint 7 — Moodle Integration

### Ready for Next Prompt

- **Status**: Completed.
- **Scope**: Clean Moodle integration layer (auth/config/API requests/response validation/timeouts/failures), create Moodle users/courses, enrollment, grade and attendance synchronization, sync results recorded to `sync_logs`; `GET /integrations/moodle/status` + `POST /integrations/moodle/sync`; tests with mocks/fixtures.
- **Forbidden**: Frontend, Deployment, new migrations (schema unchanged), new tables (no mapping table — identity derived from ERP keys).
- **Outcome**: Full sync verified against a simulated Moodle REST server (50 students / 20 courses / 120 enrollments / 20 graded courses / 500 attendance, all Success, idempotent second run); status returns `connected: false` and sync returns `503` when Moodle is not configured; test suite 267/267; migration `0001` still at head.

---

## Sprint 8 — Frontend Integration

### Ready for Next Prompt

- **Status**: Completed.
- **Scope**: Next.js app (JavaScript + CSS Modules, App Router) under `frontend/`; API client; dashboard + reports UI; CRUD pages/forms for students, departments, faculty, courses; Moodle sync page; frontend tests via Node's built-in runner.
- **Forbidden**: Backend feature creep, new backend migrations, Deployment.
- **Outcome**: `npm run build` and `npm test` pass; pages verified live against the running backend (data + CORS mutations); backend suite still 267/267; migration `0001` still at head.

---

## Sprint 9 — Testing & Final Preparation

### Ready for Next Prompt

- **Status**: Completed.
- **Scope**: Full backend + frontend + integration testing, bug fixes, API/database verification, final documentation, presentation preparation. No new features.
- **Forbidden**: Feature development, new dependencies, Deployment, schema changes.
- **Outcome**: New integration test suite (backend 272 passing incl. OpenAPI completeness, full-chain dashboard aggregates, Moodle boundary tests); frontend tests expanded to 6 (deterministic via stubFetch + sequential mode); `alembic check` clean, migration `0001` at head, seed intact; live E2E verified (create/edit/delete through UI origin); `docs/PRESENTATION.md` runbook added.

---

## Sprint 10 — Final Integration, Validation & Release Readiness

### Ready for Next Prompt

- **Status**: In progress — phases A–F delivered (2026-10-02). Remaining: sign-off / presentation readiness.
- **Expected scope**: Full end-to-end validation, fix discovered bugs, final documentation consistency, mark the project ready for manual deployment / presentation (deployment itself is out of scope). Extended at the user's request with phases A–F.
- **Delivered**: bulk course enrollment (`POST /enrollments/bulk/preview` + `/bulk`, auto Moodle sync, idempotent); attendance sync fixed for real (root cause `role_capabilities.contextid = 0` → `1`, decision D35) and grade sync working (letters → numeric points, D39); bulk student CSV import (`POST /students/bulk`, JSON-as-CSV, D36); student detail page with attendance-by-course (`GET /students/{id}/attendance-summary` + 4 new frontend pages, 17 build routes); docs updated (`AI_CONTEXT`, `CHANGELOG`, `HANDOVER`, `API`, `TASKS`, `SPRINT`, `DECISIONS`, `PRESENTATION`).
- **Outcome**: backend **311 passing** (was 272; no tests removed), frontend 6 passing + `npm run build` green, live Moodle probe green end-to-end, live API E2E green (bulk enroll → sync `Success` → idempotent re-run), OpenAPI 28 paths / 49 operations.
