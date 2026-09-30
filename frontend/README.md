# LMS-ERP Frontend

Next.js (JavaScript + CSS Modules, App Router) single-page app that consumes the FastAPI ERP backend.

## Stack

- Next.js 15 (App Router)
- React 19
- JavaScript (no TypeScript)
- CSS Modules (global stylesheet for now)

## Getting Started

```bash
# 1. Start the backend (from the repo root `backend/`)
uv run uvicorn app.main:app --reload

# 2. Configure the API base URL (default http://localhost:8000)
cp .env.local.example .env.local

# 3. Run the frontend dev server
npm install
npm run dev
```

Open http://localhost:3000.

## Environment Variables

| Variable              | Description                                     | Default                  |
| --------------------- | ----------------------------------------------- | ------------------------ |
| `NEXT_PUBLIC_API_URL` | Base URL of the FastAPI backend                 | `http://localhost:8000`  |

## Scripts

| Command        | Description                                 |
| -------------- | ------------------------------------------- |
| `npm run dev`  | Start the Next.js dev server (port 3000)    |
| `npm run build`| Create a production build                    |
| `npm start`    | Start the production server                  |
| `npm test`     | Run frontend tests (Node built-in runner)   |

## Project Structure

```
app/                  # App Router pages
  page.js             # Dashboard
  reports/page.js     # Reports
  students/           # Students CRUD (list, new, edit)
  departments/        # Departments CRUD
  faculty/            # Faculty CRUD
  courses/            # Courses CRUD
  sync/page.js        # Moodle sync (status + trigger)
components/
  Nav.js              # Top navigation
  EntityForm.js       # Reusable create/edit form
  DeleteButton.js     # Reusable delete (with confirm)
  SyncPanel.js        # Moodle status + sync controls
lib/
  api.js              # API client (get/create/update/remove)
tests/
  api.test.mjs        # API client tests (node:test)
```

## Architecture

- **Server components** fetch read data directly from the API (`lib/api.js`) with `cache: "no-store"`, so pages always show fresh data.
- **Client components** (`EntityForm`, `DeleteButton`, `SyncPanel`) handle mutations and revalidate the page via `router.refresh()`.
- The ERP API is the single source of truth; the frontend has no local data store.

## Wish paths (to do)

- Enrollments / attendance / grades UI (Sprint 8 covered students, departments, faculty, courses).
- Authentication/authorization (future).