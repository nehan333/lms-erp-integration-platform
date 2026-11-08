"""Business logic for the Moodle synchronization engine.

Reads ERP records via ``MoodleSyncRepository``, pushes them to Moodle through
``MoodleClient``, and records every outcome in the ``sync_logs`` table.
Each operation is idempotent (find-or-create by ERP key: roll_number ->
Moodle username, course_code -> Moodle shortname). No fake success: a call is
only recorded as ``Success`` when Moodle's real response validates.

Concurrency: every public sync operation holds a PostgreSQL advisory lock for
its whole duration, so two overlapping runs can never create duplicate Moodle
users, courses, attendance activities, or attendance sessions. A run that
cannot get the lock fails fast (``SyncInProgressError`` -> HTTP 409 for the
full sync endpoint) instead of racing.

Attendance idempotency: existing attendance activities and sessions are
reused (the lowest instance id wins when several exist), each student's mark
is only written when Moodle's ``attendance_log`` differs from the ERP status,
and every write is read back from ``mod_attendance_get_sessions`` before the
run is reported as successful. Session times are computed as local midnight
in ``MOODLE_SITE_TIMEZONE`` and parsed back with the same zone, so results
do not depend on the host process timezone.

Moodle functions used (verified against Moodle 5.0.10):

- ``core_webservice_get_site_info``       connection check / token user id
- ``core_user_get_users_by_field``        roll_number -> Moodle user
- ``core_user_create_users``              create missing users
- ``core_course_get_courses_by_field``    course_code -> Moodle course
- ``core_course_create_courses``          create missing courses
- ``core_course_get_contents``            discover course activities
- ``enrol_manual_enrol_users``            enrolment sync
- ``core_grades_update_grades``           grade sync (activity grade item)
- ``mod_attendance_add_attendance``       ensure attendance activity exists
- ``mod_attendance_get_sessions``         sessions, statuses and attendance_log
- ``mod_attendance_add_session``          create the session when missing
- ``mod_attendance_get_session``          fallback: read the status set
- ``mod_attendance_update_user_status``   record one student's attendance

The ``mod_attendance_*`` functions require the official Moodle Attendance
activity plugin (``mod_attendance``) and those functions enabled on the
Moodle external service used by the ERP token.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import contextmanager
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import text
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

# ``core_grades_update_grades`` returns an int status flag (lib/grade/constants.php).
GRADE_UPDATE_OK = 0

# Preferred activities to anchor a course's ERP final grade to, in order.
GRADE_ACTIVITY_PREFERENCE = ("assign", "quiz", "workshop", "forum")

# Two-int32 PostgreSQL advisory lock key serializing Moodle sync runs across
# workers/processes ("LMSE" namespace, sync channel).
SYNC_LOCK_KEY = (0x4C4D5345, 1)


class SyncInProgressError(Exception):
    """Raised when another Moodle sync already holds the sync lock."""


def site_timezone() -> ZoneInfo:
    """Timezone of the Moodle site (``MOODLE_SITE_TIMEZONE``)."""
    return ZoneInfo(settings.MOODLE_SITE_TIMEZONE)


def attendance_session_time(record_date: date) -> int:
    """Unix timestamp of local midnight for ``record_date`` in the site TZ.

    Used as the attendance session time so that sessions always land on the
    ERP attendance date regardless of the host process timezone.
    """
    return payloads.local_midnight_ts(record_date)


def attendance_session_date(sessdate: int | str) -> date:
    """Calendar date of an attendance session, interpreted in the site TZ."""
    return datetime.fromtimestamp(int(sessdate), tz=site_timezone()).date()


def status_map_from(statuses: object) -> dict[str, int]:
    """Map lowercased status description/acronym -> status id.

    Status ids are never assumed: they come from Moodle's own response for
    the instance/session (``get_sessions``/``get_session``).
    """
    mapping: dict[str, int] = {}
    if not isinstance(statuses, (list, tuple)):
        return mapping
    for status in statuses:
        if not isinstance(status, dict) or status.get("id") is None:
            continue
        try:
            status_id = int(status["id"])
        except (TypeError, ValueError):
            continue
        for field in ("description", "acronym"):
            label = str(status.get(field) or "").strip().lower()
            if label and label not in mapping:
                mapping[label] = status_id
    return mapping


def session_status_log(session: dict) -> dict[int, int]:
    """Map moodle user id -> status id from a session's ``attendance_log``."""
    log: dict[int, int] = {}
    for entry in session.get("attendance_log") or []:
        if not isinstance(entry, dict):
            continue
        try:
            log[int(entry["studentid"])] = int(entry["statusid"])
        except (KeyError, TypeError, ValueError):
            continue
    return log


