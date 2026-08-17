# Tasks

## Current Sprint: Sprint 4 — Faculty & Department Modules

Not started. The active sprint details are in `docs/SPRINT.md`.

### Preparation

- [ ] Re-read `docs/PROJECT.md`, `docs/SPRINT.md`, `docs/HANDOVER.md`
- [ ] Re-read `docs/DATABASE.md` (departments and faculty table design)
- [ ] Review the `Department` and `Faculty` models
- [ ] Review the Sprint 3 Student module as the reference pattern
- [ ] Review the `get_db` dependency, test fixtures, and session setup

### Schemas

- [ ] `DepartmentCreate`, `DepartmentUpdate`, `DepartmentRead`, `DepartmentList`
- [ ] `FacultyCreate`, `FacultyUpdate`, `FacultyRead`, `FacultyList`
- [ ] Validation (department_code / department_name uniqueness, faculty email / employee_id, department existence)

### Repository

- [ ] `DepartmentRepository` with CRUD data-access methods
- [ ] `FacultyRepository` with CRUD data-access methods (incl. filtering by department)
- [ ] Reuse/abstract a base repository if applicable

### Service

- [ ] `DepartmentService` with business logic and duplicate/error handling
- [ ] `FacultyService` with business logic and error handling
- [ ] Department existence validation when creating/updating faculty

### Router / API

- [ ] `GET /departments` — list departments
- [ ] `POST /departments` — create department
- [ ] `GET /departments/{id}` — read department
- [ ] `PUT /departments/{id}` — update department
- [ ] `DELETE /departments/{id}` — delete department
- [ ] `GET /faculty` — list faculty
- [ ] `POST /faculty` — create faculty
- [ ] `GET /faculty/{id}` — read faculty
- [ ] `PUT /faculty/{id}` — update faculty
- [ ] `DELETE /faculty/{id}` — delete faculty
- [ ] Register the department and faculty routers in the application

### Swagger

- [ ] Verify OpenAPI/Swagger documentation renders for department and faculty endpoints

### Tests

- [ ] Tests for department repository/service/API
- [ ] Tests for faculty repository/service/API
- [ ] Run test suite and fix failures

### Documentation

- [ ] Update `docs/CHANGELOG.md` with Sprint 4
- [ ] Update `docs/SPRINTS.md` (mark Sprint 4 completed)
- [ ] Update `docs/AI_CONTEXT.md`
- [ ] Update `docs/HANDOVER.md` if needed
- [ ] Update `docs/TASKS.md` (new sprint)
- [ ] Append Sprint 4 prompt summary to `docs/PROMPTS.md`
- [ ] Update `docs/API.md` with department and faculty endpoints

### Review

- [ ] Code review of all changes
- [ ] Verify no out-of-scope modules were touched
