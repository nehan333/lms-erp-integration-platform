# Handover — How to Continue Development

This is the most important document. It tells any future AI (or engineer) exactly how to continue development without breaking the project.

**Read `docs/AI_CONTEXT.md` and this file first.**

---

## 1. Which Files Must Be Read First

Read, in order:

1. `docs/PROJECT.md` — the master project specification (vision, scope, stack, coding standards).
2. `docs/HANDOVER.md` — this file.
3. `docs/AI_CONTEXT.md` — project snapshot (status, sprints, decisions, database, roadmap).
4. `docs/SPRINT.md` — the **only** active sprint.
5. `docs/SPRINTS.md` — full roadmap and what is completed.
6. `docs/DATABASE.md` + `docs/ERD.md` — current database design (before touching models/migrations).
7. `docs/ARCHITECTURE.md` — layered architecture and folder responsibilities.
8. `docs/TASKS.md` — the current sprint checklist.
9. `docs/DECISIONS.md` — architectural decisions and their reasons.
10. `backend/README.md` — how to run, migrate, and seed the backend.

Code reference files (read when touching that layer):

- `backend/app/models/*` — ORM models.
- `backend/app/db/session.py` — engine/session/`get_db`.
- `backend/app/core/config.py` — settings.
- `backend/alembic/versions/*` — migrations.
- `backend/scripts/seed.py` — seed data.
- `backend/app/schemas/student.py` — Pydantic schemas (reference pattern for new modules).
- `backend/app/schemas/department.py`, `backend/app/schemas/faculty.py` — department/faculty schemas.
- `backend/app/repositories/student.py` — repository pattern.
- `backend/app/repositories/department.py`, `backend/app/repositories/faculty.py` — department/faculty repositories.
- `backend/app/services/student.py` — service + domain exception pattern.
- `backend/app/services/department.py`, `backend/app/services/faculty.py` — department/faculty services.
- `backend/app/api/students.py` — router + error-mapping pattern.
- `backend/app/api/departments.py`, `backend/app/api/faculty.py` — department/faculty routers.
- `backend/app/schemas/course.py|enrollment.py|attendance.py|grade.py` — Sprint 5 schemas.
- `backend/app/repositories/course.py|enrollment.py|attendance.py|grade.py` — Sprint 5 repositories.
- `backend/app/services/course.py|enrollment.py|attendance.py|grade.py` — Sprint 5 services.
- `backend/app/api/courses.py|enrollments.py|attendance.py|grades.py` — Sprint 5 routers.
- `backend/app/integrations/moodle/*` — Sprint 7 Moodle integration layer.
- `frontend/lib/api.js` — frontend API client.
- `frontend/components/EntityForm.js` — reusable CRUD form.
- `frontend/app/page.js` — dashboard page pattern (server component fetching the API).
- `frontend/tests/*` — frontend tests (Node built-in runner).
- `backend/tests/*` — pytest fixtures and test patterns (dedicated `lms_erp_test` database).

## 2. How to Determine the Current Sprint

- The **authoritative** source is `docs/SPRINT.md` — it contains ONLY the active sprint.
- Cross-check with `docs/SPRINTS.md` (status markers: ✅ completed, ⏳ current) and `docs/AI_CONTEXT.md`.
- Do **not** infer the sprint from code — code may only exist for completed sprints.

If `docs/SPRINT.md` does not match what the user asks for, ask for clarification before writing code.

## 3. How to Avoid Implementing Future Sprints

- Implement **only** what is described in `docs/SPRINT.md` and the current sprint instructions.
- Before generating anything, ask: *"Does this belong to the current sprint?"* If not, do not generate it.
- Do **not** create models, migrations, endpoints, or modules for sprints beyond the current one.
- Do **not** "prepare" for future sprints (no placeholder implementations, no `TODO` comments).
- If a folder is needed later (e.g., `repositories/`, `services/`), leave it empty with an `__init__.py`.
- If something is ambiguous or seems out of scope, **ask** instead of assuming.

## 4. Rules of Engagement (non-negotiable)

