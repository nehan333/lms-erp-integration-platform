# AI Context

This file gives any AI agent (or engineer) a complete snapshot of the project so it can continue development safely. **Read this file first.**

## Project Status

- **Project**: LMS–ERP Integration Platform — a College ERP integrated with Moodle LMS.
- **Status**: Sprint 9 completed. Sprint 10 (Final Integration, Validation & Release Readiness) in progress — phases A–F delivered (bulk enrollment, working attendance + grade sync, bulk student import, student detail page with attendance, docs updated).
- **Motto**: The ERP is the source of truth. Moodle is only the LMS.

## Completed Sprints

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 1 | Backend Foundation (FastAPI, SQLAlchemy, Alembic, config, logging, health) | Completed |
| Sprint 2 | Database Design & Foundation (models, migration, seed, docs) | Completed |
| Sprint 3 | Student Management Module (schemas, repository, service, router, API, tests) | Completed |
| Sprint 4 | Faculty & Department Modules (CRUD, schemas, repository, service, router, API, tests) | Completed |
| Sprint 5 | Course & Enrollment Modules (incl. Attendance, Grades) | Completed |
| Sprint 6 | Dashboard & Reports (incl. Sync Logs read API) | Completed |
| Sprint 7 | Moodle Integration (sync engine + sync-logs recording) | Completed |
| Sprint 8 | Frontend Integration (Next.js + API client + CRUD + dashboard) | Completed |
| Sprint 9 | Testing & Final Preparation (integration tests, docs, runbook) | Completed |

## Current Sprint

- **Sprint 10 — Final Integration, Validation & Release Readiness** (see `docs/SPRINT.md`).
- Phases A–F delivered: bulk course enrollment, working Moodle attendance sync, working grade sync, bulk student CSV import, student detail page with attendance-by-course, and full docs updates. Remaining: final sign-off / presentation readiness.

## Current Module

- Sprint 10 target: **final end-to-end validation, consistency, and readiness** — production deployment is out of scope (manual, by the project owner).
- Reuse the existing layered patterns (service → repository → API).

## Tech Stack

- **Language**: Python 3.13+ (runtime venv is 3.14)
- **Package manager**: uv
- **Web framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic v2 + pydantic-settings
- **Database**: PostgreSQL (psycopg v3)
- **Migrations**: Alembic
- **Testing**: backend pytest + httpx; frontend Node built-in `node:test`
- **Deployment**: Render
- **Frontend**: Next.js (JavaScript, CSS Modules, App Router)

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
- **Soft delete** for students and faculty (D19); **limit/offset pagination** (D20); **tests run against a dedicated PostgreSQL database** via dependency override (D21); **regex email validation without an extra dependency** (D22); **department delete is guarded while in use** (D23).
- **Sprint 10 additions**: `mod_attendance` capabilities must be granted at the **system context** (`contextid = 1`) or Moodle treats the activity as hidden (D35); bulk CSV travels as a JSON string field, not multipart (D36); bulk operations are preview-then-execute and idempotent (D37); Moodle bool params are always `"0"`/`"1"` (D38); final-grade letters map to numeric `rawgrade` with the letter in `str_feedback` (D39); bulk writes auto-sync to Moodle and log "pending sync" as `Failed` when unconfigured (D40); percentages are `null` when the denominator is 0 (D41).
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

## Implemented Faculty & Department Modules (Sprint 4)

- **Schemas** — `backend/app/schemas/department.py` and `backend/app/schemas/faculty.py`: `*Create`, `*Update`, `*Read`, `*List` per module.
- **Repositories** — `backend/app/repositories/department.py` (`DepartmentRepository`) and `backend/app/repositories/faculty.py` (`FacultyRepository`). `FacultyRepository.department_exists` reuses `DepartmentRepository`.
- **Services** — `backend/app/services/department.py` (`DepartmentService` + `DepartmentNotFoundError`, `DuplicateDepartmentError`, `DepartmentInUseError`) and `backend/app/services/faculty.py` (`FacultyService` + `FacultyNotFoundError`, `DuplicateFacultyError`, `DepartmentNotFoundError`).
- **Routers** — `backend/app/api/departments.py` and `backend/app/api/faculty.py`, registered in `app/main.py`.
- **Endpoints**:
  - `GET/POST /departments`, `GET/PUT/DELETE /departments/{department_id}` (delete refused with `409` while the department has faculty/students/courses).
  - `GET/POST /faculty`, `GET/PUT/DELETE /faculty/{faculty_id}` (filters: `department_id`, `status`, `search`; delete is a soft delete).
