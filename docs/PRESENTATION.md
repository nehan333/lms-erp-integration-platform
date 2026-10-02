# Presentation & Runbook

Quick reference for presenting the LMS–ERP Integration Platform and for running it end to end.

## 1. What the platform does

A College ERP that is the **single source of truth** for academic data, with an integration engine that keeps **Moodle** in sync as the LMS.

- Manage **students, departments, faculty, courses** (CRUD) plus enrollments, attendance, and grades via a typed REST API.
- See live **dashboard statistics and reports** (enrollments per course, attendance summary, grade distribution, courses per department).
- Push data to **Moodle** (users, courses, enrollments, grades, attendance) through a clean Web Services client — every run is audited in `sync_logs`.
- Browse everything in a **Next.js web UI**.

## 2. Feature list (demo order)

1. **Health / API** — `GET /health`, Swagger at `/docs` (28 documented routes).
2. **Dashboard** — aggregate counts, grade distribution, students by department.
3. **Students / Departments / Faculty / Courses** — create, list, edit, delete (soft-delete for students & faculty; guarded deletes for departments/courses).
4. **Enrollments / Attendance / Grades** — unique-rule enforcement (one enrollment per student–course–year–semester; one final grade per student–course).
5. **Bulk operations** — CSV import of students (`POST /students/bulk`) and one-click cohort enrollment into many courses (`POST /enrollments/bulk`, with a dry-run preview), both syncing to Moodle automatically.
6. **Student detail page** — contact card plus an attendance-by-course breakdown (present / total / percentage per course).
7. **Reports** — attendance summary, enrollments per course, grade distribution, courses per department.
8. **Sync Logs** — audit trail of every Moodle sync (`GET /sync-logs`).
9. **Moodle Integration** — status check and one-click full sync (`/integrations/moodle/status`, `/integrations/moodle/sync`). Idempotent (find-or-create by roll number / course code), honest results (partial failure = `Failed` in the log). Users, courses, enrollments, **grades** and **attendance** all verified against a live Moodle 5.0.10.
10. **Frontend** — Next.js UI for all of the above (17 routes).

## 3. Runbook (local)

### Backend

```bash
cd backend
uv run alembic upgrade head      # apply migration 0001 (idempotent)
uv run python scripts/seed.py    # seed sample data (5/10/50/20/120/500/120)
uv run uvicorn app.main:app --reload   # http://localhost:8000, Swagger /docs
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local  # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                       # http://localhost:3000
```

### Moodle (optional, only when a Moodle instance exists)

Set `MOODLE_BASE_URL` and `MOODLE_WSTOKEN` in `backend/.env`, then use the Sync page or `POST /integrations/moodle/sync`.

## 4. Tests

| Suite   | Command                     | Result       |
| ------- | --------------------------- | ------------ |
| Backend | `cd backend && uv run pytest` | 311 passing  |
| Frontend| `cd frontend && npm test`     | 6 passing    |
| Build   | `cd frontend && npm run build`| 17 routes    |

## 5. Architecture (one slide)

`Next.js (frontend/)` → `FastAPI routers (app/api)` → `services (app/services)` → `repositories (app/repositories)` → `PostgreSQL`; `integrations/moodle` drives the Moodle REST API and records every outcome in `sync_logs`.

## 6. Notable decisions (for Q&A)

- ERP is the source of truth; Moodle only the LMS (D-1/D-29).
- Soft delete for students/faculty; guarded hard delete for departments/courses (409 when in use).
- Moodle identity keyed to roll number / course code — idempotent, no mapping table (D-29).
- No fake success — a sync is `Success` only when Moodle's response validates (D-30).
- Bulk writes are preview-then-execute and idempotent (dry run first, re-runs skip instead of duplicating) (D-37).
- Attendance worked only after granting the plugin capabilities **at the system context** — `role_capabilities` rows with `contextid = 0` are invisible to Moodle's `accesslib`, so the activity looked hidden (D-35).
- Percentages are `null` when there is no data rather than a misleading `0%` or `100%` (D-41).
- No new migrations needed after Sprint 2; schema is stable at migration `0001`.