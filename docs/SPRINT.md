# Current Sprint

## Sprint 10 - Final Integration, Validation & Release Readiness

### Status

In progress — phases A–F delivered (2026-10-02). Remaining: sign-off / presentation readiness.

### Goal

End-to-end review and release readiness.

### Scope

- Full end-to-end validation (backend + frontend + integration)
- Fix discovered bugs
- Final documentation consistency
- Mark the project ready for manual deployment / presentation

**Scope extended at the user's request** to close the bulk-operation and Moodle-sync gaps:

- **A — Bulk course enrollment** with automatic Moodle sync (`POST /enrollments/bulk/preview`, `POST /enrollments/bulk`)
- **B — Attendance sync** working end-to-end against the live Moodle (root cause: `role_capabilities.contextid = 0` → fixed to `1`, decision D35)
- **C — Grade sync** working (letters → numeric `rawgrade`, decision D39)
- **D — Bulk student CSV import** (`POST /students/bulk`, JSON-as-CSV, decision D36)
- **E — Student detail page** with attendance-by-course (`GET /students/{id}/attendance-summary` + `/students/[id]`, `/students/bulk`, `/enrollments`, `/enrollments/bulk` pages)
- **F — Documentation updates** across `docs/*.md`

### Restrictions

The following are **out of scope** for this sprint:

- Production deployment (handled manually by the project owner)

### Deliverables

- [x] Backend suite green (`cd backend && uv run pytest` → **311 passing**, was 272)
- [x] Frontend green (`cd frontend && npm test` → 6 passing, `npm run build` → 17 pages, was 14)
- [x] Live E2E: bulk preview → bulk enroll (Moodle sync `Success`) → idempotent re-run; attendance + grade sync probed against live Moodle; new pages render real data
- [x] Bulk enrollment / bulk import / attendance-summary endpoints documented in `docs/API.md`
- [x] Moodle access fix recorded (`contextid = 1`) in `docs/DECISIONS.md` (D35) and `docs/HANDOVER.md`
- [ ] Alembic migration head + seed integrity (no drift, `alembic check` clean)
- [ ] Final docs cross-check (`CHANGELOG`, `SPRINTS`, `PRESENTATION`, `PROMPTS`, READMEs)
- [ ] Mark the project ready for manual deployment / presentation

### Constraints

- Never delete or weaken existing tests (baseline 272 backend / 6 frontend must keep passing; now 311 / 6).
- No schema changes unless strictly required (migration still at head `0001`).

---

_This file contains ONLY the active sprint. See `docs/SPRINTS.md` for the full roadmap._
