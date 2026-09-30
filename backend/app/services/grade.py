"""Business logic for the Grade module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.grade import Grade
from app.repositories.grade import GradeRepository
from app.schemas.grade import GradeCreate, GradeUpdate


class GradeNotFoundError(Exception):
    """Raised when a grade record does not exist."""

    def __init__(self, grade_id: UUID) -> None:
        super().__init__(f"Grade {grade_id} not found")
        self.grade_id = grade_id


class DuplicateGradeError(Exception):
    """Raised when a grade for the same student/course pair already exists."""

    def __init__(self, student_id: UUID, course_id: UUID) -> None:
        super().__init__(
            f"Grade for student {student_id} in course {course_id} already exists"
        )
        self.student_id = student_id
        self.course_id = course_id


class StudentNotFoundError(Exception):
    """Raised when a referenced student does not exist."""

    def __init__(self, student_id: UUID) -> None:
        super().__init__(f"Student {student_id} not found")
        self.student_id = student_id


class CourseNotFoundError(Exception):
    """Raised when a referenced course does not exist."""

    def __init__(self, course_id: UUID) -> None:
        super().__init__(f"Course {course_id} not found")
        self.course_id = course_id


class GradeService:
    """Coordinates validation and repository operations for grades."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = GradeRepository(db)

    def create(self, payload: GradeCreate) -> Grade:
        if not self.repo.student_exists(payload.student_id):
            raise StudentNotFoundError(payload.student_id)
        if not self.repo.course_exists(payload.course_id):
            raise CourseNotFoundError(payload.course_id)
        if self.repo.get_by_unique(payload.student_id, payload.course_id):
            raise DuplicateGradeError(payload.student_id, payload.course_id)

        try:
            grade = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateGradeError(payload.student_id, payload.course_id) from exc
        self.db.refresh(grade)
        return grade

    def get(self, grade_id: UUID) -> Grade:
        grade = self.repo.get(grade_id)
        if grade is None:
            raise GradeNotFoundError(grade_id)
        return grade

    def list_grades(
        self,
        *,
        limit: int,
        offset: int,
        student_id: UUID | None = None,
        course_id: UUID | None = None,
    ) -> tuple[Sequence[Grade], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            student_id=student_id,
            course_id=course_id,
        )

    def update(self, grade_id: UUID, payload: GradeUpdate) -> Grade:
        grade = self.get(grade_id)
        data = payload.model_dump(exclude_unset=True)

        if not data:
            return grade

        try:
            grade = self.repo.update(grade, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateGradeError(grade.student_id, grade.course_id) from exc
        self.db.refresh(grade)
        return grade

    def delete(self, grade_id: UUID) -> None:
        grade = self.get(grade_id)
        self.repo.delete(grade)
        self.db.commit()