class MoodleSyncService:
    """Orchestrates ERP -> Moodle synchronization and logging."""

    def __init__(self, db: Session, client: MoodleClient | None = None) -> None:
        self.db = db
        self.client = client if client is not None else MoodleClient.from_settings()
        self.repo = MoodleSyncRepository(db)
        self.logger = SyncLogService(db)
        # Per-run lookups so one sync does not repeat identical WS calls.
        self._site_userid: int | None = None
        self._user_ids: dict[str, int] = {}
        self._course_ids: dict[str, int] = {}
        self._course_modules: dict[int, list[dict]] = {}
        self._attendance_instances: dict[int, int] = {}
        self._attendance_sessions: dict[int, dict[date, dict]] = {}
        self._attendance_status_cache: dict[tuple[int, int], dict[str, int]] = {}
        # Cross-process sync lock (held on a dedicated connection so it
        # survives the commit/release cycle of the main session).
        self._lock_depth = 0
        self._lock_conn = None

    # ------------------------------------------------------------------ #
    # Sync lock
    # ------------------------------------------------------------------ #

    def _try_acquire_lock(self) -> bool:
        """Try to take the sync lock on a dedicated connection."""
        if self._lock_conn is not None:
            return True
        conn = self.db.get_bind().connect()
        try:
            acquired = conn.execute(
                text("SELECT pg_try_advisory_lock(:ns, :channel)"),
                {"ns": SYNC_LOCK_KEY[0], "channel": SYNC_LOCK_KEY[1]},
            ).scalar()
        except Exception:
            conn.close()
            raise
        if not acquired:
            conn.close()
            return False
        self._lock_conn = conn
        return True

    def _release_lock(self) -> None:
        conn = self._lock_conn
        self._lock_conn = None
        if conn is None:
            return
        try:
            conn.execute(
                text("SELECT pg_advisory_unlock(:ns, :channel)"),
                {"ns": SYNC_LOCK_KEY[0], "channel": SYNC_LOCK_KEY[1]},
            )
        finally:
            conn.close()

    @contextmanager
    def _sync_guard(self):
        """Hold the sync lock for the duration of one sync operation.

        Re-entrant for the same service instance so ``sync_all`` can call the
        individual operations without deadlocking against itself. Raises
        ``SyncInProgressError`` when another run already holds the lock.
        """
        if self._lock_depth > 0:
            self._lock_depth += 1
            try:
                yield
            finally:
                self._lock_depth -= 1
            return
        if not self._try_acquire_lock():
            raise SyncInProgressError(
                "Another Moodle synchronization is already running"
            )
        self._lock_depth = 1
        try:
            yield
        finally:
            self._lock_depth = 0
            self._release_lock()

    def _run_locked(self, action: str, operation: Callable[[], SyncLog]) -> SyncLog:
        """Run ``operation`` under the sync lock.

        The individual operations keep their ``SyncLog`` contract: when the
        lock is busy they record an honest ``Failed`` entry instead of
        raising (the full-sync endpoint surfaces ``SyncInProgressError`` as
        HTTP 409 instead).
        """
        try:
            with self._sync_guard():
                return operation()
        except SyncInProgressError:
            return self._record(
                action=action,
                status="Failed",
                message="Another Moodle synchronization is already running",
            )

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
        if roll_number in self._user_ids:
            return self._user_ids[roll_number]
        existing = self.client.call(
            "core_user_get_users_by_field",
            payloads.user_lookup_params(roll_number),
        )
        if isinstance(existing, list) and existing:
            self._user_ids[roll_number] = int(existing[0]["id"])
            return self._user_ids[roll_number]
        raise MoodleAPIError(
            "user_not_found", f"User '{roll_number}' not found in Moodle"
        )

    def _lookup_course_id(self, course_code: str) -> int:
        if course_code in self._course_ids:
            return self._course_ids[course_code]
        result = self.client.call(
            "core_course_get_courses_by_field",
            payloads.course_lookup_params(course_code),
        )
        courses = result.get("courses", []) if isinstance(result, dict) else []
        if courses:
            self._course_ids[course_code] = int(courses[0]["id"])
            return self._course_ids[course_code]
        raise MoodleAPIError(
            "course_not_found", f"Course '{course_code}' not found in Moodle"
        )

    def _get_site_userid(self) -> int:
        """Moodle user id of the token owner (used as attendance taker)."""
        if self._site_userid is None:
            info = self.client.call("core_webservice_get_site_info", {})
            self._site_userid = int(info["userid"])
        return self._site_userid

    def _get_course_modules(self, moodle_course_id: int) -> list[dict]:
        """Return the activity modules of a Moodle course."""
        if moodle_course_id not in self._course_modules:
            sections = self.client.call(
                "core_course_get_contents",
                {"courseid": str(moodle_course_id)},
            )
            modules: list[dict] = []
            if isinstance(sections, list):
                for section in sections:
                    if isinstance(section, dict):
                        modules.extend(section.get("modules", []) or [])
            self._course_modules[moodle_course_id] = modules
        return self._course_modules[moodle_course_id]

    def _pick_grade_activity(self, moodle_course_id: int) -> tuple[str, int]:
        """Pick the course module whose grade item receives ERP final grades.

        Returns ``(component, activityid)`` e.g. ``("mod_forum", 3)``. The
        attendance activity is skipped so grades are not filed under
        "Attendance". Raises when the Moodle course has no usable activity.
        """
        modules = [
            module
            for module in self._get_course_modules(moodle_course_id)
            if module.get("modname") and module.get("id")
        ]
        chosen: dict | None = None
        for preference in GRADE_ACTIVITY_PREFERENCE:
            chosen = next(
                (m for m in modules if m["modname"] == preference), None
            )
            if chosen is not None:
                break
        if chosen is None:
            chosen = next(
                (m for m in modules if m["modname"] != "attendance"), None
            )
        if chosen is None:
            raise MoodleAPIError(
                "no_gradeable_activity",
                f"Moodle course {moodle_course_id} has no activity to "
                "attach grades to",
            )
        return f"mod_{chosen['modname']}", int(chosen["id"])

    def _ensure_attendance_instance(self, moodle_course_id: int) -> int:
        """Return the course's attendance instance id, creating it if missing.

        When a course already has several attendance activities (created by a
        past race) the lowest instance id wins so every later call converges
        on the same one instead of scattering sessions across duplicates.
        """
        if moodle_course_id in self._attendance_instances:
            return self._attendance_instances[moodle_course_id]
        existing_ids = [
            int(module["instance"])
            for module in self._get_course_modules(moodle_course_id)
            if module.get("modname") == "attendance" and module.get("instance")
        ]
        if existing_ids:
            attendance_id = min(existing_ids)
        else:
            result = self.client.call(
                "mod_attendance_add_attendance",
                payloads.attendance_instance_params(moodle_course_id),
            )
            attendance_id = int(result["attendanceid"])
        self._attendance_instances[moodle_course_id] = attendance_id
        return attendance_id

    def _ensure_attendance_session(
        self, attendance_id: int, record_date: date
    ) -> dict:
        """Return the session covering ``record_date``, creating it if missing."""
        if attendance_id not in self._attendance_sessions:
            self._attendance_sessions[attendance_id] = self._fetch_sessions(
                attendance_id
            )
        sessions = self._attendance_sessions[attendance_id]
        session = sessions.get(record_date)
        if session is not None:
            return session

        sessiontime = attendance_session_time(record_date)
        self.client.call(
            "mod_attendance_add_session",
            payloads.attendance_session_params(
                attendance_id, sessiontime, description=f"ERP {record_date}"
            ),
        )
        sessions = self._fetch_sessions(attendance_id)
        self._attendance_sessions[attendance_id] = sessions
        session = sessions.get(record_date)
        if session is None:
            raise MoodleAPIError(
                "session_not_found",
                f"Session for {record_date} not found after creation",
            )
        return session

    def _fetch_session_list(self, attendance_id: int) -> list[dict]:
        """Raw session list from Moodle (handles list and id-keyed responses)."""
        result = self.client.call(
            "mod_attendance_get_sessions",
            {"attendanceid": str(attendance_id)},
        )
        if isinstance(result, dict):
            # Defensive: a non-list JSON object keyed by session id.
            result = list(result.values())
        if not isinstance(result, list):
            return []
        return [
            session
            for session in result
            if isinstance(session, dict) and "sessdate" in session
        ]

    def _fetch_sessions(self, attendance_id: int) -> dict[date, dict]:
        sessions: dict[date, dict] = {}
        for session in self._fetch_session_list(attendance_id):
            session_date = attendance_session_date(session["sessdate"])
            sessions.setdefault(session_date, session)
        return sessions

    def _attendance_statuses(self, attendance_id: int, session: dict) -> dict[str, int]:
        """Map lowercased status description -> status id for a session.

        Prefers the status set embedded in the ``get_sessions`` payload (no
        extra call) and falls back to ``mod_attendance_get_session``. Ids
        always come from Moodle, never from constants in this codebase.
        """
        embedded = status_map_from(session.get("statuses"))
        if embedded:
            return embedded
        status_set = int(session.get("statusset", 0))
        key = (attendance_id, status_set)
        if key not in self._attendance_status_cache:
            detail = self.client.call(
                "mod_attendance_get_session",
                {"sessionid": str(session["id"])},
            )
            self._attendance_status_cache[key] = status_map_from(
                detail.get("statuses") if isinstance(detail, dict) else None
            )
        return self._attendance_status_cache[key]

    # ------------------------------------------------------------------ #
    # Connection / auth
    # ------------------------------------------------------------------ #

    def check_connection(self) -> dict:
        """Validate token/auth and return Moodle site info."""
        return self.client.call("core_webservice_get_site_info", {})

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    def sync_students(
        self, student_ids: list[UUID] | None = None
    ) -> SyncLog:
        """Create Moodle users for active ERP students (find-or-create).

        With ``student_ids`` only those students are pushed (used by the bulk
        CSV import right after it created them).
        """
        return self._run_locked(
            "sync_students", lambda: self._sync_students(student_ids)
        )

    def _sync_students(
        self, student_ids: list[UUID] | None = None
    ) -> SyncLog:
        students = self.repo.list_students(student_ids)
        if not students:
            return self._record(action="sync_students", status="Success",
                                message="No students to sync")
        if not self.client.is_configured:
            return self._record(
                action="sync_students", status="Failed",
                message=(
                    f"Moodle not configured; {len(students)} "
                    "students pending sync"
                ),
            )

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
        return self._run_locked("sync_courses", self._sync_courses)

    def _sync_courses(self) -> SyncLog:
        courses = self.repo.list_courses()
        if not courses:
            return self._record(action="sync_courses", status="Success",
                                message="No courses to sync")

        # Anchor new courses at their first attendance record (or the overall
        # earliest one) so Moodle never starts the course after its sessions.
        earliest = self.repo.earliest_attendance_dates()
        fallback_start = min(earliest.values()) if earliest else None

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
                        course,
                        settings.MOODLE_DEFAULT_CATEGORY_ID,
                        earliest.get(course.id, fallback_start),
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
    def sync_enrollments(
        self, enrollment_ids: list[UUID] | None = None
    ) -> SyncLog:
        """Enrol ERP students in their courses on Moodle.

        With ``enrollment_ids`` only those enrollments are pushed (used by the
        bulk enrollment workflow right after it created them). When Moodle is
        not configured the run is recorded as ``Failed`` with an explicit
        "pending sync" message instead of pretending success.
        """
        return self._run_locked(
            "sync_enrollments", lambda: self._sync_enrollments(enrollment_ids)
        )

    def _sync_enrollments(
        self, enrollment_ids: list[UUID] | None = None
    ) -> SyncLog:
        enrollments = self.repo.list_enrollments(enrollment_ids)
        if not enrollments:
            return self._record(action="sync_enrollments", status="Success",
                                message="No enrollments to sync")
        if not self.client.is_configured:
            return self._record(
                action="sync_enrollments", status="Failed",
                message=(
                    f"Moodle not configured; {len(enrollments)} "
                    "enrollments pending sync"
                ),
            )

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
        """Push final grades to Moodle, grouped per course.

        One ``core_grades_update_grades`` call per course updates that course's
        grade item (created by Moodle on first sync). The ERP letter grade is
        converted to points (see ``payloads.final_grade_to_points``) and the
        original letter is kept as the grade feedback.
        """
        return self._run_locked("sync_grades", self._sync_grades)

    def _sync_grades(self) -> SyncLog:
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
                component, activity_id = self._pick_grade_activity(course_id)
                rows: list[tuple[int, float, str | None]] = []
                for grade in course_grades:
                    user_id = self._lookup_user_id(grade.student.roll_number)
                    try:
                        points = payloads.final_grade_to_points(
                            grade.final_grade
                        )
                    except ValueError as exc:
                        raise MoodleAPIError(
                            "invalid_grade_value",
                            f"{grade.student.roll_number}: {exc}",
                        ) from exc
                    rows.append(
                        (
                            user_id,
                            points,
                            f"ERP final grade: {grade.final_grade}",
                        )
                    )
                result = self.client.call(
                    "core_grades_update_grades",
                    payloads.grade_params(
                        course_id, component, activity_id, rows
                    ),
                )
                if not isinstance(result, int) or result != GRADE_UPDATE_OK:
                    raise MoodleAPIError(
                        "grade_update_failed",
                        f"Course '{course_code}': Moodle returned status "
                        f"{result!r} (expected {GRADE_UPDATE_OK})",
                    )
                updated += 1
            except (MoodleError, ValueError) as exc:
                failures.append(f"{course_code}: {exc}")

        if failures:
            message = (
                f"{len(failures)} of {len(by_course)} courses failed: "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_grades", status="Failed",
                                message=message)
        return self._record(
            action="sync_grades", status="Success",
            message=f"{updated} courses graded",
        )

    def sync_attendance(self) -> SyncLog:
        """Submit ERP attendance records to Moodle via the Attendance plugin.

        For every course the sync ensures one attendance activity exists, then
        one session per ERP attendance date, then records each student's
        Present/Absent status in that session
        (``mod_attendance_update_user_status``). Moodle upserts on
        (session, student), so repeated runs update rather than duplicate.

        Idempotent by construction: a mark whose status id already matches
        Moodle's ``attendance_log`` is skipped (no write, no ``timetaken``
        churn), and every written mark is read back from Moodle before the
        run is reported as successful.
        """
        return self._run_locked("sync_attendance", self._sync_attendance)

    def _sync_attendance(self) -> SyncLog:
        records = self.repo.list_attendance()
        if not records:
            return self._record(action="sync_attendance", status="Success",
                                message="No attendance records to sync")

        by_course: dict[str, list] = {}
        for record in records:
            by_course.setdefault(record.course.course_code, []).append(record)

        failures: list[str] = []
        failed_records = 0
        written = 0
        unchanged = 0
        for course_code, course_records in by_course.items():
            try:
                moodle_course_id = self._lookup_course_id(course_code)
                attendance_id = self._ensure_attendance_instance(
                    moodle_course_id
                )
                taken_by_id = self._get_site_userid()
            except MoodleError as exc:
                failed_records += len(course_records)
                failures.append(f"{course_code}: {exc}")
                continue

            by_date: dict[date, list] = {}
            for record in course_records:
                by_date.setdefault(record.date, []).append(record)

            pending: list[tuple[int, int, int]] = []
            for record_date, day_records in by_date.items():
                try:
                    session = self._ensure_attendance_session(
                        attendance_id, record_date
                    )
                    statuses = self._attendance_statuses(
                        attendance_id, session
                    )
                except MoodleError as exc:
                    failed_records += len(day_records)
                    failures.append(f"{course_code}/{record_date}: {exc}")
                    continue

                current_log = session_status_log(session)
                for record in day_records:
                    key = (
                        f"{record.student.roll_number}/"
                        f"{course_code}/{record.date}"
                    )
                    try:
                        user_id = self._lookup_user_id(
                            record.student.roll_number
                        )
                        status_id = statuses.get(record.status.strip().lower())
                        if status_id is None:
                            raise MoodleAPIError(
                                "attendance_status_not_found",
                                f"Moodle has no status '{record.status}' "
                                f"for course '{course_code}'",
                            )
                        if current_log.get(user_id) == status_id:
                            # Moodle already shows exactly what the ERP says.
                            unchanged += 1
                            continue
                        self.client.call(
                            "mod_attendance_update_user_status",
                            payloads.attendance_status_params(
                                session_id=int(session["id"]),
                                moodle_user_id=user_id,
                                taken_by_id=taken_by_id,
                                status_id=status_id,
                                status_set=int(session.get("statusset", 0)),
                            ),
                        )
                        written += 1
                        pending.append(
                            (int(session["id"]), user_id, status_id)
                        )
                    except (MoodleError, ValueError, KeyError) as exc:
                        failed_records += 1
                        failures.append(f"{key}: {exc}")

            if pending:
                failed_records += self._verify_written_marks(
                    attendance_id, pending, course_code, failures
                )

        if failures:
            message = (
                f"{failed_records} of {len(records)} records failed "
                f"({written} written, {unchanged} already up-to-date): "
                + "; ".join(failures[:5])
            )
            return self._record(action="sync_attendance", status="Failed",
                                message=message)
        return self._record(
            action="sync_attendance", status="Success",
            message=f"{written} written, {unchanged} already up-to-date",
        )

    def _verify_written_marks(
        self,
        attendance_id: int,
        pending: list[tuple[int, int, int]],
        course_code: str,
        failures: list[str],
    ) -> int:
        """Read marks back from Moodle; return how many are missing.

        A WebSocket call that returns HTTP 200 is not proof: the mark must
        actually appear in the session's ``attendance_log``. When the
        response carries no ``attendance_log`` the check is skipped rather
        than inventing a result.
        """
        try:
            sessions = self._fetch_session_list(attendance_id)
        except MoodleError as exc:
            failures.append(f"{course_code}: read-back failed: {exc}")
            return len(pending)
        by_id = {
            int(session["id"]): session
            for session in sessions
            if session.get("id") is not None
        }
        missing = 0
        for session_id, user_id, status_id in pending:
            session = by_id.get(session_id)
            if session is None or "attendance_log" not in session:
                continue
            if session_status_log(session).get(user_id) != status_id:
                missing += 1
                failures.append(
                    f"{course_code}/session {session_id}: mark for user "
                    f"{user_id} not visible in Moodle after write"
                )
        return missing

    def sync_all(self) -> list[SyncLog]:
        """Run every sync operation in dependency order and return the logs.

        Holds the sync lock for the whole run; raises
        ``SyncInProgressError`` when another sync is already running (the
        endpoint maps that to HTTP 409).
        """
        if not self.client.is_configured:
            raise MoodleNotConfiguredError()
        with self._sync_guard():
            return [
                self.sync_students(),
                self.sync_courses(),
                self.sync_enrollments(),
                self.sync_grades(),
                self.sync_attendance(),
            ]