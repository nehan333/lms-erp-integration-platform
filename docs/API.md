# API Reference

> **Status**: `GET /health`, the Student, Department, Faculty (Sprint 3–4), Course, Enrollment, Attendance, Grades (Sprint 5), Dashboard, Reports, Sync Logs (Sprint 6), and Moodle integration (Sprint 7) modules are implemented and documented. Bulk operations and the per-student attendance summary (Sprint 10 scope) are documented in §4.2 and §4.6.

## 1. Overview

- Base URL (local): `http://localhost:8000`
- Format: JSON
- Interactive docs: Swagger UI at `/docs`, ReDoc at `/redoc`
- OpenAPI schema: `/openapi.json`

## 2. Conventions

- REST resource naming (plural nouns, e.g., `/students`).
- Standard HTTP methods: `GET` (read), `POST` (create), `PUT` (update), `DELETE` (delete).
- Status codes: `200 OK`, `201 Created`, `204 No Content`, `400 Bad Request`, `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity`, `500 Internal Server Error`.
- Request/response bodies validated with Pydantic v2 schemas.
- Errors return a JSON body with a `detail` key containing a human-readable message.
- Pagination uses `limit` (1–100, default 10) and `offset` (default 0) query parameters.

## 3. Authentication

- Not implemented yet (future sprint).
- Planned: JWT-based authentication.

## 4. Endpoints by Module

### 4.1 System

#### `GET /health`

Returns service liveness information.

**Response `200 OK`**

```json
{
  "status": "ok",
  "service": "LMS-ERP Integration Platform",
  "version": "0.1.0"
}
```

### 4.2 Students (Sprint 3)

All routes live under the `/students` prefix. `department_id` values must reference an existing department (`departments` table).

#### `GET /students` — List students

Returns a paginated list of students.

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | integer | 10 | Max rows (1–100) |
| `offset` | integer | 0 | Rows to skip |
| `department_id` | UUID | — | Filter by department |
| `semester` | integer | — | Filter by semester (1–10) |
| `status` | boolean | — | Filter by active status (`true`/`false`) |
| `search` | string | — | Case-insensitive match on name, email, or roll number |

**Response `200 OK`** — `StudentList`

```json
{
  "items": [
    {
      "id": "a8098c1a-f86e-11da-bd1a-00112444be1e",
      "roll_number": "CSE24001",
      "name": "Aarav Sharma",
      "email": "cse24001@student.college.edu",
      "phone": "+91 9000000000",
      "department_id": "6f9619ff-8b86-d011-b42d-00cf4fc964ff",
      "semester": 3,
      "section": "A",
      "status": true,
      "created_at": "2026-08-05T21:42:04Z",
      "updated_at": "2026-08-05T21:42:04Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### `POST /students` — Create a student

**Request body** — `StudentCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `roll_number` | string | yes | 1–20 chars, unique |
| `name` | string | yes | 1–100 chars |
| `email` | string | yes | 1–100 chars, valid email format, unique (case-insensitive) |
| `phone` | string | no | max 20 chars |
| `department_id` | UUID | yes | must exist in `departments` |
| `semester` | integer | yes | 1–10 |
| `section` | string | yes | 1–10 chars |
| `status` | boolean | no | defaults to `true` |

**Responses**

- `201 Created` — `StudentRead` (the created student).
- `400 Bad Request` — `department_id` does not reference an existing department.
- `409 Conflict` — a student with the same `email` or `roll_number` already exists.
- `422 Unprocessable Entity` — validation failure (missing field, invalid email, out-of-range value).

#### `GET /students/{student_id}` — Get a student

**Path parameter**: `student_id` (UUID).

**Responses**

- `200 OK` — `StudentRead`.
- `404 Not Found` — no student with that id.

#### `PUT /students/{student_id}` — Update a student

**Path parameter**: `student_id` (UUID).

**Request body** — `StudentUpdate`. All fields optional; only provided fields are applied. `email`/`roll_number` changes are checked for uniqueness against other students; `department_id` changes must reference an existing department.

**Responses**

- `200 OK` — `StudentRead` (the updated student).
- `400 Bad Request` — invalid `department_id`.
- `404 Not Found` — no student with that id.
- `409 Conflict` — `email` or `roll_number` is already in use by another student.
- `422 Unprocessable Entity` — validation failure.

