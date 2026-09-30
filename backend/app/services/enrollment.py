"""Business logic for the Enrollment module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate


class EnrollmentNotFoundError(Exception):
    """Raised when an enrollment does not exist."""

    def __init__(self, enrollment_id: UUID) -> None:
        super().__init__(f"Enrollment {enrollment_id} not found")
        self.enrollment_id = enrollment_id


class DuplicateEnrollmentError(Exception):
    """Raised when the unique student/course/year/semester combination already exists."""

    def __init__(self, student_id: UUID, course_id: UUID) -> None:
        super().__init__(
            f"Enrollment for student {student_id} in course {course_id} "
            "already exists for this academic year and semester"
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


class EnrollmentService:
    """Coordinates validation and repository operations for enrollments."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EnrollmentRepository(db)

    def create(self, payload: EnrollmentCreate) -> Enrollment:
        if not self.repo.student_exists(payload.student_id):
            raise StudentNotFoundError(payload.student_id)
        if not self.repo.course_exists(payload.course_id):
            raise CourseNotFoundError(payload.course_id)
        if self.repo.get_by_unique(
            payload.student_id, payload.course_id, payload.academic_year, payload.semester
        ):
            raise DuplicateEnrollmentError(payload.student_id, payload.course_id)

        try:
            enrollment = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateEnrollmentError(payload.student_id, payload.course_id) from exc
        self.db.refresh(enrollment)
        return enrollment

    def get(self, enrollment_id: UUID) -> Enrollment:
        enrollment = self.repo.get(enrollment_id)
        if enrollment is None:
            raise EnrollmentNotFoundError(enrollment_id)
        return enrollment

    def list_enrollments(
        self,
        *,
        limit: int,
        offset: int,
        student_id: UUID | None = None,
        course_id: UUID | None = None,
        academic_year: str | None = None,
        semester: int | None = None,
    ) -> tuple[Sequence[Enrollment], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            student_id=student_id,
            course_id=course_id,
            academic_year=academic_year,
            semester=semester,
        )

    def update(self, enrollment_id: UUID, payload: EnrollmentUpdate) -> Enrollment:
        enrollment = self.get(enrollment_id)
        data = payload.model_dump(exclude_unset=True)

        new_student = data.get("student_id", enrollment.student_id)
        new_course = data.get("course_id", enrollment.course_id)
        new_year = data.get("academic_year", enrollment.academic_year)
        new_semester = data.get("semester", enrollment.semester)

        if "student_id" in data and not self.repo.student_exists(data["student_id"]):
            raise StudentNotFoundError(data["student_id"])
        if "course_id" in data and not self.repo.course_exists(data["course_id"]):
            raise CourseNotFoundError(data["course_id"])

        existing = self.repo.get_by_unique(new_student, new_course, new_year, new_semester)
        if existing is not None and existing.id != enrollment.id:
            raise DuplicateEnrollmentError(new_student, new_course)

        if not data:
            return enrollment

        try:
            enrollment = self.repo.update(enrollment, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateEnrollmentError(new_student, new_course) from exc
        self.db.refresh(enrollment)
        return enrollment

    def delete(self, enrollment_id: UUID) -> None:
        enrollment = self.get(enrollment_id)
        self.repo.delete(enrollment)
        self.db.commit()