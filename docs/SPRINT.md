# Current Sprint

## Sprint 4 - Faculty & Department Modules

### Status

Not started.

### Goal

Implement the complete **Faculty Management** and **Department Management** modules for the ERP.

### Scope

- Department CRUD operations
- Faculty CRUD operations
- Department ↔ Faculty relationships
- Repository, Service, and Router layers
- Swagger/OpenAPI documentation
- API endpoints for departments and faculty

### Restrictions

The following are **out of scope** for this sprint:

- No Courses module
- No Enrollment module
- No Attendance / Grades modules
- No Moodle integration
- No Frontend work

### Deliverables

- [ ] Department Repository / Service / Router
- [ ] Faculty Repository / Service / Router
- [ ] Pydantic schemas for Department and Faculty
- [ ] Validation rules
- [ ] CRUD endpoints (create, read, update, delete, list)
- [ ] Swagger/OpenAPI documentation
- [ ] Tests (per project workflow)

### Constraints

- Follow the approved tech stack (FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL, Alembic).
- Follow the existing architecture: **API → Service → Repository → Database**.
- Reuse the existing `Department` / `Faculty` models, `get_db` dependency, and settings.
- Reuse the existing Student-module patterns (schemas, repository, service, router, tests).
- Keep code modular and production-ready.

---

_This file contains ONLY the active sprint. See `docs/SPRINTS.md` for the full roadmap._