#### `DELETE /students/{student_id}` — Delete a student

Performs a **soft delete**: sets `status` to `false` so the record is preserved for academic history. The record remains retrievable via `GET /students/{student_id}` and visible in `GET /students` when filtered with `status=false`.

**Path parameter**: `student_id` (UUID).

**Responses**

- `204 No Content` — student deactivated.
- `404 Not Found` — no student with that id.

#### `POST /students/bulk` — Bulk import students from CSV

Imports many students in one request. The CSV body travels **inside JSON** (`csv` field) so no multipart upload is required.

**Request body** — `BulkStudentImportRequest`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `csv` | string | yes | 1–1,000,000 chars; header row required |
| `department_id` | UUID | yes | every row is imported into this department |
| `dry_run` | boolean | no | default `false` — validate only, persist nothing |
| `sync_moodle` | boolean | no | default `true` — sync newly created students to Moodle |

**CSV format** — first row is the header (case-insensitive; a UTF-8 BOM is tolerated). Required columns: `roll_number`, `name`, `email`, `semester`, `section`. Optional: `phone`. Unknown columns are ignored.

**Responses**

- `201 Created` — `BulkStudentImportResult`
- `400 Bad Request` — CSV is unusable (missing/invalid header, no data rows, or more than 5000 rows) or `department_id` does not reference an existing department.
- `422 Unprocessable Entity` — body validation failure (e.g. `department_id` not a UUID).

```json
{
  "total": 3,
  "created": 2,
  "skipped": 0,
  "failed": 1,
  "dry_run": false,
  "errors": [{ "row": 4, "error": "email already exists" }],
  "sync_log": { "id": "…", "module": "moodle", "action": "sync_students", "status": "Success", "message": "2 students synced", "created_at": "…", "updated_at": "…" }
}
```

Notes:

- Row numbers in `errors[].row` are **1-based and include the header** (so the first data row is 2).
- `skipped` counts rows rejected for duplicates (same `roll_number`/`email` already in the database); `failed` counts rows that could not be validated at all.
- When nothing is created (or `dry_run: true`) `sync_log` is `null`.
- Rows are inserted in savepoint chunks, so one bad row does not roll back the good ones.
- The CSV is capped at **5000 data rows** (`MAX_BULK_ROWS`); larger files are rejected with `400`.

#### `GET /students/{student_id}/attendance-summary` — Attendance by course

Returns the per-course attendance totals that back the student detail page.

**Path parameter**: `student_id` (UUID).

**Responses**

- `200 OK` — `StudentAttendanceSummary`
- `404 Not Found` — no student with that id.

```json
{
  "student_id": "e6c5bc49-6ad2-4c7f-86d7-b67484c82a94",
  "courses": [
    { "course_id": "245e33ca-…", "course_code": "ME101", "course_name": "Engineering Mechanics", "present": 3, "total": 4, "percentage": 75.0 }
  ],
  "present": 6,
  "total": 8,
  "percentage": 75.0
}
```

Notes:

- Courses with no attendance records for this student are **omitted** from `courses` (they are not guessed at).
- `percentage` is `null` when `total` is 0 — division by zero is never reported as `0` or `100`.

### 4.3 Departments (Sprint 4)

All routes live under the `/departments` prefix.

#### `GET /departments` — List departments

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | integer | 10 | Max rows (1–100) |
| `offset` | integer | 0 | Rows to skip |
| `search` | string | — | Case-insensitive match on name or code |

**Response `200 OK`** — `DepartmentList`

```json
{
  "items": [
    {
      "id": "26ee2020-4818-4645-8a11-1e2db0895edd",
      "department_code": "CSE",
      "department_name": "Computer Science and Engineering",
      "created_at": "2026-08-05T21:42:04Z",
      "updated_at": "2026-08-05T21:42:04Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### `POST /departments` — Create a department

**Request body** — `DepartmentCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `department_code` | string | yes | 1–10 chars, unique |
| `department_name` | string | yes | 1–100 chars, unique |

**Responses**

- `201 Created` — `DepartmentRead`.
- `409 Conflict` — a department with the same `department_code` or `department_name` already exists.
- `422 Unprocessable Entity` — validation failure.

