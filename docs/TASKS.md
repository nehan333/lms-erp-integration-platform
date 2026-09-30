# Tasks

## Current Sprint: Sprint 10 — Final Integration, Validation & Release Readiness

Not started. The active sprint details are in `docs/SPRINT.md`.

### Preparation

- [ ] Re-read `docs/PROJECT.md`, `docs/SPRINT.md`, `docs/HANDOVER.md`, `docs/PRESENTATION.md`
- [ ] Confirm final scope: no new features — validation, bug fixes, consistency, readiness

### End-to-End Validation

- [ ] Backend suite green (`cd backend && uv run pytest` → 272 passing)
- [ ] Frontend build + tests green (`cd frontend && npm run build && npm test` → 6 passing)
- [ ] Live E2E: dashboard, reports, CRUD flows, Moodle status/sync behavior
- [ ] Alembic migration head + seed integrity (no drift, `alembic check` clean)

### Consistency

- [ ] Cross-check docs: `CHANGELOG`, `SPRINTS`, `SPRINT`, `AI_CONTEXT`, `HANDOVER`, `API`, `DECISIONS`, `PRESENTATION`
- [ ] Verify READMEs (root, `backend/README.md`, `frontend/README.md`) match reality
- [ ] Resolve any documentation vs. implementation mismatches

### Fixes

- [ ] Fix any bugs discovered during validation

### Sign-off

- [ ] Mark the project ready for manual deployment / presentation
- [ ] Update `docs/CHANGELOG.md`, `docs/SPRINTS.md`, `docs/SPRINT.md` (project complete), `docs/AI_CONTEXT.md`, `docs/HANDOVER.md`, `docs/PROMPTS.md`

### Review

- [ ] Final review of all changes
- [ ] Verify nothing out of scope was touched (no production deployment)