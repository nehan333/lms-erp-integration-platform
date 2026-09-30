"""Business logic for the Course module.

Domain errors are raised as dedicated exceptions so the API layer can map
them to HTTP responses without leaking raw database errors.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.course import Course
from app.repositories.course import CourseRepository
from app.schemas.course import CourseCreate, CourseUpdate


class CourseNotFoundError(Exception):
    """Raised when a course does not exist."""

    def __init__(self, course_id: UUID) -> None:
        super().__init__(f"Course {course_id} not found")
        self.course_id = course_id


class DuplicateCourseError(Exception):
    """Raised when a unique course field is already in use."""

    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Course with {field} '{value}' already exists")
        self.field = field
        self.value = value


class DepartmentNotFoundError(Exception):
    """Raised when a referenced department does not exist."""

    def __init__(self, department_id: UUID) -> None:
        super().__init__(f"Department {department_id} not found")
        self.department_id = department_id


class FacultyNotFoundError(Exception):
    """Raised when a referenced faculty member does not exist."""

    def __init__(self, faculty_id: UUID) -> None:
        super().__init__(f"Faculty {faculty_id} not found")
        self.faculty_id = faculty_id


class CourseInUseError(Exception):
    """Raised when a course cannot be deleted because it is in use."""

    def __init__(self, course_id: UUID) -> None:
        super().__init__(
            f"Course {course_id} cannot be deleted; it has enrollments, "
            "attendance, or grades"
        )
        self.course_id = course_id


class CourseService:
    """Coordinates validation and repository operations for courses."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CourseRepository(db)

    def create(self, payload: CourseCreate) -> Course:
        if not self.repo.department_exists(payload.department_id):
            raise DepartmentNotFoundError(payload.department_id)
        if payload.faculty_id is not None and not self.repo.faculty_exists(payload.faculty_id):
            raise FacultyNotFoundError(payload.faculty_id)
        if self.repo.get_by_code(payload.course_code):
            raise DuplicateCourseError("code", payload.course_code)

        try:
            course = self.repo.create(payload.model_dump())
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateCourseError("code", payload.course_code) from exc
        self.db.refresh(course)
        return course

    def get(self, course_id: UUID) -> Course:
        course = self.repo.get(course_id)
        if course is None:
            raise CourseNotFoundError(course_id)
        return course

    def list_courses(
        self,
        *,
        limit: int,
        offset: int,
        department_id: UUID | None = None,
        faculty_id: UUID | None = None,
        semester: int | None = None,
        search: str | None = None,
    ) -> tuple[Sequence[Course], int]:
        return self.repo.list(
            limit=limit,
            offset=offset,
            department_id=department_id,
            faculty_id=faculty_id,
            semester=semester,
            search=search,
        )

    def update(self, course_id: UUID, payload: CourseUpdate) -> Course:
        course = self.get(course_id)
        data = payload.model_dump(exclude_unset=True)

        if "department_id" in data:
            if not self.repo.department_exists(data["department_id"]):
                raise DepartmentNotFoundError(data["department_id"])
        if "faculty_id" in data and data["faculty_id"] is not None:
            if not self.repo.faculty_exists(data["faculty_id"]):
                raise FacultyNotFoundError(data["faculty_id"])
        if "course_code" in data:
            existing = self.repo.get_by_code(data["course_code"])
            if existing is not None and existing.id != course.id:
                raise DuplicateCourseError("code", data["course_code"])

        if not data:
            return course

        try:
            course = self.repo.update(course, data)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateCourseError("code", data.get("course_code", "")) from exc
        self.db.refresh(course)
        return course

    def delete(self, course_id: UUID) -> None:
        course = self.get(course_id)
        if self.repo.has_children(course_id):
            raise CourseInUseError(course_id)
        try:
            self.repo.delete(course)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise CourseInUseError(course_id) from exc