#### `GET /departments/{department_id}` — Get a department

- `200 OK` — `DepartmentRead`.
- `404 Not Found` — no department with that id.

#### `PUT /departments/{department_id}` — Update a department

**Request body** — `DepartmentUpdate`. All fields optional; only provided fields are applied. `department_code`/`department_name` changes are checked for uniqueness against other departments.

**Responses**

- `200 OK` — `DepartmentRead`.
- `404 Not Found` — no department with that id.
- `409 Conflict` — `department_code` or `department_name` is already in use.
- `422 Unprocessable Entity` — validation failure.

#### `DELETE /departments/{department_id}` — Delete a department

Hard-deletes the department, but only when it has **no** faculty, students, or courses assigned.

**Responses**

- `204 No Content` — department deleted.
- `404 Not Found` — no department with that id.
- `409 Conflict` — the department still has faculty, students, or courses (delete refused).

### 4.4 Faculty (Sprint 4)

All routes live under the `/faculty` prefix. `department_id` values must reference an existing department (`departments` table).

#### `GET /faculty` — List faculty

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | integer | 10 | Max rows (1–100) |
| `offset` | integer | 0 | Rows to skip |
| `department_id` | UUID | — | Filter by department |
| `status` | boolean | — | Filter by active status (`true`/`false`) |
| `search` | string | — | Case-insensitive match on name, email, or employee id |

**Response `200 OK`** — `FacultyList`

```json
{
  "items": [
    {
      "id": "f8d3b52c-9a1e-4b7c-9e02-1c2f8b41d7aa",
      "employee_id": "FAC001",
      "name": "Dr. Meera Iyer",
      "email": "meera.iyer@college.edu",
      "phone": "+91 9000000001",
      "designation": "Assistant Professor",
      "department_id": "26ee2020-4818-4645-8a11-1e2db0895edd",
      "status": true,
      "created_at": "2026-08-05T21:42:04Z",
      "updated_at": "2026-08-05T21:42:04Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### `POST /faculty` — Create a faculty member

**Request body** — `FacultyCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `employee_id` | string | yes | 1–20 chars, unique |
| `name` | string | yes | 1–100 chars |
| `email` | string | yes | 1–100 chars, valid email format, unique (case-insensitive) |
| `phone` | string | no | max 20 chars |
| `designation` | string | yes | 1–100 chars |
| `department_id` | UUID | yes | must exist in `departments` |
| `status` | boolean | no | defaults to `true` |

**Responses**

- `201 Created` — `FacultyRead`.
- `400 Bad Request` — `department_id` does not reference an existing department.
- `409 Conflict` — a faculty member with the same `email` or `employee_id` already exists.
- `422 Unprocessable Entity` — validation failure.

#### `GET /faculty/{faculty_id}` — Get a faculty member

- `200 OK` — `FacultyRead`.
- `404 Not Found` — no faculty member with that id.

#### `PUT /faculty/{faculty_id}` — Update a faculty member

**Request body** — `FacultyUpdate`. All fields optional; only provided fields are applied. `email`/`employee_id` changes are checked for uniqueness against other faculty; `department_id` changes must reference an existing department.

**Responses**

- `200 OK` — `FacultyRead`.
- `400 Bad Request` — invalid `department_id`.
- `404 Not Found` — no faculty member with that id.
- `409 Conflict` — `email` or `employee_id` is already in use by another faculty member.
- `422 Unprocessable Entity` — validation failure.

#### `DELETE /faculty/{faculty_id}` — Delete (deactivate) a faculty member

Performs a **soft delete**: sets `status` to `false` so the record is preserved for academic history. The record remains retrievable via `GET /faculty/{faculty_id}` and visible in `GET /faculty` when filtered with `status=false`.

**Responses**

- `204 No Content` — faculty member deactivated.
- `404 Not Found` — no faculty member with that id.

### 4.5 Courses (Sprint 5)

All routes live under the `/courses` prefix.

#### `GET /courses` — List courses

**Query parameters**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `limit` | integer | 10 | Max rows (1–100) |
| `offset` | integer | 0 | Rows to skip |
| `department_id` | UUID | — | Filter by department |
| `faculty_id` | UUID | — | Filter by faculty |
| `semester` | integer | — | Filter by semester (1–10) |
| `search` | string | — | Case-insensitive match on name or code |

