# Infrastructure

## Overview

The backend is deployed as a container-less Python service on **Render**. Local development uses the same stack to keep parity between environments.

## Development Environment

| Component | Value |
|-----------|-------|
| OS | Linux (any modern distro) |
| Python | 3.13+ |
| Package manager | uv |
| Web framework | FastAPI (ASGI) |
| ASGI server | uvicorn |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| Database | PostgreSQL |
| Driver | psycopg v3 |

## Python / uv

- Dependencies are declared in `backend/pyproject.toml`.
- Lockfile: `backend/uv.lock`.
- Create the environment and install dependencies:

  ```bash
  cd backend
  uv sync
  ```

- The project is configured as a non-package (`[tool.uv] package = false`).

## FastAPI (uvicorn)

- Start the development server:

  ```bash
  cd backend
  uv run uvicorn app.main:app --reload
  ```

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Tests (pytest)

- The test suite (added in Sprint 3) covers the Student module across the repository, service, and API layers.
- Tests run against a dedicated PostgreSQL test database `lms_erp_test` (created automatically on first run). Override the connection string with `TEST_DATABASE_URL`. The dev/seeded database is never modified by tests.

  ```bash
  cd backend
  uv run pytest
  ```

- Dev-only dependencies (`pytest`, `httpx`) are declared in the `dev` dependency group in `backend/pyproject.toml`.

## PostgreSQL

- Local connection string:

  ```
  postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp
  ```

- Apply migrations:

  ```bash
  uv run alembic upgrade head
  ```

- Undo one migration:

  ```bash
  uv run alembic downgrade -1
  ```

- Seed the database:

  ```bash
  uv run python -m scripts.seed
  uv run python -m scripts.seed --reset   # truncate and reseed
  ```

## Environment Variables

Provided via a `.env` file locally (see `backend/.env.example`) and as environment variables on Render.

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Debug behavior (e.g., SQL echo) | `true` / `false` |
| `LOG_LEVEL` | Root logger level | `INFO` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp` |
| `CORS_ORIGINS` | Allowed origins, comma-separated | `http://localhost:3000` |

## Ports

| Service | Port | Notes |
|---------|------|-------|
| FastAPI (uvicorn) | 8000 | default local dev port |
| PostgreSQL | 5432 | local instance |
| Next.js (frontend) | 3000 | future frontend dev server |

## Render Deployment (future)

- **Web Service**: run `uvicorn app.main:app --host 0.0.0.0 --port $PORT` with the `uv` buildpack.
- **Database**: Render PostgreSQL; set `DATABASE_URL` from the Render-provided internal URL.
- **Build**: `uv sync` in the build phase.
- **Migrations**: run `alembic upgrade head` as a startup/release command or manually.
- **Environment**: all variables set in the Render dashboard (never hardcode credentials).

## Docker

- Not yet configured. Docker Compose is planned for Sprint 9.
