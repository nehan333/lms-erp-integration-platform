"""Business logic for the Moodle synchronization engine.

Reads ERP records via ``MoodleSyncRepository``, pushes them to Moodle through
``MoodleClient``, and records every outcome in the ``sync_logs`` table.
Each operation is idempotent (find-or-create by ERP key: roll_number ->
Moodle username, course_code -> Moodle shortname). No fake success: a call is
only recorded as ``Success`` when Moodle's real response validates.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.moodle import payloads
from app.integrations.moodle.client import MoodleClient
from app.integrations.moodle.errors import (
    MoodleAPIError,
    MoodleError,
    MoodleNotConfiguredError,
)
from app.models.sync_log import SyncLog
from app.repositories.moodle import MoodleSyncRepository
from app.services.sync_log import SyncLogService

logger = logging.getLogger(__name__)

MODULE = "moodle"


class MoodleSyncService:
    """Orchestrates ERP -> Moodle synchronization and logging."""

    def __init__(self, db: Session, client: MoodleClient | None = None) -> None:
        self.db = db
        self.client = client if client is not None else MoodleClient.from_settings()
        self.repo = MoodleSyncRepository(db)
        self.logger = SyncLogService(db)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _record(
        self,
        *,
        action: str,
        status: str,
        message: str,
    ) -> SyncLog:
        log = self.logger.record(
            module=MODULE,
            action=action,
            status=status,
            message=message,
        )
        logger.info("moodle sync '%s' -> %s: %s", action, status, message)
        return log

    def _lookup_user_id(self, roll_number: str) -> int:
        existing = self.client.call(
            "core_user_get_users_by_field",
            payloads.user_lookup_params(roll_number),
        )
        if isinstance(existing, list) and existing:
            return int(existing[0]["id"])
        raise MoodleAPIError(
            "user_not_found", f"User '{roll_number}' not found in Moodle"
        )

    def _lookup_course_id(self, course_code: str) -> int:
        result = self.client.call(
            "core_course_get_courses_by_field",
            payloads.course_lookup_params(course_code),
        )
        courses = result.get("courses", []) if isinstance(result, dict) else []
        if courses:
            return int(courses[0]["id"])
        raise MoodleAPIError(
            "course_not_found", f"Course '{course_code}' not found in Moodle"
        )

    # ------------------------------------------------------------------ #
    # Connection / auth
    # ------------------------------------------------------------------ #

    def check_connection(self) -> dict:
        """Validate token/auth and return Moodle site info."""
        return self.client.call("core_webservice_get_site_info", {})

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    def sync_students(self) -> SyncLog:
        """Create Moodle users for active ERP students (find-or-create)."""
        students = self.repo.list_students()
        if not students:
            return self._record(action="sync_students", status="Success",
                                message="No students to sync")

        failures: list[str] = []
        created = 0
        for student in students:
            try:
                existing = self.client.call(
                    "core_user_get_users_by_field",
                    payloads.user_lookup_params(student.roll_number),
                )
                if isinstance(existing, list) and existing:
                    continue
                self.client.call(
                    "core_user_create_users", payloads.user_create_params(student)
                )
                created += 1
            except MoodleError as exc:
                failures.append(f"{student.roll_number}: {exc}")

        if failures:
            message = (
                f"{len(failures)} of {len(students)} students failed: "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_students", status="Failed", message=message)
        return self._record(
            action="sync_students", status="Success",
            message=f"{created} students synced",
        )

    def sync_courses(self) -> SyncLog:
        """Create Moodle courses for ERP courses (find-or-create)."""
        courses = self.repo.list_courses()
        if not courses:
            return self._record(action="sync_courses", status="Success",
                                message="No courses to sync")

        failures: list[str] = []
        created = 0
        for course in courses:
            try:
                result = self.client.call(
                    "core_course_get_courses_by_field",
                    payloads.course_lookup_params(course.course_code),
                )
                existing = result.get("courses", []) if isinstance(result, dict) else []
                if existing:
                    continue
                self.client.call(
                    "core_course_create_courses",
                    payloads.course_create_params(
                        course, settings.MOODLE_DEFAULT_CATEGORY_ID
                    ),
                )
                created += 1
            except MoodleError as exc:
                failures.append(f"{course.course_code}: {exc}")

        if failures:
            message = (
                f"{len(failures)} of {len(courses)} courses failed: "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_courses", status="Failed", message=message)
        return self._record(
            action="sync_courses", status="Success",
            message=f"{created} courses synced",
        )

    def sync_enrollments(self) -> SyncLog:
        """Enrol ERP students in their courses on Moodle."""
        enrollments = self.repo.list_enrollments()
        if not enrollments:
            return self._record(action="sync_enrollments", status="Success",
                                message="No enrollments to sync")

        failures: list[str] = []
        enrolled = 0
        for enrollment in enrollments:
            key = (
                f"{enrollment.student.roll_number}/"
                f"{enrollment.course.course_code}"
            )
            try:
                user_id = self._lookup_user_id(enrollment.student.roll_number)
                course_id = self._lookup_course_id(enrollment.course.course_code)
                self.client.call(
                    "enrol_manual_enrol_users",
                    payloads.enrollment_params(
                        user_id, course_id, settings.MOODLE_STUDENT_ROLE_ID
                    ),
                )
                enrolled += 1
            except MoodleError as exc:
                failures.append(f"{key}: {exc}")

        if failures:
            message = (
                f"{len(failures)} of {len(enrollments)} enrollments failed: "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_enrollments", status="Failed",
                                message=message)
        return self._record(
            action="sync_enrollments", status="Success",
            message=f"{enrolled} enrollments synced",
        )

    def sync_grades(self) -> SyncLog:
        """Push final grades to Moodle, grouped per course."""
        grades = self.repo.list_grades()
        if not grades:
            return self._record(action="sync_grades", status="Success",
                                message="No grades to sync")

        by_course: dict[str, list] = {}
        for grade in grades:
            by_course.setdefault(grade.course.course_code, []).append(grade)

        failures: list[str] = []
        updated = 0
        for course_code, course_grades in by_course.items():
            try:
                course_id = self._lookup_course_id(course_code)
                rows: list[tuple[int, str]] = []
                for grade in course_grades:
                    user_id = self._lookup_user_id(grade.student.roll_number)
                    rows.append((user_id, grade.final_grade))
                result = self.client.call(
                    "core_grades_update_grades",
                    payloads.grade_params(course_code, rows),
                )
                if isinstance(result, dict):
                    if result.get("result") is not True:
                        raise MoodleAPIError(
                            "grade_update_failed",
                            f"Course '{course_code}': result not true",
                        )
                    if result.get("failures"):
                        raise MoodleAPIError(
                            "grade_update_failed",
                            f"Course '{course_code}': {len(result['failures'])} failures",
                        )
                updated += 1
            except MoodleError as exc:
                failures.append(f"{course_code}: {exc}")

        if failures:
            message = (
                f"{len(failures)} of {len(by_course)} courses failed: "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_grades", status="Failed", message=message)
        return self._record(
            action="sync_grades", status="Success",
            message=f"{updated} courses graded",
        )

    def sync_attendance(self) -> SyncLog:
        """Submit ERP attendance records to Moodle (configurable wsfunction)."""
        records = self.repo.list_attendance()
        if not records:
            return self._record(action="sync_attendance", status="Success",
                                message="No attendance records to sync")

        wsfunction = settings.MOODLE_ATTENDANCE_WSFUNCTION
        failures: list[str] = []
        synced = 0
        for record in records:
            key = (
                f"{record.student.roll_number}/"
                f"{record.course.course_code}/{record.date}"
            )
            try:
                user_id = self._lookup_user_id(record.student.roll_number)
                course_id = self._lookup_course_id(record.course.course_code)
                self.client.call(
                    wsfunction,
                    payloads.attendance_params(user_id, course_id, record),
                )
                synced += 1
            except MoodleError as exc:
                failures.append(f"{key}: {exc}")

        if failures:
            message = (
                f"{len(failures)} of {len(records)} records failed: "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_attendance", status="Failed",
                                message=message)
        return self._record(
            action="sync_attendance", status="Success",
            message=f"{synced} attendance records synced",
        )

    def sync_all(self) -> list[SyncLog]:
        """Run every sync operation in dependency order and return the logs."""
        if not self.client.is_configured:
            raise MoodleNotConfiguredError()
        return [
            self.sync_students(),
            self.sync_courses(),
            self.sync_enrollments(),
            self.sync_grades(),
            self.sync_attendance(),
        ]