**Response `200 OK`** — `CourseList` (`items`, `total`, `limit`, `offset`).

#### `POST /courses` — Create a course

**Request body** — `CourseCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `course_code` | string | yes | 1–20 chars, unique |
| `course_name` | string | yes | 1–150 chars |
| `credits` | integer | yes | 1–10 |
| `semester` | integer | yes | 1–10 |
| `department_id` | UUID | yes | must exist in `departments` |
| `faculty_id` | UUID | no | must exist in `faculty` if provided |

**Responses**

- `201 Created` — `CourseRead`.
- `400 Bad Request` — invalid `department_id` / `faculty_id`.
- `409 Conflict` — a course with the same `course_code` already exists.
- `422 Unprocessable Entity` — validation failure.

#### `GET /courses/{course_id}` — Get a course

- `200 OK` — `CourseRead`.
- `404 Not Found` — no course with that id.

#### `PUT /courses/{course_id}` — Update a course

**Request body** — `CourseUpdate`. All fields optional; only provided fields are applied.

**Responses**

- `200 OK` — `CourseRead`.
- `400 Bad Request` — invalid `department_id` / `faculty_id`.
- `404 Not Found` — no course with that id.
- `409 Conflict` — `course_code` is already in use.

#### `DELETE /courses/{course_id}` — Delete a course

Hard-deletes the course only when it has **no** enrollments, attendance, or grades.

**Responses**

- `204 No Content` — course deleted.
- `404 Not Found` — no course with that id.
- `409 Conflict` — course still has enrollments/attendance/grades.

### 4.6 Enrollments (Sprint 5)

All routes live under the `/enrollments` prefix. A student cannot be enrolled in the same course twice within the same academic year and semester (`409` on duplicate).

#### `GET /enrollments` — List enrollments

**Query parameters**: `limit`, `offset`, `student_id`, `course_id`, `academic_year`, `semester`.

**Response `200 OK`** — `EnrollmentList` (`items`, `total`, `limit`, `offset`).

#### `POST /enrollments` — Create an enrollment

**Request body** — `EnrollmentCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `student_id` | UUID | yes | must exist in `students` |
| `course_id` | UUID | yes | must exist in `courses` |
| `academic_year` | string | yes | 1–20 chars |
| `semester` | integer | yes | 1–10 |

**Responses**

- `201 Created` — `EnrollmentRead`.
- `400 Bad Request` — invalid `student_id` / `course_id`.
- `409 Conflict` — duplicate student/course/year/semester.
- `422 Unprocessable Entity` — validation failure.

#### `GET /enrollments/{enrollment_id}` — Get an enrollment

- `200 OK` — `EnrollmentRead`.
- `404 Not Found` — no enrollment with that id.

#### `PUT /enrollments/{enrollment_id}` — Update an enrollment

**Request body** — `EnrollmentUpdate`. All fields optional; the unique combination is re-checked after updates.

**Responses**

- `200 OK` — `EnrollmentRead`.
- `400 Bad Request` — invalid `student_id` / `course_id`.
- `404 Not Found` — no enrollment with that id.
- `409 Conflict` — the resulting combination already exists.

#### `DELETE /enrollments/{enrollment_id}` — Delete an enrollment

- `204 No Content` — enrollment deleted.
- `404 Not Found` — no enrollment with that id.

#### `POST /enrollments/bulk/preview` — Preview a bulk enrollment (dry run)

Resolves a department cohort (all **active** students of `department_id` at `semester`) and reports how many enrollment rows would be created, without writing anything.

**Request body** — `BulkEnrollmentRequest`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `department_id` | UUID | yes | must exist in `departments` |
| `semester` | integer | yes | 1–10 |
| `academic_year` | string | yes | 1–20 chars |
| `course_ids` | UUID[] | yes | 1–50 courses; each must exist **and belong to `department_id`** |

**Responses**

- `200 OK` — `BulkEnrollmentPreview`
- `404 Not Found` — unknown `department_id`.
- `400 Bad Request` — unknown `course_id`, or a course that belongs to another department.
- `422 Unprocessable Entity` — body validation failure.

