# Changelog

All notable changes are documented here. Format follows the current sprint lifecycle.

---

## Sprint 10 - Final Integration, Validation & Release Readiness — 2026-10-02

Scope was extended at the user's request beyond "validation only" to close the bulk-operation and Moodle-sync gaps (phases A–F below). No schema change: migration still at head `0001`.

### Fixed (Moodle integration)

- **Attendance sync now works end-to-end against a live Moodle 5.0.10.** Root cause: the integration role's `mod_attendance` capabilities had been inserted with `contextid = 0`; Moodle's `accesslib` only resolves capabilities joined to the `{context}` table, so `has_capability('mod/attendance:view')` stayed false, the activity was treated as hidden, and `require_login` rejected every call (`Activity is hidden`). Fixed by granting the four capabilities at the system context (`contextid = 1`) and purging caches (decision **D35**).
- **Bool parameters are form-encoded as `"0"` / `"1"`** instead of Python `False` (Moodle's `PARAM_BOOL` rejects `"False"` with `invalidparameter`) — decision **D38**.
- **`MOODLE_ATTENDANCE_WSFUNCTION` removed from `app/core/config.py` / `.env.example`** — dead setting (decision D31 superseded by D35).
- **Bug fix in `app/services/moodle.py`**: the instance dict field `_attendance_statuses` shadowed the method of the same name; renamed to `_attendance_status_cache`.
- **Grade sync**: `core_grades_update_grades` now sends `rawgrade` derived from a lower-bound letter table (`A+` ≥ 90 … `F` = 0), numeric grades pass through, and the original letter is placed in `str_feedback` (Moodle currently discards `str_feedback` — documented limitation, decision **D39**).
- **Attendance session strategy**: one attendance instance per course, one session per ERP attendance date at local midnight (`duration = 0`, `groupid = 0`, `addcalendarevent = "0"`), statuses resolved via `mod_attendance_get_session` and matched case-insensitively; `takenbyid` comes from `core_webservice_get_site_info`.

### Added

- **Bulk course enrollment (phase A)**
  - `POST /enrollments/bulk/preview` — dry run: resolves the department cohort (active students at a semester), validates every course exists *and* belongs to that department, reports per-course `to_create` / `already_enrolled` (`BulkEnrollmentPreview`).
  - `POST /enrollments/bulk` — creates every missing pair, skips duplicates, and **auto-syncs the created ids to Moodle** (`MoodleSyncService.sync_enrollments`); returns `BulkEnrollmentResult` with the `sync_log`. Idempotent — a repeat run reports `created: 0, skipped: N`.
  - `BulkEnrollmentRequest` / `BulkEnrollmentPreview` / `BulkEnrollmentResult` schemas; `list_students_for_cohort`, `list_courses_by_ids`, `existing_pairs` repository helpers; `DepartmentNotFoundError`, `CourseNotInDepartmentError` domain errors.
- **Bulk student CSV import (phase D)**
  - `POST /students/bulk` — CSV-as-JSON (`csv` field, no multipart dependency), `dry_run`, `sync_moodle`; header required (`roll_number,name,email,semester,section`[,`phone`]), UTF-8 BOM tolerated, 1-based row numbers including the header, savepoint-per-row, `MAX_BULK_ROWS = 5000`.
  - `BulkStudentImportRequest` / `BulkStudentImportResult` / `BulkStudentRowError`, `BulkImportFormatError`, and `MoodleSyncService.sync_students(student_ids=…)` for targeted sync.
- **Attendance summary (phase E)**
  - `GET /students/{student_id}/attendance-summary` — per-course `present` / `total` / `percentage` plus an overall roll-up (`StudentAttendanceSummary`); `percentage` is `null` when `total == 0` (decision **D41**), unknown student → `404`.
  - `AttendanceRepository.summary_by_course_for_student` + `AttendanceService.student_summary`.
- **Frontend (phase E)** — four new pages, build up from 14 → 17 routes:
  - `/students/[id]` — student detail with contact card, status/attendance stat cards, and the attendance-by-course table.
  - `/students/bulk` — CSV paste + department + dry-run + Moodle-sync checkboxes with per-row error reporting (`components/BulkStudentImport.js`).
  - `/enrollments` — enrollment list joined against students/courses for readable names, with delete and a link into bulk enroll.
  - `/enrollments/bulk` — two-step preview → confirm workflow (`components/BulkEnrollForm.js`).
  - Nav gained an **Enrollments** link; student names in the list now link to their detail page; the students list gained a **Bulk Import** button.

### Verified

- **Backend**: `uv run pytest` → **311 passing** (272 baseline + 39 new; no tests removed or weakened).
- **Frontend**: `npm test` → 6 passing; `npm run build` succeeds (17 pages).
- **Live Moodle probe** (all green): `core_user_get_users_by_field`, `core_course_get_courses_by_field`, `mod_attendance_add_attendance`, `mod_attendance_add_session`, `mod_attendance_get_session`, `mod_attendance_update_user_status` (twice), `core_grades_update_grades` (twice). Rows verified in `mdl_attendance_log`, `mdl_grade_grades`, `mdl_grade_items`, `mdl_attendance_sessions`.
- **Live API E2E**: bulk preview → bulk enroll (created 1, `sync_log: Success — 1 enrollments synced`) → repeat run (`created 0, skipped 1`); bulk import dry run; attendance summary returns real per-course data; all four new pages render 200 with live data.
- **OpenAPI**: 28 paths / 49 operations (was 24 paths); the route-completeness guard now also asserts the four new paths.

### Notes

- No new dependencies on either side; no schema change and no migration (still at head `0001`).
- The Moodle Docker stack (`moodle-test/`) is the verification environment; never delete `moodle-postgres-data` or run `docker volume prune`.

---

## Sprint 9 - Testing & Final Preparation — 2026-08-17

### Added

- **Integration test suite** (`backend/tests/test_integration.py`, 5 tests):
  - OpenAPI route completeness guard (all 24 expected paths present).
  - Full-chain test: department → faculty → student → course → enrollment → grade → attendance reflected correctly in `GET /dashboard/overview` aggregates.
  - Moodle orchestration boundaries: partial failure in `sync_all` records exactly the failing operation as `Failed`; a grade response without `result: true` is honestly treated as `Failed`; sync logs are persisted and listable.
- **Frontend API-client tests** (`frontend/tests/api.test.mjs`, now 6 tests): added PUT and GET-without-body coverage; tests made deterministic via a `stubFetch` helper and `{ concurrency: false }` (shared `global.fetch` state).
- **Presentation runbook** (`docs/PRESENTATION.md`): feature list for a demo, local runbook, test summary, architecture slide, and notable decisions for Q&A.

### Verified

- **Schema/database**: `uv run alembic check` reports no drift between models and DB; migration still at head `0001`; seed data intact (5/10/50/20/120/500/120/0).
- **OpenAPI**: 24 documented routes across health, 8 CRUD modules, dashboard, reports, sync-logs, and Moodle.
- **Integration (live servers)**: full UI-origin E2E — create department → appears on `/departments` → edit → reflects rename → delete → removed; all 13 GET endpoints return 200; Moodle status reports `connected: false` when unconfigured.
- **Suites**: backend 272 passing (5 added), frontend build succeeds and 6 tests passing. No tests removed or weakened.

### Notes

- This sprint added no production code, no schema change, and no new dependencies (frontend tests use Node's built-in `node:test`).
- Existing docs kept consistent: sprint roadmap now points to Sprint 10.

---

## Sprint 8 - Frontend Integration — 2026-08-17

## Sprint 8 - Frontend Integration — 2026-08-17

### Added

- **Next.js app** under `frontend/` (JavaScript + CSS Modules, App Router):
  - `package.json`, `next.config.mjs`, `jsconfig.json` (`@/*` alias), `.env.local.example` (`NEXT_PUBLIC_API_URL=https://localhost:8000`).
  - Root layout + `app/globals.css` (design system) + `<Nav>` component (`components/Nav.js`).
  - API client (`lib/api.js`): `api.get/create/update/remove`, JSON body handling, error `detail` surfacing, 204 handling.
- **Dashboard** (`/`): stat cards + grade distribution + students-by-department from `GET /dashboard/overview`.
- **Reports** (`/reports`): attendance summary, enrollments-by-course, grade distribution, courses-by-department from `GET /reports/*`.
- **CRUD pages** for Departments, Faculty, Courses, Students: list tables (with badges / edit / delete) plus `/new` and `/[id]/edit` form pages. Built on a reusable `EntityForm` (client component) and `DeleteButton` (client component).
- **Moodle sync page** (`/sync`): check status and trigger a full sync via `components/SyncPanel.js`.
- **Tests** (`frontend/tests/api.test.mjs`) using Node's built-in `node:test` (no new dependencies) — verified GET/POST/error/204 behavior of the API client.

### Verified

- `npm run build` succeeds (all data-fetching routes server-rendered as dynamic).
- `npm test` passes (4 frontend tests).
- Live integration: served the built frontend against the running backend; `/`, `/reports`, `/students`, `/departments`, `/faculty`, `/courses`, `/sync` all rendered real ERP data; CORS preflight and POST/DELETE mutations from the `http://localhost:3000` origin worked (temp department created and cleaned up).

### Notes

- No backend code changed this sprint and no tests were removed/weakened — the full backend suite still passes (267).
- No new backend migrations (schema unchanged, migration still at head `0001`).
- Frontend adds no JavaScript dependencies beyond `next`, `react`, `react-dom`.

---

## Sprint 7 - Moodle Integration — 2026-08-17

## Sprint 7 - Moodle Integration — 2026-08-17

### Added

- **Moodle integration layer** (`app/integrations/moodle/`):
  - `client.py` — `MoodleClient`: authenticated REST client against `/webservice/rest/server.php` (wstoken + wsfunction + JSON format), timeouts, and response validation. Maps all failures to typed `MoodleError` subclasses.
  - `errors.py` — `MoodleError`, `MoodleNotConfiguredError`, `MoodleConnectionError`, `MoodleAPIError`.
  - `payloads.py` — pure payload builders mapping ERP records to Moodle WS request params (`core_user_create_users`, `core_course_create_courses`, `enrol_manual_enrol_users`, `core_grades_update_grades`, attendance wsfunction).
- **Config** (`app/core/config.py` + `.env.example`): `MOODLE_BASE_URL`, `MOODLE_WSTOKEN`, `MOODLE_TIMEOUT_SECONDS`, `MOODLE_DEFAULT_CATEGORY_ID`, `MOODLE_STUDENT_ROLE_ID`, `MOODLE_ATTENDANCE_WSFUNCTION`.
- **Repository** (`app/repositories/moodle.py`): `MoodleSyncRepository` reads active students, courses, enrollments, grades, and attendance from the ERP.
- **Service** (`app/services/moodle.py`): `MoodleSyncService` — `check_connection`, `sync_students`, `sync_courses`, `sync_enrollments`, `sync_grades`, `sync_attendance`, `sync_all`. Every operation is idempotent (find-or-create by `roll_number` → Moodle username, `course_code` → Moodle shortname) and records a `sync_logs` entry with the honest outcome (`Success`/`Failed`).
- **API** (`app/api/moodle.py`, registered in `app/main.py`):
  - `GET /integrations/moodle/status` — validates the token via `core_webservice_get_site_info`.
  - `POST /integrations/moodle/sync` — runs the full synchronization and returns a `MoodleSyncResult` summary (`503` when Moodle is not configured).
- **Schemas** (`app/schemas/moodle.py`): `MoodleStatus`, `MoodleSyncResult`.
- **Tests** (`backend/tests/`): `test_moodle_payloads.py`, `test_moodle_client.py` (httpx `MockTransport`), `test_moodle_service.py` (fake client: success, idempotency, partial/full failures, logging), `test_moodle_api.py`. **37 new tests; suite total 267, all passing.**

### Verified

- Full sync run against a simulated Moodle REST server (real HTTP path): 50 students, 20 courses, 120 enrollments, 20 graded courses, 500 attendance records — all `Success`, and a second run was idempotent (0 new users/courses). Sync logs persisted and readable via `GET /sync-logs`.
- `GET /integrations/moodle/status` returns `connected: false` and `/sync` returns `503` when Moodle is not configured (dev default).

### Notes

- No schema change was required; no new migration (still at head `0001`). `sync_logs` is now populated by the integration engine (per decision D27).
- Moodle user/course identity is derived from ERP keys (roll number / course code) because no mapping table exists (and adding one would require a migration). Find-or-create keeps synchronization idempotent.
- Attendance synchronization uses a configurable wsfunction (`MOODLE_ATTENDANCE_WSFUNCTION`, default `mod_attendance_add_take`) because Moodle has no core attendance function — deployment must enable the corresponding plugin/function.
- No fake success: a call is recorded `Success` only when Moodle's real response validates (e.g., `core_grades_update_grades` must return `result: true` with no failures).

---

## Sprint 6 - Dashboard & Reports — 2026-08-17

## Sprint 6 - Dashboard & Reports — 2026-08-17

### Added

- **Dashboard module**:
  - Schema (`app/schemas/dashboard.py`): `OverviewStatistics` — aggregate counts (`departments`, `faculty`, `students`, `courses`, `enrollments`, `attendance_present`, `attendance_absent`, `grades`) plus `grade_distribution` and `students_by_department` breakdowns.
  - Repository (`app/repositories/dashboard.py`): `DashboardRepository` (aggregate `COUNT`s and grouped summaries).
  - Service (`app/services/dashboard.py`): `DashboardService.overview()`.
  - Router (`app/api/dashboard.py`): `GET /dashboard/overview`.
- **Reports module**:
  - Schema (`app/schemas/reports.py`): `CourseEnrollmentReport`, `AttendanceSummaryReport`, `GradeDistributionReport`, `DepartmentCourseReport`.
  - Repository (`app/repositories/reports.py`): `ReportsRepository` (enrollments per course, attendance summary, grade distribution, courses per department).
  - Service (`app/services/reports.py`): `ReportsService`.
  - Router (`app/api/reports.py`): `GET /reports/enrollments-by-course`, `/reports/attendance-summary`, `/reports/grade-distribution`, `/reports/courses-by-department`.
- **Sync Log module**:
  - Schemas (`app/schemas/sync_log.py`): `SyncLogRead`, `SyncLogList`.
  - Repository (`app/repositories/sync_log.py`): `SyncLogRepository` including a `create(module, action, status, message)` used by the future Moodle integration (Sprint 7).
  - Service (`app/services/sync_log.py`): `SyncLogService` (`get`, `list_logs` with module/action/status filters + pagination, `record` for the integration engine).
  - Router (`app/api/sync_logs.py`): `GET /sync-logs` and `GET /sync-logs/{sync_log_id}`; `status` query filtered via regex `^(Success|Failed)$`.
- Routers registered in `app/main.py`.
- **Tests** (`backend/tests/`): `test_dashboard.py`, `test_sync_logs.py` (repository, service, API layers). **26 new tests; suite total 230, all passing.**

### Notes

- No schema change was required: all tables existed from migration `0001`; no new migration was created (still at head).
- `sync_logs` read API is exposed now; the table is populated only by the Moodle integration in Sprint 7.
- Grading distribution (`/reports/grade-distribution`) is ordered by frequency descending (highest count first), ties broken by grade label ascending.
- Dashboard/reports are pure read/aggregate endpoints — no writes, no business-logic mutation.

---

## Sprint 5 - Course & Enrollment Modules — 2026-08-17

## Sprint 5 - Course & Enrollment Modules — 2026-08-17

### Added

- **Course module**:
  - Schemas (`app/schemas/course.py`): `CourseCreate`, `CourseUpdate`, `CourseRead`, `CourseList`.
  - Repository (`app/repositories/course.py`): `CourseRepository` (CRUD, `get_by_code`, `department_exists`/`faculty_exists`, `has_children`, list filters `department_id`/`faculty_id`/`semester`/`search`).
  - Service (`app/services/course.py`): `CourseService` + `CourseNotFoundError`, `DuplicateCourseError`, `DepartmentNotFoundError`, `FacultyNotFoundError`, `CourseInUseError`.
  - Router (`app/api/courses.py`): `GET/POST /courses`, `GET/PUT/DELETE /courses/{course_id}`.
  - `DELETE /courses/{id}` hard-deletes only when the course has no enrollments/attendance/grades (else `409`).
- **Enrollment module**:
  - Schemas (`app/schemas/enrollment.py`): `EnrollmentCreate`, `EnrollmentUpdate`, `EnrollmentRead`, `EnrollmentList`.
  - Repository (`app/repositories/enrollment.py`): `EnrollmentRepository` (CRUD, `get_by_unique`, existence helpers, list filters `student_id`/`course_id`/`academic_year`/`semester`).
  - Service (`app/services/enrollment.py`): `EnrollmentService` + `EnrollmentNotFoundError`, `DuplicateEnrollmentError`, `StudentNotFoundError`, `CourseNotFoundError`.
  - Router (`app/api/enrollments.py`): `GET/POST /enrollments`, `GET/PUT/DELETE /enrollments/{enrollment_id}`.
  - Enforces the `(student_id, course_id, academic_year, semester)` unique enrollment rule (`409` on duplicate).
- **Attendance module**:
  - Schemas (`app/schemas/attendance.py`): `AttendanceCreate`, `AttendanceUpdate`, `AttendanceRead`, `AttendanceList`; `status` constrained (via `Literal`) to `Present`/`Absent`.
  - Repository (`app/repositories/attendance.py`): `AttendanceRepository` (CRUD, `get_by_unique`, list filters `student_id`/`course_id`/`date`/`status`).
  - Service (`app/services/attendance.py`): `AttendanceService` + `AttendanceNotFoundError`, `DuplicateAttendanceError`, `StudentNotFoundError`, `CourseNotFoundError`.
  - Router (`app/api/attendance.py`): `GET/POST /attendance`, `GET/PUT/DELETE /attendance/{attendance_id}`.
  - Enforces the `(student_id, course_id, date)` unique attendance rule (`409` on duplicate).
- **Grade module**:
  - Schemas (`app/schemas/grade.py`): `GradeCreate`, `GradeUpdate`, `GradeRead`, `GradeList` with `Decimal` marks bounded to 0–100 with 2 decimal places.
  - Repository (`app/repositories/grade.py`): `GradeRepository` (CRUD, `get_by_unique`, list filters `student_id`/`course_id`).
  - Service (`app/services/grade.py`): `GradeService` + `GradeNotFoundError`, `DuplicateGradeError`, `StudentNotFoundError`, `CourseNotFoundError`.
  - Router (`app/api/grades.py`): `GET/POST /grades`, `GET/PUT/DELETE /grades/{grade_id}`.
  - Enforces the `(student_id, course_id)` one-final-grade rule (`409` on duplicate).
- **Tests** (`backend/tests/`): `test_courses.py`, `test_enrollments.py`, `test_attendance.py`, `test_grades.py` (repository, service, API layers). Helpers added to `conftest.py` including `seed_student_and_course`. **100 new tests; suite total 204, all passing.**

### Notes

- No schema change was required: all four tables existed from migration `0001`; no new migration was created (still at head).
- Course delete is guarded (`CourseInUseError`, `409`) because courses are referenced by enrollments, attendance, and grades.
- Attendance/grades validate only that the referenced student and course exist (enrollment is not required) — kept minimal and consistent with the documented schema.
- `final_grade` is validated by length only (max 5 chars), matching the DB which has no check constraint on it.
- Attendance `status` is enforced at the schema level (`Literal`) to match the DB check constraint `Present/Absent`.

---

## Sprint 4 - Faculty & Department Modules — 2026-08-17

### Added

- **Department module**:
  - Schemas (`app/schemas/department.py`): `DepartmentCreate`, `DepartmentUpdate` (partial), `DepartmentRead`, `DepartmentList`.
  - Repository (`app/repositories/department.py`): `DepartmentRepository` with `get`, `get_by_code`, `get_by_name` (case-insensitive), `exists`, `has_children`, `list` (search + limit/offset pagination), `create`, `update`, `delete`.
  - Service (`app/services/department.py`): `DepartmentService` with domain exceptions `DepartmentNotFoundError`, `DuplicateDepartmentError`, `DepartmentInUseError`.
  - Router (`app/api/departments.py`): `GET/POST /departments`, `GET/PUT/DELETE /departments/{department_id}`. Registered in `app/main.py`.
  - `DELETE /departments/{id}` hard-deletes only when the department has **no** faculty, students, or courses assigned (otherwise `409 Conflict`).
- **Faculty module**:
  - Schemas (`app/schemas/faculty.py`): `FacultyCreate`, `FacultyUpdate` (partial), `FacultyRead`, `FacultyList` with regex email validation/normalization (same approach as students).
  - Repository (`app/repositories/faculty.py`): `FacultyRepository` with `get`, `get_by_employee_id`, `get_by_email` (case-insensitive), `department_exists` (reuses `DepartmentRepository`), `list` (department/status/search filters + pagination), `create`, `update`, `soft_delete`.
  - Service (`app/services/faculty.py`): `FacultyService` with domain exceptions `FacultyNotFoundError`, `DuplicateFacultyError`, `DepartmentNotFoundError`.
  - Router (`app/api/faculty.py`): `GET/POST /faculty`, `GET/PUT/DELETE /faculty/{faculty_id}`. Registered in `app/main.py`.
  - `DELETE /faculty/{id}` is a **soft delete** (`status=false`), matching the Student module.
- **Tests** (`backend/tests/`): `test_departments.py` (repository, service, API layers) and `test_faculty.py` (repository, service, API layers). Shared data helpers `department_data` / `faculty_data` added to `conftest.py`. **59 new tests; suite total 104, all passing.**

### Notes

- No schema change was required: the `departments` and `faculty` tables already existed from migration `0001`; no new migration was created.
- Department delete is guarded (`DepartmentInUseError`) because departments have no `status` column and are referenced by faculty, students, and courses.
- Faculty `department_id` is validated against `departments` before create/update (`400` when missing).
- OpenAPI/Swagger renders all department and faculty endpoints (`/docs`).

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
