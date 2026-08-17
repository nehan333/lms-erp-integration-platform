"""Business logic for the Student module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.student import Student
from app.repositories.student import StudentRepository
from app.schemas.student import StudentCreate, StudentUpdate


class StudentNotFoundError(Exception):
    """Raised when a student does not exist."""

    def __init__(self, student_id: UUID) -> None:
        super().__init__(f"Student {student_id} not found")
        self.student_id = student_id


class DuplicateStudentError(Exception):
    """Raised when a unique student field is already in use."""

    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Student with {field} '{value}' already exists")
        self.field = field
        self.value = value


class DepartmentNotFoundError(Exception):
    """Raised when a referenced department does not exist."""

    def __init__(self, department_id: UUID) -> None:
        super().__init__(f"Department {department_id} not found")
        self.department_id = department_id


class StudentService:
    """Coordinates validation and repository operations for students."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = StudentRepository(db)

    def create(self, payload: StudentCreate) -> Student:
        if not self.repo.department_exists(payload.department_id):
            raise DepartmentNotFoundError(payload.department_id)
        if self.repo.get_by_email(payload.email):
            raise DuplicateStudentError("email", payload.email)
        if self.repo.get_by_roll_number(payload.roll_number):
            raise DuplicateStudentError("roll_number", payload.roll_number)

        try:
            student = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateStudentError(
                "email or roll_number", payload.email
            ) from exc
        self.db.refresh(student)
        return student

    def get(self, student_id: UUID) -> Student:
        student = self.repo.get(student_id)
        if student is None:
            raise StudentNotFoundError(student_id)
        return student

    def list_students(
        self,
        *,
        limit: int,
        offset: int,
        department_id: UUID | None = None,
        semester: int | None = None,
        status: bool | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[Student], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            department_id=department_id,
            semester=semester,
            status=status,
            search=search,
        )

    def update(self, student_id: UUID, payload: StudentUpdate) -> Student:
        student = self.get(student_id)
        data = payload.model_dump(exclude_unset=True)

        if "department_id" in data:
            if not self.repo.department_exists(data["department_id"]):
                raise DepartmentNotFoundError(data["department_id"])
        if "email" in data:
            existing = self.repo.get_by_email(data["email"])
            if existing is not None and existing.id != student.id:
                raise DuplicateStudentError("email", data["email"])
        if "roll_number" in data:
            existing = self.repo.get_by_roll_number(data["roll_number"])
            if existing is not None and existing.id != student.id:
                raise DuplicateStudentError("roll_number", data["roll_number"])

        if not data:
            return student

        try:
            student = self.repo.update(student, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateStudentError(
                "email or roll_number", data.get("email", "")
            ) from exc
        self.db.refresh(student)
        return student

    def delete(self, student_id: UUID) -> None:
        student = self.get(student_id)
        self.repo.soft_delete(student)
        self.db.commit()