```json
{
  "department_id": "c4cf1a11-…",
  "semester": 1,
  "academic_year": "2025-26",
  "students_total": 1,
  "courses": [
    { "course_id": "5aa58ef9-…", "course_code": "CS101", "course_name": "Data Structures", "to_create": 1, "already_enrolled": 0 }
  ],
  "total_to_create": 1,
  "total_already_enrolled": 0
}
```

#### `POST /enrollments/bulk` — Bulk enroll a cohort (auto-syncs to Moodle)

Same request body as `/bulk/preview`. Creates every missing `student × course` pair for the cohort, skips pairs that already exist, and then **synchronously pushes the newly created enrollments to Moodle** (`enrol_manual_enrol_users`).

**Responses**

- `201 Created` — `BulkEnrollmentResult` (with `sync_log` present when anything was created)
- `404 Not Found` — unknown `department_id`.
- `400 Bad Request` — unknown `course_id`, or a course from another department.
- `422 Unprocessable Entity` — body validation failure.

```json
{
  "department_id": "c4cf1a11-…",
  "semester": 1,
  "academic_year": "2025-26",
  "students_total": 1,
  "created": 1,
  "skipped": 0,
  "courses": [{ "course_id": "5aa58ef9-…", "course_code": "CS101", "created": 1, "skipped": 0 }],
  "sync_log": { "id": "c38636c6-…", "module": "moodle", "action": "sync_enrollments", "status": "Success", "message": "1 enrollments synced", "created_at": "…", "updated_at": "…" }
}
```

Notes:

- **Idempotent**: re-running the same request reports `created: 0` and `skipped: N`; no duplicate rows and no duplicate Moodle enrolments.
- When nothing is created (or Moodle is not configured) `sync_log` reflects the sync attempt or is absent — see decision **D30** (partial/failed syncs are logged honestly as `Failed`, never as success).
- `service.bulk_create()` returns the created ids; the router runs `MoodleSyncService.sync_enrollments(enrollment_ids=…)` and attaches the resulting `sync_log`.

### 4.7 Attendance (Sprint 5)

All routes live under the `/attendance` prefix. `status` is one of `Present` / `Absent`.

#### `GET /attendance` — List attendance

**Query parameters**: `limit`, `offset`, `student_id`, `course_id`, `date`, `status` (`Present`/`Absent`).

**Response `200 OK`** — `AttendanceList` (`items`, `total`, `limit`, `offset`).

#### `POST /attendance` — Create an attendance record

