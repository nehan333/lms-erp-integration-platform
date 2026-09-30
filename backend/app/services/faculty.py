"""Business logic for the Faculty module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.faculty import Faculty
from app.repositories.faculty import FacultyRepository
from app.schemas.faculty import FacultyCreate, FacultyUpdate


class FacultyNotFoundError(Exception):
    """Raised when a faculty member does not exist."""

    def __init__(self, faculty_id: UUID) -> None:
        super().__init__(f"Faculty {faculty_id} not found")
        self.faculty_id = faculty_id


class DuplicateFacultyError(Exception):
    """Raised when a unique faculty field is already in use."""

    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Faculty with {field} '{value}' already exists")
        self.field = field
        self.value = value


class DepartmentNotFoundError(Exception):
    """Raised when a referenced department does not exist."""

    def __init__(self, department_id: UUID) -> None:
        super().__init__(f"Department {department_id} not found")
        self.department_id = department_id


class FacultyService:
    """Coordinates validation and repository operations for faculty."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = FacultyRepository(db)

    def create(self, payload: FacultyCreate) -> Faculty:
        if not self.repo.department_exists(payload.department_id):
            raise DepartmentNotFoundError(payload.department_id)
        if self.repo.get_by_email(payload.email):
            raise DuplicateFacultyError("email", payload.email)
        if self.repo.get_by_employee_id(payload.employee_id):
            raise DuplicateFacultyError("employee_id", payload.employee_id)

        try:
            faculty = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateFacultyError(
                "email or employee_id", payload.email
            ) from exc
        self.db.refresh(faculty)
        return faculty

    def get(self, faculty_id: UUID) -> Faculty:
        faculty = self.repo.get(faculty_id)
        if faculty is None:
            raise FacultyNotFoundError(faculty_id)
        return faculty

    def list_faculty(
        self,
        *,
        limit: int,
        offset: int,
        department_id: UUID | None = None,
        status: bool | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[Faculty], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            department_id=department_id,
            status=status,
            search=search,
        )

    def update(self, faculty_id: UUID, payload: FacultyUpdate) -> Faculty:
        faculty = self.get(faculty_id)
        data = payload.model_dump(exclude_unset=True)

        if "department_id" in data:
            if not self.repo.department_exists(data["department_id"]):
                raise DepartmentNotFoundError(data["department_id"])
        if "email" in data:
            existing = self.repo.get_by_email(data["email"])
            if existing is not None and existing.id != faculty.id:
                raise DuplicateFacultyError("email", data["email"])
        if "employee_id" in data:
            existing = self.repo.get_by_employee_id(data["employee_id"])
            if existing is not None and existing.id != faculty.id:
                raise DuplicateFacultyError("employee_id", data["employee_id"])

        if not data:
            return faculty

        try:
            faculty = self.repo.update(faculty, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateFacultyError(
                "email or employee_id", data.get("email", "")
            ) from exc
        self.db.refresh(faculty)
        return faculty

    def delete(self, faculty_id: UUID) -> None:
        faculty = self.get(faculty_id)
        self.repo.soft_delete(faculty)
        self.db.commit()