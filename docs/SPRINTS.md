# Sprint Roadmap

This document is the roadmap from **Sprint 1 until project completion**.

- The **active sprint** is tracked in `docs/SPRINT.md`.
- Do not implement any sprint until it is explicitly assigned.

---

## Sprint 1 - Backend Foundation ✅

### Goal

Establish a production-ready backend foundation.

### Completed

- Project structure
- FastAPI
- SQLAlchemy
- Alembic
- Configuration
- Logging
- Environment Variables
- Health Endpoint
- Project Documentation

Status: Completed

---

## Sprint 2 - Database Design & Foundation ✅

### Goal

Design and implement the ERP database.

### Tasks

- Finalize DATABASE.md
- Design ER Diagram
- Configure PostgreSQL
- Generate SQLAlchemy Models
- Generate Alembic Migration
- Run Migration
- Create Seed Script
- Insert Sample Data
- Verify Relationships
- Commit Changes

Deliverable:

Working PostgreSQL database containing sample academic data.

Status: Completed

---

## Sprint 3 - Student Management Module ✅

### Goal

Implement complete Student Management.

### Completed

- Pydantic v2 schemas (`StudentCreate`, `StudentUpdate`, `StudentRead`, `StudentList`)
- `StudentRepository` (data access, filtering, pagination)
- `StudentService` (business logic, validation, error handling)
- Student API router (`GET /students`, `POST /students`, `GET /students/{id}`, `PUT /students/{id}`, `DELETE /students/{id}`)
- Swagger/OpenAPI documentation for student endpoints
- pytest-based test suite (repository, service, API layers)

Deliverable:

Complete Student Module.

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 4 - Faculty & Department Modules ✅

### Goal

Faculty and Department Management.

### Completed

- Department CRUD (`GET/POST /departments`, `GET/PUT/DELETE /departments/{department_id}`)
- Faculty CRUD (`GET/POST /faculty`, `GET/PUT/DELETE /faculty/{faculty_id}`)
- Pydantic schemas, repository, service, and router layers for both modules
- Validation (unique codes/names, faculty email/employee_id, department existence)
- Error handling (404/400/409, soft delete for faculty, guarded department delete)
- Swagger/OpenAPI documentation
- Tests (repository, service, API layers) — 59 new tests

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 5 - Course & Enrollment Modules ✅

### Goal

Academic Structure.

### Completed

- Course CRUD (`GET/POST /courses`, `GET/PUT/DELETE /courses/{course_id}`)
- Enrollment CRUD (`GET/POST /enrollments`, `GET/PUT/DELETE /enrollments/{enrollment_id}`)
- Attendance CRUD (`GET/POST /attendance`, `GET/PUT/DELETE /attendance/{attendance_id}`)
- Grades CRUD (`GET/POST /grades`, `GET/PUT/DELETE /grades/{grade_id}`)
- Pydantic schemas, repository, service, and router layers for each module
- Validation (course code uniqueness, attendance status, marks ranges, student/course/department/faculty existence)
- Error handling (404/400/409, guarded course delete)
- Swagger/OpenAPI documentation
- Tests (repository, service, API layers) — 100 new tests

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 6 - Dashboard & Reports ✅

### Goal

ERP Dashboard and Reporting.

### Completed

- `GET /dashboard/overview` — aggregate counts and grade/student-by-department breakdowns
- Reports: `GET /reports/enrollments-by-course`, `/reports/attendance-summary`, `/reports/grade-distribution`, `/reports/courses-by-department`
- Sync Logs: `GET /sync-logs`, `GET /sync-logs/{id}` (read API; populated by Sprint 7's Moodle integration)
- Pydantic schemas, repository, service, and router layers for each module
- Routers registered in `app/main.py`
- Swagger/OpenAPI documentation
- Tests (repository, service, API layers) — 26 new tests
- Full regression suite passing (230 total)

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 7 - Moodle Integration ✅

### Goal

Integrate the ERP with Moodle LMS.

### Completed

- Clean Moodle integration layer (`app/integrations/moodle/`): authenticated REST client, typed errors, payload builders, timeouts, response validation
- Moodle auth/connection check via `core_webservice_get_site_info` (`GET /integrations/moodle/status`)
- Create Moodle users (`core_user_create_users`), courses (`core_course_create_courses`) — find-or-create, idempotent
- Student enrollment (`enrol_manual_enrol_users`)
- Grade synchronization (`core_grades_update_grades`) and attendance synchronization (configurable wsfunction)
- Every outcome recorded in `sync_logs` (module `moodle`, action per operation, `Success`/`Failed`)
- `POST /integrations/moodle/sync` full-run endpoint (503 when not configured)
- Tests (payloads, client with mock transport, service with fake client, API) — 37 new tests
- Full regression suite passing (267 total)

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 8 - Frontend Integration ✅

### Goal

Connect Next.js with FastAPI.

### Completed

- Next.js app (JavaScript + CSS Modules, App Router) under `frontend/`
- API client layer (`lib/api.js`) — GET/POST/PUT/DELETE with error surfacing
- Dashboard UI (`/`) consuming `GET /dashboard/overview`
- Reports UI (`/reports`) consuming `GET /reports/*`
- CRUD pages for Departments, Faculty, Courses, Students (list + `/new` + `/[id]/edit` forms) built on a reusable `EntityForm`
- Moodle Sync page (`/sync`) — status check + full sync trigger
- Tests — `frontend/tests/api.test.mjs` via Node's built-in test runner (4 tests)
- Verified live against the running backend (data rendered, CORS mutations OK)
- Backend regression suite still passing (267)

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 9 - Testing & Final Preparation ✅

### Goal

Prepare the project for release and presentation.

### Completed

- Full backend testing (272 passing) incl. a new integration suite (OpenAPI completeness, full data-chain dashboard aggregates, Moodle partial-failure boundaries)
- Frontend build + tests passing (6 frontend tests)
- Integration verification (live UI-origin create/edit/delete flow, all GET endpoints 200, CORS)
- Bug fixes / hardening (frontend tests made deterministic)
- API / database verification (`alembic check` clean, migration at head `0001`, seed intact, OpenAPI complete)
- Final documentation + presentation runbook (`docs/PRESENTATION.md`)

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 10 - Final Integration, Validation & Release Readiness ⏳

### Goal

End-to-end review and release readiness.

### Tasks

- Full end-to-end validation
- Fix discovered bugs
- Final documentation consistency
- Mark the project ready for manual deployment / presentation

### Delivered (2026-10-02, scope extended at the user's request)

- **A** Bulk course enrollment with automatic Moodle sync (`POST /enrollments/bulk/preview`, `POST /enrollments/bulk`)
- **B** Working attendance sync (root cause: `role_capabilities.contextid = 0` → `1`; see decision D35)
- **C** Working grade sync (letters → numeric `rawgrade`, D39)
- **D** Bulk student CSV import (`POST /students/bulk`)
- **E** Student detail page with attendance-by-course (`GET /students/{id}/attendance-summary` + `/students/[id]`, `/students/bulk`, `/enrollments`, `/enrollments/bulk`)
- **F** Documentation updates across `docs/*.md`
- Verification: backend **311 passing** (was 272), frontend 6 passing + `npm run build` (17 routes), live Moodle probe green, live API E2E green.

### Out of scope

- Production deployment (handled manually by the project owner).