- **Tests** — `backend/tests/test_departments.py`, `backend/tests/test_faculty.py` (repository, service, API layers). Helpers `department_data` / `faculty_data` in `conftest.py`.

## Implemented Course, Enrollment, Attendance & Grades Modules (Sprint 5)

- **Schemas** — `backend/app/schemas/{course,enrollment,attendance,grade}.py`: `*Create`, `*Update`, `*Read`, `*List` per module. Attendance `status` uses `Literal["Present","Absent"]`; grade marks are `Decimal` bounded 0–100 (2 dp).
- **Repositories** — `backend/app/repositories/{course,enrollment,attendance,grade}.py`: CRUD + existence helpers + unique lookups + list filters.
- **Services** — `backend/app/services/{course,enrollment,attendance,grade}.py` with domain exceptions per module.
- **Routers** — `backend/app/api/{courses,enrollments,attendance,grades}.py`, registered in `app/main.py`.
- **Endpoints**:
  - `GET/POST /courses`, `GET/PUT/DELETE /courses/{course_id}` (filters `department_id`/`faculty_id`/`semester`/`search`; delete guarded while in use).
  - `GET/POST /enrollments`, `GET/PUT/DELETE /enrollments/{enrollment_id}` (filters `student_id`/`course_id`/`academic_year`/`semester`).
  - `GET/POST /attendance`, `GET/PUT/DELETE /attendance/{attendance_id}` (filters `student_id`/`course_id`/`date`/`status`).
  - `GET/POST /grades`, `GET/PUT/DELETE /grades/{grade_id}` (filters `student_id`/`course_id`).
- **Tests** — `backend/tests/test_{courses,enrollments,attendance,grades}.py` (repository, service, API layers). `seed_student_and_course` helper added to `conftest.py`.
- **Sprint 6** — `GET /dashboard/overview` (counts, grade distribution, students per department); `/reports/enrollments-by-course`, `/reports/attendance-summary`, `/reports/grade-distribution`, `/reports/courses-by-department`; `GET /sync-logs` + `GET /sync-logs/{id}`.
- **Sprint 7** — Moodle integration (`app/integrations/moodle/`), `MoodleSyncService` (users/courses/enrollments/grades/attendance), `GET /integrations/moodle/status` + `POST /integrations/moodle/sync`; `sync_logs` now populated by the sync engine.

## Implemented Sprint 10 — Bulk Operations, Moodle Sync Fixes & Student Detail

- **Bulk enrollment** (`backend/app/services/enrollment.py` → `bulk_preview` / `bulk_create`, `backend/app/api/enrollments.py`):
  - `POST /enrollments/bulk/preview` (200) — dry run; validates courses exist **and** belong to the department (`CourseNotInDepartmentError`), reports per-course `to_create` / `already_enrolled`.
  - `POST /enrollments/bulk` (201) — idempotent (skips existing pairs), then auto-syncs created ids to Moodle and attaches the `sync_log`.
  - Errors: `DepartmentNotFoundError` → 404, `CourseNotFoundError` / `CourseNotInDepartmentError` → 400.
- **Bulk student import** (`backend/app/services/student.py` → `_parse_rows` / `bulk_import`, `backend/app/api/students.py`):
  - `POST /students/bulk` (201) — CSV inside JSON (`csv`), `dry_run`, `sync_moodle`; required header `roll_number,name,email,semester,section` (+ optional `phone`); BOM tolerated; row numbers 1-based incl. header; savepoint per row; `MAX_BULK_ROWS = 5000`.
  - `skipped` = duplicates already in the DB; `failed` = malformed rows; both appear in `errors[]`.
- **Attendance summary** (`backend/app/services/attendance.py` → `student_summary`, `backend/app/repositories/attendance.py` → `summary_by_course_for_student`):
  - `GET /students/{student_id}/attendance-summary` (200 / 404) — per-course breakdown + overall `present`/`total`/`percentage`; `percentage` is `null` when `total == 0`.
