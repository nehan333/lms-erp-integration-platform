# LMS-ERP Backend

Backend foundation for the LMS–ERP Integration Platform: a College ERP that synchronizes academic data with Moodle LMS.

The ERP is the source of truth. Moodle integration is implemented in later sprints.

## Tech Stack

- Python 3.13+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2 + pydantic-settings
- PostgreSQL (psycopg v3)
- uv
- Render

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

3. Run database migrations:

   ```bash
   uv run alembic upgrade head
   ```

 4. Start the development server:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

## Database

### Run Migrations

The initial migration creates all eight ERP tables (departments, faculty, students, courses, enrollments, attendance, grades, sync_logs):

```bash
uv run alembic upgrade head
```

To undo the latest migration:

```bash
uv run alembic downgrade -1
```

### Seed the Database

Populate the database with realistic sample data (5 departments, 10 faculty, 50 students, 20 courses, 120 enrollments, 500 attendance records, 120 grades). The schema must exist first.

```bash
uv run python -m scripts.seed
```

To wipe existing data and reseed:

```bash
uv run python -m scripts.seed --reset
```

See [docs/DATABASE.md](../docs/DATABASE.md) for the full database design and [docs/ERD.md](../docs/ERD.md) for the entity relationship diagram.

## Health Check

```bash
curl http://localhost:8000/health
```

## Tests

The pytest suite covers the implemented modules (repository, service, and API layers). It runs against a dedicated PostgreSQL test database (`lms_erp_test`) that is created automatically; set `TEST_DATABASE_URL` to override the connection string. The dev/seeded database is never touched.

```bash
uv run pytest
```

Run a single file:

```bash
uv run pytest tests/test_api.py -q
```

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routers (health, students, departments, faculty, courses, enrollments, attendance, grades, dashboard, reports, sync_logs, integrations/moodle)
│   ├── core/             # Settings and logging configuration
│   ├── db/               # Engine, session factory, declarative base
│   ├── integrations/
│   │   └── moodle/       # Moodle REST integration (client, errors, payloads) — Sprint 7
│   ├── middlewares/      # Custom middleware (future sprint)
│   ├── models/           # SQLAlchemy ORM models (Sprint 2)
│   ├── repositories/     # Data-access layer (student, department, faculty, course, enrollment, attendance, grade, dashboard, reports, sync_log, moodle)
│   ├── schemas/          # Pydantic schemas (student, department, faculty, course, enrollment, attendance, grade, dashboard, reports, sync_log, moodle)
│   ├── services/         # Business logic (student, department, faculty, course, enrollment, attendance, grade, dashboard, reports, sync_log, moodle)
│   ├── utils/            # Shared helpers (future sprint)
│   └── main.py           # Application entry point
├── alembic/              # Database migration scripts
├── scripts/              # Utility scripts (database seed)
├── alembic.ini
├── pyproject.toml
└── .env.example
```

## Configuration

Settings are managed with pydantic-settings and read from environment variables (or `.env`).

| Variable        | Description                                  | Default                                                       |
| --------------- | -------------------------------------------- | ------------------------------------------------------------- |
| `PROJECT_NAME`  | Application name                             | `LMS-ERP Integration Platform`                                |
| `ENVIRONMENT`   | Runtime environment                          | `development`                                                 |
| `DEBUG`         | Enable debug behavior (e.g. SQL echo)        | `false`                                                       |
| `LOG_LEVEL`     | Root logger level                            | `INFO`                                                        |
| `DATABASE_URL`  | PostgreSQL connection string (psycopg v3)    | `postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp` |
| `CORS_ORIGINS`  | Allowed origins, comma-separated             | `*`                                                           |
| `MOODLE_BASE_URL` | Moodle site base URL                       | *(empty)*                                                   |
| `MOODLE_WSTOKEN` | Moodle Web Services token                   | *(empty)*                                                   |
| `MOODLE_TIMEOUT_SECONDS` | HTTP timeout for Moodle calls        | `30`                                                         |
| `MOODLE_DEFAULT_CATEGORY_ID` | Moodle category for created courses | `1`                                                          |
| `MOODLE_STUDENT_ROLE_ID` | Moodle student role id for enrolment | `5`                                                          |
| `MOODLE_ATTENDANCE_WSFUNCTION` | Attendance wsfunction to call       | `mod_attendance_add_take`                                    |

## Layer Conventions

Requests flow through **API → Service → Repository → Database**. Business logic stays in services, all SQLAlchemy queries live in repositories, and routers stay thin.
