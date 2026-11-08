# LMS–ERP Integration Platform

A web-based College Enterprise Resource Planning (ERP) platform integrated with Moodle Learning Management System (LMS), designed to automate the synchronization of academic information between the two systems.

---

## 1. Project Overview

The **LMS–ERP Integration Platform** connects a college ERP system with Moodle LMS through Moodle REST Web Services.

The ERP acts as the primary source of academic information. Administrative users can manage students, faculty, departments, courses, enrollments, attendance, and grades through the ERP platform. Relevant academic information can then be synchronized with Moodle, reducing duplicate data entry and manual administrative work.

The platform provides a centralized interface for managing academic records and monitoring synchronization operations between the ERP and Moodle.

## 2. Key Features

### ERP Management
- **Student Management:** Create, view, update, and manage student records.
- **Faculty Management:** Maintain faculty information.
- **Department Management:** Manage academic departments.
- **Course Management:** Create and maintain course information.
- **Enrollment Management:** Manage student course enrollments.
- **Bulk Student Import:** Import student records using CSV files, with validation and preview before execution.
- **Bulk Enrollment:** Preview and process enrollments for selected student groups and courses.

### Academic Management
- Attendance record management.
- Grade management.
- Student attendance summaries and academic reports.
- Dashboard statistics and academic information.

### Moodle Integration
- Synchronization of ERP students with Moodle users.
- Synchronization of ERP courses with Moodle courses.
- Synchronization of student enrollments.
- Grade synchronization.
- Attendance session and attendance record synchronization.
- Synchronization logs for monitoring operations and failures.

### Synchronization Reliability
- Idempotent synchronization to avoid creating duplicate Moodle records.
- Existing Moodle records are checked before creating new records.
- Synchronization results and errors are recorded.
- Attendance synchronization includes protection against concurrent execution and duplicate processing.

## 3. System Architecture

The platform consists of three main components:

1. **Frontend:** Provides the administrative interface.
2. **Backend:** Handles application logic, database operations, and Moodle integration.
3. **Database and LMS:** PostgreSQL stores ERP information, while Moodle provides the learning management functionality.

### Architecture Overview

```text
                  Administrator
                        |
                        v
              Next.js Frontend
                 (React 19)
                        |
                   HTTP REST
                        |
                        v
                FastAPI Backend
                        |
              ---------------------
              |                   |
              v                   v
       PostgreSQL Database   Moodle REST API
              |                   |
              v                   v
        ERP Academic Data     Moodle LMS
```

### Backend Request Flow

The backend follows a layered architecture:

```text
API Router
    |
    v
Service Layer
    |
    v
Repository Layer
    |
    v
PostgreSQL Database
```

Moodle integration is handled through a dedicated integration layer that communicates with Moodle's REST Web Services.

## 4. Technology Stack

| Component | Technology |
|---|---|
| Frontend Framework | Next.js 15 |
| UI Library | React 19 |
| Frontend Language | JavaScript |
| Styling | CSS |
| Backend Framework | FastAPI |
| Backend Language | Python 3.13+ |
| Data Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 |
| Database Migrations | Alembic |
| Database | PostgreSQL |
| Python Package Manager | uv |
| LMS | Moodle 5.0.10 |
| LMS Communication | Moodle REST Web Services |
| Local LMS Environment | Docker and Docker Compose |
| Backend Testing | pytest |
| Frontend Testing | Node.js built-in test runner |

## 5. Project Structure

```text
lms-erp-integration-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/             # REST API endpoints
│   │   ├── core/            # Application configuration and logging
│   │   ├── db/              # Database connection and session
│   │   ├── integrations/
│   │   │   └── moodle/      # Moodle REST API integration
│   │   ├── middlewares/     # Application middleware
│   │   ├── models/          # SQLAlchemy database models
│   │   ├── repositories/    # Database access layer
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI application entry point
│   │
│   ├── alembic/             # Database migration scripts
│   ├── scripts/             # Utility and database seed scripts
│   ├── tests/               # Backend test suite
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/
│   ├── app/                 # Next.js application pages
│   ├── components/          # Reusable UI components
│   ├── lib/                 # API client and utilities
│   ├── tests/               # Frontend tests
│   └── package.json
│
├── moodle-test/
│   ├── moodle-docker/       # Local Moodle Docker configuration
│   └── README.md
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── ERD.md
│   ├── INFRASTRUCTURE.md
│   ├── PROJECT.md
│   └── ...
│
├── .gitignore
├── LICENSE
└── README.md
```

The Moodle source directory is intentionally excluded from Git and must be obtained separately when setting up the local Moodle environment.

## 6. Prerequisites

Install the following software before setting up the project:

- Git
- Python 3.13 or newer
- uv
- Node.js 22 or newer
- npm
- PostgreSQL
- Docker Engine
- Docker Compose

Verify the installations:

```bash
git --version
python3 --version
uv --version
node --version
npm --version
psql --version
docker --version
docker compose version
```

## 7. Installation and Setup

### 7.1 Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd lms-erp-integration-platform
```

Replace `<REPOSITORY_URL>` with the Git repository URL.

### 7.2 Configure PostgreSQL

Install and start PostgreSQL if it is not already installed.

On Ubuntu/Linux Mint:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

Create the application database and user.

Open the PostgreSQL shell:

```bash
sudo -u postgres psql
```

Execute:

```sql
CREATE USER postgres WITH PASSWORD 'postgres';
CREATE DATABASE lms_erp OWNER postgres;
```

If the `postgres` role already exists, configure its password instead of creating it again.

Exit:

```sql
\q
```

The default development database URL is:

```text
postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp
```

Change the credentials and database URL according to your local PostgreSQL configuration.

### 7.3 Configure the Backend

Navigate to the backend directory:

```bash
cd backend
```

Create the environment file:

```bash
cp .env.example .env
```

Install dependencies:

```bash
uv sync
```

Edit `.env` and configure the database URL and CORS origin.

Example:

```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/lms_erp

CORS_ORIGINS=http://localhost:3001
```

Moodle integration variables can be configured after setting up Moodle.

### 7.4 Run Database Migrations

From the `backend/` directory:

```bash
uv run alembic upgrade head
```

This creates the database schema required by the application.

### 7.5 Populate Sample Data (Optional)

To populate the database with sample academic records:

```bash
uv run python -m scripts.seed
```

The seed script creates sample departments, faculty, students, courses, enrollments, attendance records, and grades.

**Warning:** The `--reset` option clears existing seeded application data before reseeding. Do not use it on a database containing records you want to preserve.

### 7.6 Configure the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Create the environment file:

```bash
cp .env.local.example .env.local
```

The default configuration is:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Install dependencies:

```bash
npm ci
```

## 8. Moodle Setup

The project uses a local Moodle environment through Docker.

The Docker configuration is available under:

```text
moodle-test/moodle-docker/
```

The Moodle source code itself is not included in the repository. Obtain the compatible Moodle source separately and place it at:

```text
moodle-test/moodle/
```

Configure the Moodle Docker environment.

Navigate to:

```bash
cd moodle-test/moodle-docker
```

Set the required environment variables:

```bash
export MOODLE_DOCKER_WWWROOT=../moodle
export MOODLE_DOCKER_DB=pgsql
export MOODLE_DOCKER_WEB_PORT=8080
export MOODLE_DOCKER_DB_PASSWORD='your-local-password'
```

Start Moodle:

```bash
bin/moodle-docker-compose up -d
```

Open Moodle:

```text
http://localhost:8080
```

Complete the initial Moodle installation through the browser if this is a new environment.

### Moodle Web Services Configuration

Moodle integration requires:

1. Enable Moodle Web Services.
2. Enable REST protocol.
3. Create or configure an external service.
4. Enable the required Moodle functions for the service.
5. Generate a web-service token for the integration account.
6. Install and configure the Moodle Attendance plugin for attendance synchronization.
7. Enable the required `mod_attendance_*` functions for the external service.

Configure the following variables in `backend/.env`:

```env
MOODLE_BASE_URL=http://localhost:8080
MOODLE_WSTOKEN=your_moodle_webservice_token
MOODLE_TIMEOUT_SECONDS=30
MOODLE_DEFAULT_CATEGORY_ID=1
MOODLE_STUDENT_ROLE_ID=5
MOODLE_DEFAULT_PASSWORD=your_local_default_password
MOODLE_SITE_TIMEZONE=Asia/Kolkata
```

The Moodle token and password must never be committed to Git.

`MOODLE_SITE_TIMEZONE` must match the timezone configured on the Moodle site.

For additional Moodle environment instructions, refer to [moodle-test/README.md](moodle-test/README.md).

## 9. Running the Application

The application consists of three independently running services.

### Terminal 1: Start the Backend

```bash
cd lms-erp-integration-platform/backend

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

API documentation:

```text
http://localhost:8000/docs
```

### Terminal 2: Start the Frontend

```bash
cd lms-erp-integration-platform/frontend

npm run dev -- --port 3001
```

Frontend:

```text
http://localhost:3001
```

### Terminal 3: Start Moodle

```bash
cd lms-erp-integration-platform/moodle-test/moodle-docker

export MOODLE_DOCKER_WWWROOT=../moodle
export MOODLE_DOCKER_DB=pgsql
export MOODLE_DOCKER_WEB_PORT=8080
export MOODLE_DOCKER_DB_PASSWORD='your-local-password'

bin/moodle-docker-compose up -d
```

Moodle:

```text
http://localhost:8080
```

Once all services are running, open the frontend in your browser.

## 10. Stopping the Services

Stop the frontend and backend using `Ctrl+C` in their respective terminals.

To stop Moodle:

```bash
cd moodle-test/moodle-docker
bin/moodle-docker-compose down
```

This stops the Moodle containers but preserves the persistent database volume.

Do not delete the Moodle database volume when stopping the environment.

## 11. Testing

### Backend Tests

Navigate to the backend directory:

```bash
cd backend
```

Run the complete test suite:

```bash
uv run pytest
```

Run a specific test file:

```bash
uv run pytest tests/test_moodle_service.py -q
```

The backend test suite uses a dedicated PostgreSQL test database. The development database should not be used as the test database.

Set `TEST_DATABASE_URL` if a separate test database configuration is required.

### Frontend Tests

Navigate to the frontend directory:

```bash
cd frontend
```

Run:

```bash
npm test
```

### Production Build

To verify the frontend production build:

```bash
npm run build
```

## 12. API Documentation

The backend exposes REST API endpoints through FastAPI.

Once the backend is running, interactive API documentation is available at:

```text
http://localhost:8000/docs
```

The OpenAPI specification is available at:

```text
http://localhost:8000/openapi.json
```

Refer to [docs/API.md](docs/API.md) for additional API documentation.

## 13. Synchronization Workflow

The ERP is the primary source of academic information.

The integration layer communicates with Moodle using its REST Web Services API.

The synchronization process generally follows these steps:

1. Retrieve the relevant academic record from the ERP database.
2. Check whether the corresponding record already exists in Moodle.
3. Create a Moodle record if one does not exist, or reuse the existing record.
4. Map ERP identifiers to Moodle identifiers.
5. Synchronize the relevant relationships or academic information.
6. Record the synchronization result in the ERP synchronization logs.

### Synchronization Mapping

| ERP Entity | Moodle Entity |
|---|---|
| Student | Moodle User |
| Course | Moodle Course |
| Enrollment | Course Enrollment |
| Grade | Moodle Grade |
| Attendance | Moodle Attendance Session and Records |

The synchronization process uses stable identifiers and checks existing records to reduce duplicate creation.

Attendance synchronization additionally depends on the Moodle Attendance plugin and its enabled web-service functions.

## 14. Database Overview

The ERP database contains the following primary application tables:

| Table | Purpose |
|---|---|
| `students` | Student information |
| `departments` | Department records |
| `faculty` | Faculty information |
| `courses` | Course information |
| `enrollments` | Student-course relationships |
| `attendance` | Student attendance records |
| `grades` | Academic grade records |
| `sync_logs` | Moodle synchronization history |

Alembic maintains its own `alembic_version` table to track database migrations.

Refer to:

- [Database Documentation](docs/DATABASE.md)
- [Entity Relationship Diagram](docs/ERD.md)

## 15. Environment Variables

### Backend

| Variable | Description |
|---|---|
| `ENVIRONMENT` | Application environment |
| `DEBUG` | Enable or disable debug mode |
| `LOG_LEVEL` | Application logging level |
| `DATABASE_URL` | PostgreSQL connection URL |
| `CORS_ORIGINS` | Allowed frontend origins |
| `MOODLE_BASE_URL` | Moodle site URL |
| `MOODLE_WSTOKEN` | Moodle Web Services token |
| `MOODLE_DEFAULT_PASSWORD` | Default password used when creating Moodle users |
| `MOODLE_TIMEOUT_SECONDS` | Moodle API request timeout |
| `MOODLE_DEFAULT_CATEGORY_ID` | Default Moodle course category |
| `MOODLE_STUDENT_ROLE_ID` | Moodle student role ID |
| `MOODLE_SITE_TIMEZONE` | Moodle site's timezone |

### Frontend

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend |

Keep actual environment files and credentials private. Only example configuration files should be committed.

## 16. Additional Documentation

The `docs/` directory contains supporting project documentation.

| Document | Description |
|---|---|
| `PROJECT.md` | Project scope and overview |
| `ARCHITECTURE.md` | System architecture |
| `API.md` | API documentation |
| `DATABASE.md` | Database design |
| `ERD.md` | Entity relationship diagram |
| `INFRASTRUCTURE.md` | Infrastructure and deployment information |
| `DECISIONS.md` | Technical decisions |
| `CHANGELOG.md` | Project change history |
| `CONTRIBUTING.md` | Contribution guidelines |
| `HANDOVER.md` | Project handover information |

## 17. Security Considerations

- Do not commit `.env` or `.env.local` files.
- Do not expose Moodle Web Services tokens.
- Use environment variables for credentials and sensitive configuration.
- Configure appropriate CORS origins for the deployment environment.
- Use a dedicated PostgreSQL database for automated tests.
- Do not expose development credentials in production.
- Configure Moodle web services with only the permissions required by the integration.

## 18. License

This project is distributed under the license included in the repository. Refer to [LICENSE](LICENSE) for details.

---

**LMS–ERP Integration Platform**  
College ERP and Moodle LMS Integration Project.
