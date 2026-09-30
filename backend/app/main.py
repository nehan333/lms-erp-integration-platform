"""Application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attendance import router as attendance_router
from app.api.courses import router as courses_router
from app.api.dashboard import router as dashboard_router
from app.api.departments import router as departments_router
from app.api.enrollments import router as enrollments_router
from app.api.faculty import router as faculty_router
from app.api.grades import router as grades_router
from app.api.health import router as health_router
from app.api.moodle import router as moodle_router
from app.api.reports import router as reports_router
from app.api.students import router as students_router
from app.api.sync_logs import router as sync_logs_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown resources."""
    yield
    engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials="*" not in settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(students_router)
app.include_router(departments_router)
app.include_router(faculty_router)
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(attendance_router)
app.include_router(grades_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(sync_logs_router)
app.include_router(moodle_router)