- **Moodle sync fixes** (`backend/app/services/moodle.py`, `backend/app/integrations/moodle/payloads.py`, `backend/app/core/config.py`):
  - Attendance status cache field renamed `_attendance_status_cache` (it shadowed the method).
  - Bool params encoded as `"0"`/`"1"`; `MOODLE_ATTENDANCE_WSFUNCTION` setting removed; grades map letters → numeric points with the letter in `str_feedback`.
- **Frontend pages**: `/students/[id]` (detail + attendance table), `/students/bulk` (`components/BulkStudentImport.js`), `/enrollments` (joined names), `/enrollments/bulk` (`components/BulkEnrollForm.js`, preview → confirm); Nav gained **Enrollments**; student names link to detail.
- **Tests**: `backend/tests/test_students_bulk.py` (15), extended `test_enrollments.py` (+9), `test_moodle_service.py` / `test_moodle_payloads.py` (grade + attendance payloads), `test_attendance.py` (+6 for the summary). Full suite **311 passing**.
- **Moodle environment** (`moodle-test/`): service `LMS-ERP Integration` (id 2) with 13 functions enabled; token user `lms_erp_sync` (userid 3); custom role id 9 `lms-erpintegration` with 4 `mod_attendance` capabilities at `contextid = 1`.

## Current Database Status

- Schema: 8 tables (`departments, faculty, students, courses, enrollments, attendance, grades, sync_logs`).
- Migration `0001_create_core_tables` **has been executed** (still at head — Sprints 3–7 added no migration).
- Database **has been seeded**:
  - 5 departments, 10 faculty, 50 students, 20 courses, 120 enrollments, 500 attendance records, 120 grades.
- `sync_logs` populated only by the Sprint 7 Moodle integration engine (left empty in the dev database).
- **Test database**: `lms_erp_test` is created automatically by the test suite (override with `TEST_DATABASE_URL`). The dev database is never touched by tests.

## Current Limitations

- No authentication or authorization (future sprint).
- A live Moodle **is** available in this environment (`moodle-test/` via Docker, base URL `http://localhost:8080`) and the sync engine is verified against it; when `MOODLE_BASE_URL`/`MOODLE_WSTOKEN` are absent the status/sync endpoints fall back to reporting "not configured".
- CRUD pages cover students (list, detail, edit, bulk import), departments, faculty, courses, and enrollments (list + bulk) on the frontend; attendance/grades UIs are not built (reports + the student detail attendance table cover the read side).
- Moodle identity is keyed to ERP roll number / course code (no ID mapping table; see decision D29).
- Attendance sync requires the `mod_attendance` plugin and its capabilities granted to the integration role **at the system context** (decision D35); statuses are matched by name case-insensitively (`Present`/`Absent`/`Late`/`Excused`).
- `core_grades_update_grades` accepts `str_feedback` but Moodle's implementation discards it — the original letter grade is **not** persisted on the Moodle side (decision D39).
- `grades` allows one final grade per student–course; retake/reexam handling is future work.
- `DELETE /students` and `DELETE /faculty` are **soft deletes** (`status=false`); records are never hard-deleted.
- `DELETE /departments` and `DELETE /courses` are **hard deletes** but refused (`409`) while they have children.
- `StudentRead` / `FacultyRead` do not include department details (kept minimal).
- `GET /enrollments` returns only ids; the frontend list page joins student/course names by fetching `/students` and `/courses` (limit 100 each).

## Future Roadmap

| Sprint | Scope | Status |
|--------|-------|--------|
| Sprint 5 | Course & Enrollment Modules (incl. attendance, grades) | ✅ Completed |
| Sprint 6 | Dashboard & Reports | ✅ Completed |
| Sprint 7 | Moodle Integration | ✅ Completed |
| Sprint 8 | Frontend Integration (Next.js) | ✅ Completed |
| Sprint 9 | Testing & Final Preparation | ✅ Completed |
| Sprint 10 | Final Integration, Validation & Release Readiness | ⏳ Next |

## Rules for AI Agents

- Read `docs/PROJECT.md`, `docs/HANDOVER.md`, `docs/SPRINT.md` before any work.
- Implement **only the current sprint**.
- Never generate code for future sprints.
- Never introduce technologies outside the approved stack.
- Never modify files outside the scope of the current sprint.
- Run `uv run pytest` from `backend/` after changes to ensure the suite still passes.
- Use Alembic migrations for any schema change; confirm whether a schema change is actually needed before creating one.
- Deployment is handled manually by the project owner and is out of scope for every sprint.
