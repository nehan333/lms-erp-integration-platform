# Contributing

Guidelines for contributing to the LMS–ERP Integration Platform.

## 1. Naming Conventions

### Python / Backend

- **Files**: `snake_case.py` (e.g., `student.py`, `department.py`).
- **Classes**: `PascalCase` (e.g., `StudentRepository`, `StudentService`).
- **Functions & methods**: `snake_case` (e.g., `get_student`, `create_student`).
- **Variables**: `snake_case`.
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ROWS`).
- **Private members**: leading underscore (e.g., `_validate_email`).
- **Pydantic schemas**: `PascalCase` with a role suffix: `StudentCreate`, `StudentUpdate`, `StudentRead`.
- **Repositories/services**: `<Entity>Repository`, `<Entity>Service`.

### Database

- **Tables**: lowercase plural `snake_case` (e.g., `students`, `sync_logs`).
- **Columns**: lowercase `snake_case`.
- **Constraints**: prefixed — `pk_<table>`, `fk_<table>_<col>_<table>`, `uq_<table>_<cols>`, `ck_<table>_<name>`, `ix_<table>_<cols>`.
- **Migration revisions**: sequential ids (`0001`, `0002`, ...) with descriptive slugs.

### API

- **Routes**: lowercase plural nouns (e.g., `/students`).
- **Query params**: `snake_case`.

### Frontend

- Follow Next.js/JavaScript conventions (PascalCase components, camelCase variables).

## 2. Folder Conventions

- **Backend** lives entirely under `backend/`; **frontend** under `frontend/` (kept separate).
- Each module spans the appropriate layers:

  ```
  app/models/<entity>.py        # ORM model
  app/schemas/<entity>.py       # Pydantic schemas
  app/repositories/<entity>.py  # data access
  app/services/<entity>.py      # business logic
  app/api/<entity>.py           # router
  ```

- Layer dependency direction: **API → Service → Repository → Database**.
- Documentation lives in `docs/`.
- Utility scripts live in `backend/scripts/`.

## 3. Branch Naming Suggestions

- Main branch: `main`.
- Feature branches: `feature/<sprint>-<scope>` (e.g., `feature/sprint3-student-crud`).
- Fix branches: `fix/<short-description>` (e.g., `fix/student-email-validation`).
- Docs branches: `docs/<short-description>`.
- Keep branches short-lived and scoped to one sprint.

## 4. Code Style

- Python 3.13+, type hints on all public functions and methods.
- SQLAlchemy 2.0 style: `Mapped[...]` + `mapped_column`, no legacy `Query` API.
- Pydantic v2 style: `field_validator` / `model_validator`, no v1 `validator`.
- Never hardcode credentials; use environment variables via settings.
- No placeholder code, no `TODO` comments.
- Keep functions small and focused; reuse existing layers and utilities.
- Follow existing patterns in the repository before inventing new ones.

## 5. Review Process

- Every change must target **only the current sprint** scope.
- Verify no files outside the sprint scope were modified.
- Run the test suite (when tests exist) and fix failures before requesting review.
- Check migrations: every model change ships with an Alembic migration.
- Update documentation that the change affects (`CHANGELOG.md`, `SPRINTS.md`, `AI_CONTEXT.md`, `TASKS.md`, `PROMPTS.md`, `HANDOVER.md`).
- Request review with a clear summary of what changed and why.

## 6. Commit Messages

- Present tense, imperative mood (e.g., `Add student CRUD endpoints`).
- Keep commits scoped and readable.
