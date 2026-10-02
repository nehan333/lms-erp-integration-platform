# Tasks

## Current Sprint: Sprint 10 — Final Integration, Validation & Release Readiness

Active — see `docs/SPRINT.md` for scope and status.

### Phases A–F (delivered 2026-10-02)

- [x] **A** — Bulk course enrollment: `POST /enrollments/bulk/preview` + `POST /enrollments/bulk` (auto Moodle sync, idempotent)
- [x] **B** — Attendance sync working: `role_capabilities.contextid` 0 → 1, caches purged, live probe green
- [x] **C** — Grade sync working: letters → numeric points, `str_feedback` carries the original letter
- [x] **D** — Bulk student CSV import: `POST /students/bulk` (JSON-as-CSV, dry-run, targeted Moodle sync)
- [x] **E** — Student detail page with attendance-by-course: `GET /students/{id}/attendance-summary` + `/students/[id]`, `/students/bulk`, `/enrollments`, `/enrollments/bulk`, Nav "Enrollments"
- [x] **F** — Documentation: `AI_CONTEXT`, `CHANGELOG`, `HANDOVER`, `API`, `TASKS`, `SPRINT`, `DECISIONS`

### Validation (remaining)

- [ ] Backend suite green (`cd backend && uv run pytest` → **311 passing**)
- [x] Frontend build + tests green (`cd frontend && npm run build && npm test` → 6 passing, 17 pages)
- [x] Live E2E: bulk enrollment + Moodle sync, attendance/grade sync probe, new pages render real data
- [ ] Alembic migration head + seed integrity (no drift, `alembic check` clean)

### Consistency

- [x] `CHANGELOG`, `SPRINT`, `AI_CONTEXT`, `HANDOVER`, `API`, `DECISIONS`, `TASKS` updated
- [ ] Cross-check remaining docs: `SPRINTS`, `PRESENTATION`, `PROMPTS`, READMEs (root, `backend/README.md`, `frontend/README.md`)
- [ ] Resolve any documentation vs. implementation mismatches

### Sign-off

- [ ] Mark the project ready for manual deployment / presentation
- [ ] Final review of all changes (`git status` / `git diff`)
- [ ] Verify nothing out of scope was touched (no production deployment, no commit unless asked)