- Follow `docs/PROJECT.md` and the approved tech stack exactly.
- Never introduce libraries/frameworks outside the stack.
- Never modify the database directly; always use Alembic migrations.
- Never hardcode credentials; use environment variables.
- Do not commit unless explicitly asked.
- Do not install packages or run commands unless explicitly asked and the task permits it.
- Keep frontend and backend separate.

## 5. How to Update Documentation After Each Sprint

After completing a sprint, update **all** of the following so the next agent has an accurate picture:

- `docs/SPRINTS.md` — mark the completed sprint `✅` and move the `⏳` marker to the next sprint.
- `docs/SPRINT.md` — replace with the next sprint's details.
- `docs/AI_CONTEXT.md` — update status, completed/current sprints, module, database status, limitations.
- `docs/CHANGELOG.md` — append the completed sprint under a dated heading.
- `docs/TASKS.md` — replace with the next sprint's unchecked checklist.
- `docs/PROMPTS.md` — append the sprint prompt summary.
- `docs/HANDOVER.md` — update this file if anything about the workflow changed.
- `docs/API.md` — document any endpoints created.
- `docs/DATABASE.md` / `docs/ERD.md` — update if the schema changed.

Checklist after each sprint:

- [ ] Sprint work complete and verified
- [ ] `SPRINTS.md` status updated
- [ ] `SPRINT.md` points to the next sprint
- [ ] `CHANGELOG.md` updated
- [ ] `TASKS.md` updated
- [ ] `PROMPTS.md` updated
- [ ] `AI_CONTEXT.md` updated
- [ ] `API.md` updated if endpoints changed
- [ ] `DATABASE.md` / `ERD.md` updated if schema changed
- [ ] `HANDOVER.md` reviewed

## 6. Current State Summary

- **Completed**: Sprint 1 (Backend Foundation), Sprint 2 (Database Design & Foundation), Sprint 3 (Student Management Module), Sprint 4 (Faculty & Department Modules), Sprint 5 (Course & Enrollment Modules incl. Attendance and Grades), Sprint 6 (Dashboard & Reports incl. Sync Logs), Sprint 7 (Moodle Integration), Sprint 8 (Frontend Integration), Sprint 9 (Testing & Final Preparation).
- **Current**: Sprint 10 — Final Integration, Validation & Release Readiness, not started.
- **Database**: 8 tables, migration `0001` applied (still at head), seeded (5/10/50/20/120/500/120), `sync_logs` left empty (dev unchanged post-verification). `uv run alembic check` clean (no model/DB drift).
- **API**: `GET /health`; Student (`/students`), Department (`/departments`), Faculty (`/faculty`), Course (`/courses`), Enrollment (`/enrollments`), Attendance (`/attendance`), Grade (`/grades`) CRUD; Dashboard (`/dashboard/overview`), Reports (`/reports/*`), Sync Logs (`/sync-logs`), Moodle (`/integrations/moodle/status`, `/integrations/moodle/sync`). 24 documented routes.
- **Frontend**: Next.js (JavaScript, CSS Modules, App Router) under `frontend/` — dashboard, reports, CRUD pages (students/departments/faculty/courses), Moodle sync page. Run `npm run dev` (default port 3000); API base configurable via `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- **Running**: backend `uv run uvicorn app.main:app --reload` in `backend/` (Swagger at `/docs`); frontend `npm run dev` in `frontend/`.
- **Tests**: backend `uv run pytest` from `backend/` (272 passing); frontend `npm test` from `frontend/` (6 tests).
- **Presentation**: see `docs/PRESENTATION.md` for a demo runbook and feature list.
- **Reference implementation**: the Student / Department / Faculty / Course / Enrollment / Attendance / Grade modules are the patterns to follow for new modules; `sync_logs` is populated by the Sprint 7 Moodle integration engine.
- **Deployment**: handled manually by the project owner; out of scope for all sprints.

## 7. Golden Rules for AI Agents

1. Read the handover and context files before doing anything.
2. Implement only the current sprint.
3. When in doubt, ask — never assume.
4. Keep every sprint's output self-contained and reviewable.
