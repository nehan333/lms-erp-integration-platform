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
- `backend/app/repositories/student.py` — repository pattern.
- `backend/app/services/student.py` — service + domain exception pattern.
- `backend/app/api/students.py` — router + error-mapping pattern.
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

- **Completed**: Sprint 1 (Backend Foundation), Sprint 2 (Database Design & Foundation), Sprint 3 (Student Management Module).
- **Current**: Sprint 4 — Faculty & Department Modules (not started).
- **Database**: 8 tables, migration `0001` applied (still at head), seeded (5/10/50/20/120/500/120).
- **API**: `GET /health` and the full Student CRUD API (`/students`).
- **Running**: `uv run uvicorn app.main:app --reload` in `backend/`; health check at `GET /health`; Swagger at `GET /docs`.
- **Tests**: `uv run pytest` from `backend/` (45 passing) against the dedicated `lms_erp_test` database.
- **Reference implementation**: the Student module (`app/schemas/student.py`, `app/repositories/student.py`, `app/services/student.py`, `app/api/students.py`, `tests/`) is the pattern to follow for new modules.

## 7. Golden Rules for AI Agents

1. Read the handover and context files before doing anything.
2. Implement only the current sprint.
3. When in doubt, ask — never assume.
4. Keep every sprint's output self-contained and reviewable.
