"""Business logic for the Student module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.student import Student
from app.repositories.student import StudentRepository
from app.schemas.student import (
    BulkStudentImportRequest,
    BulkStudentImportResult,
    BulkStudentRowError,
    StudentCreate,
    StudentUpdate,
)

REQUIRED_CSV_COLUMNS = ("roll_number", "name", "email", "semester", "section")
OPTIONAL_CSV_COLUMNS = ("phone",)
MAX_BULK_ROWS = 5000


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


class BulkImportFormatError(Exception):
    """Raised when the uploaded CSV is structurally unusable."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


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

    # ------------------------------------------------------------------ #
    # Bulk CSV import
    # ------------------------------------------------------------------ #

    def _parse_rows(
        self, payload: BulkStudentImportRequest
    ) -> list[tuple[int, StudentCreate | BulkStudentRowError]]:
        """Parse and validate the CSV body into per-row outcomes.

        Returns ``(row_number, StudentCreate)`` for usable rows and
        ``(row_number, BulkStudentRowError)`` for rejected ones. Row numbers
        are 1-based and include the header line, matching what a user sees in
        their editor. Raises ``BulkImportFormatError`` when the CSV itself is
        unusable and ``DepartmentNotFoundError`` for an unknown department.
        """
        if not self.repo.department_exists(payload.department_id):
            raise DepartmentNotFoundError(payload.department_id)

        text = payload.csv.lstrip("\ufeff")  # strip UTF-8 BOM
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise BulkImportFormatError("CSV is empty")

        headers = {
            (name or "").strip().lower(): name for name in reader.fieldnames
        }
        missing = [c for c in REQUIRED_CSV_COLUMNS if c not in headers]
        if missing:
            raise BulkImportFormatError(
                "CSV is missing required column(s): " + ", ".join(missing)
            )

        parsed: list[tuple[int, StudentCreate | BulkStudentRowError]] = []
        seen_rolls: set[str] = set()
        seen_emails: set[str] = set()
        for offset, raw in enumerate(reader):
            row_number = offset + 2  # 1-based, header is row 1
            if len(parsed) >= MAX_BULK_ROWS:
                raise BulkImportFormatError(
                    f"CSV exceeds the limit of {MAX_BULK_ROWS} rows"
                )

            def cell(column: str) -> str:
                key = headers.get(column)
                if key is None:
                    return ""
                return str(raw.get(key) or "").strip()

            values = {column: cell(column) for column in REQUIRED_CSV_COLUMNS}
            values["phone"] = cell("phone") or None

            def reject(message: str) -> None:
                parsed.append(
                    (row_number, BulkStudentRowError(row=row_number, error=message))
                )

            missing_values = [
                column for column, value in values.items()
                if column != "phone" and not value
            ]
            if missing_values:
                reject("Missing value(s): " + ", ".join(missing_values))
                continue

            try:
                semester = int(values["semester"])
            except ValueError:
                reject(
                    f"semester must be an integer, got '{values['semester']}'"
                )
                continue

            try:
                student = StudentCreate(
                    roll_number=values["roll_number"],
                    name=values["name"],
                    email=values["email"],
                    phone=values["phone"],
                    department_id=payload.department_id,
                    semester=semester,
                    section=values["section"],
                )
            except Exception as exc:  # pydantic validation
                reject(str(exc))
                continue

            roll_key = student.roll_number.lower()
            email_key = student.email.lower()
            if roll_key in seen_rolls:
                reject(
                    f"Duplicate roll_number '{student.roll_number}' in this file"
                )
                continue
            if email_key in seen_emails:
                reject(f"Duplicate email '{student.email}' in this file")
                continue

            if self.repo.get_by_roll_number(student.roll_number):
                reject(
                    f"roll_number '{student.roll_number}' already exists (skipped)"
                )
                continue
            if self.repo.get_by_email(student.email):
                reject(f"email '{student.email}' already exists (skipped)")
                continue

            seen_rolls.add(roll_key)
            seen_emails.add(email_key)
            parsed.append((row_number, student))

        if not parsed:
            raise BulkImportFormatError("CSV contains no data rows")
        return parsed

    def bulk_import(
        self, payload: BulkStudentImportRequest
    ) -> tuple[BulkStudentImportResult, list[UUID]]:
        """Import CSV rows; returns the result plus created student ids.

        Each insert runs in its own savepoint so one bad row never poisons
        the batch. With ``dry_run`` everything is validated and rolled back.
        """
        parsed = self._parse_rows(payload)

        errors: list[BulkStudentRowError] = []
        created_ids: list[UUID] = []
        failed = 0
        skipped = 0

        for row_number, entry in parsed:
            if isinstance(entry, BulkStudentRowError):
                # Pre-existing rows are "skipped"; malformed rows are "failed".
                if "already exists" in entry.error:
                    skipped += 1
                else:
                    failed += 1
                errors.append(entry)
                continue
            try:
                with self.db.begin_nested():
                    student = self.repo.create(entry.model_dump())
                created_ids.append(student.id)
            except IntegrityError:
                failed += 1
                errors.append(BulkStudentRowError(
                    row=row_number,
                    error="Database rejected the row (unique constraint)",
                ))

        total = len(parsed)
        created = len(created_ids)
        if payload.dry_run:
            self.db.rollback()
            created = 0
            created_ids = []
        else:
            self.db.commit()

        return (
            BulkStudentImportResult(
                total=total,
                created=created,
                skipped=skipped,
                failed=failed,
                dry_run=payload.dry_run,
                errors=errors,
            ),
            created_ids,
        )
