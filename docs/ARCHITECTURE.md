# Architecture

## Overview

The LMS–ERP Integration Platform connects a **College ERP** with the **Moodle LMS**.

- The **ERP is the source of truth** for academic data (students, faculty, departments, courses, enrollments, attendance, grades).
- **Moodle is only the Learning Management System** (course materials, assignments, quizzes, learning).
- A **Synchronization Engine** keeps Moodle in sync with the ERP in a future sprint.

## Layered Architecture

```
┌───────────────────────────────┐
│   Presentation (Next.js)      │
└──────────────┬────────────────┘
               │ REST API (JSON)
┌──────────────▼────────────────┐
│   Backend API (FastAPI)       │
│   Router → Service → Repository
└──────────────┬────────────────┘
               │ SQLAlchemy ORM
┌──────────────▼────────────────┐
│   PostgreSQL (ERP Database)   │
└──────────────┬────────────────┘
               │ (future) Sync Engine
┌──────────────▼────────────────┐
│   Moodle REST Web Services    │
└──────────────┬────────────────┘
               │
┌──────────────▼────────────────┐
│   Moodle LMS                  │
└───────────────────────────────┘
```

## Request Flow

1. The user interacts with the **Next.js** frontend.
2. The frontend sends a **REST request** (JSON) to the FastAPI backend.
3. FastAPI routes the request to the matching **API router**.
4. The router calls the **service layer** (business logic).
5. The service uses the **repository layer** (data access).
6. The repository interacts with **PostgreSQL through SQLAlchemy ORM**.
7. The response is validated with **Pydantic schemas** and returned to the client.

```
Client → Next.js → REST → FastAPI → Router → Service → Repository → SQLAlchemy → PostgreSQL
```

## Synchronization Flow (future sprint)

1. Academic data changes inside the ERP (e.g., a student is created).
2. The **Synchronization Engine** detects the change.
3. It maps the ERP record to the equivalent Moodle entity.
4. It calls the **Moodle REST API** using a Moodle web service token.
5. It records the result in the `sync_logs` table.

```
ERP change → Sync Engine → Moodle REST API → Moodle LMS → sync_logs
```

## Folder Responsibilities

| Folder | Responsibility |
|--------|----------------|
| `app/api/` | HTTP routers. Request/response handling. |
| `app/core/` | Cross-cutting concerns: settings (`config.py`) and logging (`logging.py`). |
| `app/db/` | Database plumbing: engine, session factory, declarative base. |
| `app/models/` | SQLAlchemy 2.0 ORM models (Sprint 2). |
| `app/schemas/` | Pydantic v2 request/response schemas (future). |
| `app/services/` | Business logic (future). |
| `app/repositories/` | Data-access layer (future). |
| `app/middlewares/` | Custom ASGI/Starlette middleware (future). |
| `app/integrations/moodle/` | Moodle REST Web Services client (future). |
| `app/utils/` | Shared helpers (future). |
| `scripts/` | Utility scripts (database seed). |
| `alembic/` | Database migrations. |

## Layer Conventions

- **API → Service → Repository → Database**. Layers depend downward.
- Repositories encapsulate all SQLAlchemy queries.
- Services contain business logic and are framework-agnostic.
- Routers stay thin and delegate to services.

## Future Moodle Integration

- Use **Moodle REST Web Services** with token-based authentication.
- Map ERP entities to Moodle equivalents:

| ERP | Moodle |
|-----|--------|
| Student / Faculty | Moodle user |
| Department | Moodle course category |
| Course | Moodle course |
| Enrollment | Moodle enrolment |
| Grade / Attendance | Moodle grade/attendance plug-in data |

- Every operation writes a `sync_logs` entry.
- Integration is implemented in Sprint 7 and is out of scope for earlier sprints.
