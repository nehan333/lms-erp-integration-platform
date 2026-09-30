"""Business logic for the Department module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentNotFoundError(Exception):
    """Raised when a department does not exist."""

    def __init__(self, department_id: UUID) -> None:
        super().__init__(f"Department {department_id} not found")
        self.department_id = department_id


class DuplicateDepartmentError(Exception):
    """Raised when a unique department field is already in use."""

    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Department with {field} '{value}' already exists")
        self.field = field
        self.value = value


class DepartmentInUseError(Exception):
    """Raised when a department cannot be deleted because it is in use."""

    def __init__(self, department_id: UUID) -> None:
        super().__init__(
            f"Department {department_id} cannot be deleted; it has faculty, "
            "students, or courses assigned to it"
        )
        self.department_id = department_id


class DepartmentService:
    """Coordinates validation and repository operations for departments."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DepartmentRepository(db)

    def create(self, payload: DepartmentCreate) -> Department:
        if self.repo.get_by_code(payload.department_code):
            raise DuplicateDepartmentError("code", payload.department_code)
        if self.repo.get_by_name(payload.department_name):
            raise DuplicateDepartmentError("name", payload.department_name)

        try:
            department = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateDepartmentError(
                "code or name", payload.department_name
            ) from exc
        self.db.refresh(department)
        return department

    def get(self, department_id: UUID) -> Department:
        department = self.repo.get(department_id)
        if department is None:
            raise DepartmentNotFoundError(department_id)
        return department

    def list_departments(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
    ) -> tuple[Sequence[Department], int]:
        return self.repo.list(limit=limit, offset=offset, search=search)

    def update(self, department_id: UUID, payload: DepartmentUpdate) -> Department:
        department = self.get(department_id)
        data = payload.model_dump(exclude_unset=True)

        if "department_code" in data:
            existing = self.repo.get_by_code(data["department_code"])
            if existing is not None and existing.id != department.id:
                raise DuplicateDepartmentError("code", data["department_code"])
        if "department_name" in data:
            existing = self.repo.get_by_name(data["department_name"])
            if existing is not None and existing.id != department.id:
                raise DuplicateDepartmentError("name", data["department_name"])

        if not data:
            return department

        try:
            department = self.repo.update(department, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateDepartmentError(
                "code or name", data.get("department_name", "")
            ) from exc
        self.db.refresh(department)
        return department

    def delete(self, department_id: UUID) -> None:
        department = self.get(department_id)
        if self.repo.has_children(department_id):
            raise DepartmentInUseError(department_id)
        try:
            self.repo.delete(department)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DepartmentInUseError(department_id) from exc