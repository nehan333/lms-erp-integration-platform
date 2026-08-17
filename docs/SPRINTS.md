# Sprint Roadmap

This document is the roadmap from **Sprint 1 until project completion**.

- The **active sprint** is tracked in `docs/SPRINT.md`.
- Do not implement any sprint until it is explicitly assigned.

---

## Sprint 1 - Backend Foundation ✅

### Goal

Establish a production-ready backend foundation.

### Completed

- Project structure
- FastAPI
- SQLAlchemy
- Alembic
- Configuration
- Logging
- Environment Variables
- Health Endpoint
- Project Documentation

Status: Completed

---

## Sprint 2 - Database Design & Foundation ✅

### Goal

Design and implement the ERP database.

### Tasks

- Finalize DATABASE.md
- Design ER Diagram
- Configure PostgreSQL
- Generate SQLAlchemy Models
- Generate Alembic Migration
- Run Migration
- Create Seed Script
- Insert Sample Data
- Verify Relationships
- Commit Changes

Deliverable:

Working PostgreSQL database containing sample academic data.

Status: Completed

---

## Sprint 3 - Student Management Module ✅

### Goal

Implement complete Student Management.

### Completed

- Pydantic v2 schemas (`StudentCreate`, `StudentUpdate`, `StudentRead`, `StudentList`)
- `StudentRepository` (data access, filtering, pagination)
- `StudentService` (business logic, validation, error handling)
- Student API router (`GET /students`, `POST /students`, `GET /students/{id}`, `PUT /students/{id}`, `DELETE /students/{id}`)
- Swagger/OpenAPI documentation for student endpoints
- pytest-based test suite (repository, service, API layers)

Deliverable:

Complete Student Module.

Status: Completed (see `docs/CHANGELOG.md`).

---

## Sprint 4 - Faculty & Department Modules ⏳

### Goal

Faculty and Department Management.

### Tasks

- Department CRUD
- Faculty CRUD
- Relationships
- Testing

---

## Sprint 5 - Course & Enrollment Modules

### Goal

Academic Structure.

### Tasks

- Course CRUD
- Enrollment CRUD
- Attendance
- Grades

---

## Sprint 6 - Dashboard & Reports

### Goal

ERP Dashboard.

### Tasks

- Dashboard
- Statistics
- Reports
- Sync Logs

---

## Sprint 7 - Moodle Integration

### Goal

Integrate ERP with Moodle.

### Tasks

- Moodle Authentication
- Create Moodle Users
- Create Moodle Courses
- Student Enrollment
- Grade Synchronization
- Attendance Synchronization

---

## Sprint 8 - Frontend Integration

### Goal

Connect Next.js with FastAPI.

### Tasks

- API Integration
- Forms
- Dashboard UI
- CRUD Pages

---

## Sprint 9 - Testing & Deployment

### Goal

Prepare production release.

### Tasks

- Testing
- Bug Fixes
- Docker Compose
- Render Deployment
- Documentation
- Final Presentation