**Request body** — `AttendanceCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `student_id` | UUID | yes | must exist in `students` |
| `course_id` | UUID | yes | must exist in `courses` |
| `date` | date | yes | ISO date |
| `status` | string | yes | `Present` or `Absent` |

**Responses**

- `201 Created` — `AttendanceRead`.
- `400 Bad Request` — invalid `student_id` / `course_id`.
- `409 Conflict` — a record for the same student/course/date already exists.
- `422 Unprocessable Entity` — validation failure (incl. invalid status).

#### `GET /attendance/{attendance_id}` — Get an attendance record

- `200 OK` — `AttendanceRead`.
- `404 Not Found` — no record with that id.

#### `PUT /attendance/{attendance_id}` — Update an attendance record

**Request body** — `AttendanceUpdate`. All fields optional.

**Responses**: `200 OK` / `400` / `404` / `409` (duplicate student/course/date).

#### `DELETE /attendance/{attendance_id}` — Delete an attendance record

- `204 No Content` / `404 Not Found`.

### 4.8 Grades (Sprint 5)

All routes live under the `/grades` prefix. A student receives one final grade per course (unique `student_id` + `course_id`).

#### `GET /grades` — List grades

**Query parameters**: `limit`, `offset`, `student_id`, `course_id`.

**Response `200 OK`** — `GradeList` (`items`, `total`, `limit`, `offset`).

#### `POST /grades` — Create a grade record

**Request body** — `GradeCreate`

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `student_id` | UUID | yes | must exist in `students` |
| `course_id` | UUID | yes | must exist in `courses` |
| `internal_marks` | decimal | yes | 0–100, up to 2 dp |
| `external_marks` | decimal | yes | 0–100, up to 2 dp |
| `final_grade` | string | yes | 1–5 chars |

**Responses**

- `201 Created` — `GradeRead`.
- `400 Bad Request` — invalid `student_id` / `course_id`.
- `409 Conflict` — a grade for the same student/course already exists.
- `422 Unprocessable Entity` — validation failure.

#### `GET /grades/{grade_id}` — Get a grade record

- `200 OK` / `404 Not Found`.

#### `PUT /grades/{grade_id}` — Update a grade record

**Request body** — `GradeUpdate`. All fields optional; marks recomputed not automatic.

**Responses**: `200 OK` / `404 Not Found`.

#### `DELETE /grades/{grade_id}` — Delete a grade record

- `204 No Content` / `404 Not Found`.

### 4.9 Dashboard (Sprint 6)

Read-only aggregate statistics. All routes under `/dashboard`.

#### `GET /dashboard/overview` — Overview statistics

**Response `200 OK`** — `OverviewStatistics`:

| Field | Type | Description |
|-------|------|-------------|
| `departments` | int | total departments |
| `faculty` | int | total faculty |
| `students` | int | total students |
| `courses` | int | total courses |
| `enrollments` | int | total enrollments |
| `attendance_present` | int | present attendance records |
| `attendance_absent` | int | absent attendance records |
| `grades` | int | total grade records |
| `grade_distribution` | list | `{grade, count}` |
| `students_by_department` | list | `{department_id, department_code, department_name, student_count}` |

### 4.10 Reports (Sprint 6)

Read-only aggregate reports. All routes under `/reports`.

#### `GET /reports/enrollments-by-course` — Enrollments per course

**Response `200 OK`** — list of `CourseEnrollmentReport` (`course_id`, `course_code`, `course_name`, `enrollment_count`).

#### `GET /reports/attendance-summary` — Attendance summary

**Response `200 OK`** — `AttendanceSummaryReport` (`total`, `present`, `absent`, `present_percent`).

#### `GET /reports/grade-distribution` — Grade distribution

**Response `200 OK`** — list of `GradeDistributionReport` (`grade`, `count`) ordered by grade precedence.

#### `GET /reports/courses-by-department` — Courses per department

**Response `200 OK`** — list of `DepartmentCourseReport` (`department_id`, `department_code`, `department_name`, `course_count`).

### 4.11 Sync Logs (Sprint 6)

Read-only access to integration/synchronization logs. All routes under `/sync-logs`.

#### `GET /sync-logs` — List sync log entries

**Query parameters**: `limit`, `offset`, `module`, `action`, `status` (`Success`/`Failed`).

**Response `200 OK`** — `SyncLogList` (`items`, `total`, `limit`, `offset`).

#### `GET /sync-logs/{sync_log_id}` — Get a sync log entry

- `200 OK` / `404 Not Found`.

### 4.12 Moodle Integration (Sprint 7)

Endpoints to check and trigger ERP → Moodle synchronization. Requires `MOODLE_BASE_URL` and `MOODLE_WSTOKEN` to be configured.

#### `GET /integrations/moodle/status` — Check Moodle connection and token

Validates the token via Moodle's `core_webservice_get_site_info`.

**Responses**

- `200 OK` — `MoodleStatus` (`connected`, `site_name`, `moodle_version`, `message`). When Moodle is not configured or unreachable, `connected` is `false` with a descriptive `message`.

#### `POST /integrations/moodle/sync` — Run full ERP → Moodle synchronization

Runs, in order: `sync_students`, `sync_courses`, `sync_enrollments`, `sync_grades`, `sync_attendance`. Each operation writes a `sync_logs` entry (`module=moodle`) with the honest outcome.

**Responses**

- `200 OK` — `MoodleSyncResult` (`total`, `success`, `failed`, `logs`).
- `503 Service Unavailable` — Moodle not configured.
- `502 Bad Gateway` — unexpected integration error.

## 5. Schemas

- `StudentCreate` — create payload (see section 4.2).
- `StudentUpdate` — partial update payload (all fields optional).
- `StudentRead` — student response (all model fields plus `id`, `created_at`, `updated_at`).
- `StudentList` — paginated response (`items`, `total`, `limit`, `offset`).
- `BulkStudentImportRequest` — bulk CSV import payload (`csv`, `department_id`, `dry_run`, `sync_moodle`).
- `BulkStudentImportResult` / `BulkStudentRowError` — bulk import outcome (`total`, `created`, `skipped`, `failed`, `dry_run`, `errors[]`, `sync_log`).
- `StudentAttendanceSummary` / `StudentAttendanceCourse` — per-course attendance breakdown (`present`, `total`, `percentage` with `null` when `total` is 0).
- `DepartmentCreate` / `DepartmentUpdate` / `DepartmentRead` / `DepartmentList` — department payloads and responses (see section 4.3).
- `FacultyCreate` / `FacultyUpdate` / `FacultyRead` / `FacultyList` — faculty payloads and responses (see section 4.4).
- `CourseCreate` / `CourseUpdate` / `CourseRead` / `CourseList` — course payloads and responses (see section 4.5).
- `EnrollmentCreate` / `EnrollmentUpdate` / `EnrollmentRead` / `EnrollmentList` — enrollment payloads and responses (see section 4.6).
- `BulkEnrollmentRequest` / `BulkEnrollmentPreview` / `BulkEnrollmentResult` — bulk enrollment payload, dry-run preview, and outcome (see section 4.6).
- `AttendanceCreate` / `AttendanceUpdate` / `AttendanceRead` / `AttendanceList` — attendance payloads and responses (see section 4.7).
- `GradeCreate` / `GradeUpdate` / `GradeRead` / `GradeList` — grade payloads and responses (see section 4.8).
- `OverviewStatistics` — dashboard overview response (see section 4.9).
- `CourseEnrollmentReport` / `AttendanceSummaryReport` / `GradeDistributionReport` / `DepartmentCourseReport` — report responses (see section 4.10).
- `SyncLogRead` / `SyncLogList` — sync log responses (see section 4.11).
- `MoodleStatus` / `MoodleSyncResult` — Moodle integration responses (see section 4.12).

## 6. Error Handling

Domain errors are mapped to HTTP responses; raw database exceptions are never exposed to clients.

| Domain error | HTTP status |
|--------------|-------------|
| `StudentNotFoundError` | `404 Not Found` |
| `DuplicateStudentError` (email/roll_number) | `409 Conflict` |
| `DepartmentNotFoundError` (student module) | `400 Bad Request` |
| `DepartmentNotFoundError` (department module) | `404 Not Found` |
| `DuplicateDepartmentError` (code/name) | `409 Conflict` |
| `DepartmentInUseError` | `409 Conflict` |
| `FacultyNotFoundError` | `404 Not Found` |
| `DuplicateFacultyError` (email/employee_id) | `409 Conflict` |
| `DepartmentNotFoundError` (faculty module) | `400 Bad Request` |
| `CourseNotFoundError` | `404 Not Found` |
| `DuplicateCourseError` (code) | `409 Conflict` |
| `FacultyNotFoundError` / `DepartmentNotFoundError` (course module) | `400 Bad Request` |
| `CourseInUseError` | `409 Conflict` |
| `EnrollmentNotFoundError` | `404 Not Found` |
| `DuplicateEnrollmentError` | `409 Conflict` |
| `StudentNotFoundError` / `CourseNotFoundError` (enrollment module) | `400 Bad Request` |
| `AttendanceNotFoundError` | `404 Not Found` |
| `DuplicateAttendanceError` | `409 Conflict` |
| `GradeNotFoundError` | `404 Not Found` |
| `DuplicateGradeError` | `409 Conflict` |
| `StudentNotFoundError` / `CourseNotFoundError` (attendance/grade modules) | `400 Bad Request` |
| `BulkImportFormatError` (bulk student import) | `400 Bad Request` |
| `DepartmentNotFoundError` (bulk student import) | `400 Bad Request` |
| `DepartmentNotFoundError` (bulk enrollment) | `404 Not Found` |
| `CourseNotInDepartmentError` (bulk enrollment) | `400 Bad Request` |
| `StudentNotFoundError` (`/students/{id}/attendance-summary`) | `404 Not Found` |
| Pydantic validation failure | `422 Unprocessable Entity` |
| Unexpected internal error | `500 Internal Server Error` |

## 7. Versioning

- No version prefix currently. To be decided when the first release is prepared.
