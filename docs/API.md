# API Reference

> **Status**: `GET /health` and the Student module (Sprint 3) are implemented and documented. Faculty, Departments, Courses, Enrollments, Attendance, Grades, Dashboard, and Synchronization endpoints will be documented as their modules are implemented.

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

## 5. Schemas

- `StudentCreate` — create payload (see section 4.2).
- `StudentUpdate` — partial update payload (all fields optional).
- `StudentRead` — student response (all model fields plus `id`, `created_at`, `updated_at`).
- `StudentList` — paginated response (`items`, `total`, `limit`, `offset`).

## 6. Error Handling

Domain errors are mapped to HTTP responses; raw database exceptions are never exposed to clients.

| Domain error | HTTP status |
|--------------|-------------|
| `StudentNotFoundError` | `404 Not Found` |
| `DuplicateStudentError` (email/roll_number) | `409 Conflict` |
| `DepartmentNotFoundError` | `400 Bad Request` |
| Pydantic validation failure | `422 Unprocessable Entity` |
| Unexpected internal error | `500 Internal Server Error` |

## 7. Versioning

- No version prefix currently. To be decided when the first release is prepared.
