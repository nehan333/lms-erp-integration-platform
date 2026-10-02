"""Business logic for the Enrollment module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.repositories.department import DepartmentRepository
from app.repositories.enrollment import EnrollmentRepository
from app.schemas.enrollment import (
    BulkEnrollmentCoursePreview,
    BulkEnrollmentCourseResult,
    BulkEnrollmentPreview,
    BulkEnrollmentRequest,
    BulkEnrollmentResult,
    EnrollmentCreate,
    EnrollmentUpdate,
)


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


class DepartmentNotFoundError(Exception):
    """Raised when the department selected for bulk enrollment does not exist."""

    def __init__(self, department_id: UUID) -> None:
        super().__init__(f"Department {department_id} not found")
        self.department_id = department_id


class CourseNotInDepartmentError(Exception):
    """Raised when a bulk-enrollment course belongs to another department."""

    def __init__(self, course_id: UUID, department_id: UUID) -> None:
        super().__init__(
            f"Course {course_id} does not belong to department {department_id}"
        )
        self.course_id = course_id
        self.department_id = department_id


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

    # ------------------------------------------------------------------ #
    # Bulk enrollment
    # ------------------------------------------------------------------ #

    def _resolve_bulk(
        self, payload: BulkEnrollmentRequest
    ) -> tuple[list[Student], list[Course]]:
        """Validate a bulk payload and return the cohort plus its courses."""
        if not DepartmentRepository(self.db).exists(payload.department_id):
            raise DepartmentNotFoundError(payload.department_id)

        courses = self.repo.list_courses_by_ids(payload.course_ids)
        by_id = {course.id: course for course in courses}
        missing = [
            cid for cid in payload.course_ids if cid not in by_id
        ]
        if missing:
            raise CourseNotFoundError(missing[0])
        mismatched = [
            cid
            for cid in payload.course_ids
            if by_id[cid].department_id != payload.department_id
        ]
        if mismatched:
            raise CourseNotInDepartmentError(
                mismatched[0], payload.department_id
            )
        ordered = [by_id[cid] for cid in payload.course_ids]
        students = self.repo.list_students_for_cohort(
            payload.department_id, payload.semester
        )
        return students, ordered

    def bulk_preview(self, payload: BulkEnrollmentRequest) -> BulkEnrollmentPreview:
        """Dry-run: report how many enrollments a bulk run would create."""
        students, courses = self._resolve_bulk(payload)
        student_ids = [s.id for s in students]
        course_ids = [c.id for c in courses]
        existing = self.repo.existing_pairs(
            student_ids, course_ids, payload.academic_year, payload.semester
        )

        previews: list[BulkEnrollmentCoursePreview] = []
        total_to_create = 0
        total_existing = 0
        for course in courses:
            already = sum(
                1 for sid in student_ids if (sid, course.id) in existing
            )
            to_create = len(student_ids) - already
            previews.append(
                BulkEnrollmentCoursePreview(
                    course_id=course.id,
                    course_code=course.course_code,
                    course_name=course.course_name,
                    to_create=to_create,
                    already_enrolled=already,
                )
            )
            total_to_create += to_create
            total_existing += already

        return BulkEnrollmentPreview(
            department_id=payload.department_id,
            semester=payload.semester,
            academic_year=payload.academic_year,
            students_total=len(students),
            courses=previews,
            total_to_create=total_to_create,
            total_already_enrolled=total_existing,
        )

    def bulk_create(
        self, payload: BulkEnrollmentRequest
    ) -> tuple[BulkEnrollmentResult, list[UUID]]:
        """Create the missing enrollments; existing pairs are skipped.

        Returns the result plus the ids of newly created enrollments (in
        ``created_ids``) so the caller can trigger a targeted Moodle sync.
        """
        students, courses = self._resolve_bulk(payload)
        student_ids = [s.id for s in students]
        course_ids = [c.id for c in courses]
        existing = self.repo.existing_pairs(
            student_ids, course_ids, payload.academic_year, payload.semester
        )

        results: list[BulkEnrollmentCourseResult] = []
        created_ids: list[UUID] = []
        skipped = 0
        for course in courses:
            course_created = 0
            course_skipped = 0
            for student in students:
                key = (student.id, course.id)
                if key in existing:
                    course_skipped += 1
                    continue
                enrollment = self.repo.create(
                    {
                        "student_id": student.id,
                        "course_id": course.id,
                        "academic_year": payload.academic_year,
                        "semester": payload.semester,
                    }
                )
                created_ids.append(enrollment.id)
                existing.add(key)
                course_created += 1
            results.append(
                BulkEnrollmentCourseResult(
                    course_id=course.id,
                    course_code=course.course_code,
                    created=course_created,
                    skipped=course_skipped,
                )
            )
            skipped += course_skipped

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateEnrollmentError(
                student_ids[0] if student_ids else UUID(int=0),
                course_ids[0],
            ) from exc

        return BulkEnrollmentResult(
            department_id=payload.department_id,
            semester=payload.semester,
            academic_year=payload.academic_year,
            students_total=len(students),
            created=len(created_ids),
            skipped=skipped,
            courses=results,
        ), created_ids