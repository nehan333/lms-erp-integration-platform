"""Sprint 7 — MoodleSyncService tests (success, failure, idempotency, logging).

Uses a fake client so no real Moodle is contacted. The fake honours
``MoodleError`` semantics the same way ``MoodleClient`` does.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import text

from app.integrations.moodle.errors import (
    MoodleAPIError,
    MoodleError,
    MoodleNotConfiguredError,
)
from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student
from app.services.moodle import (
    SYNC_LOCK_KEY,
    MoodleSyncService,
    SyncInProgressError,
    attendance_session_date,
    attendance_session_time,
)


class FakeMoodleClient:
    """Scripted stand-in for ``MoodleClient`` used by the sync service."""

    def __init__(self, *, is_configured: bool = True) -> None:
        self.is_configured = is_configured
        self.calls: list[tuple[str, dict]] = []
        self.default_response: object = []
        self.response_overrides: dict[str, object] = {}
        self.response_sequences: dict[str, list] = {}
        self.error_overrides: dict[str, list[MoodleError]] = {}

    def call(self, wsfunction: str, params: dict) -> object:
        self.calls.append((wsfunction, params))
        if wsfunction in self.error_overrides:
            errors = self.error_overrides[wsfunction]
            if errors:
                raise errors.pop(0)
        sequence = self.response_sequences.get(wsfunction)
        if sequence:
            return sequence.pop(0)
        if wsfunction in self.response_overrides:
            return self.response_overrides[wsfunction]
        return self.default_response


def _seed_erp(db_session):
    dept = Department(department_code="CSE", department_name="Computer Science")
    db_session.add(dept)
    db_session.flush()

    faculty = Faculty(
        employee_id="F1", name="Prof A", email="a@college.edu",
        designation="Professor", department_id=dept.id,
    )
    db_session.add(faculty)
    db_session.flush()

    students = [
        Student(
            roll_number=f"CS{i:04d}", name=f"Student {i}", email=f"s{i}@student.college.edu",
            department_id=dept.id, semester=1, section="A",
        )
        for i in range(1, 3)
    ]
    db_session.add_all(students)
    db_session.flush()

    course = Course(
        course_code="CS101", course_name="Data Structures", credits=4,
        semester=1, department_id=dept.id, faculty_id=faculty.id,
    )
    db_session.add(course)
    db_session.flush()

    enrollment = Enrollment(
        student_id=students[0].id, course_id=course.id,
        academic_year="2025-2026", semester=1,
    )
    db_session.add(enrollment)
    db_session.flush()

    grade = Grade(
        student_id=students[0].id, course_id=course.id,
        internal_marks=35, external_marks=45, final_grade="B+",
    )
    db_session.add(grade)
    attendance = Attendance(
        student_id=students[0].id, course_id=course.id,
        date=date(2025, 8, 1), status="Present",
    )
    db_session.add(attendance)
    db_session.commit()

    return {
        "dept": dept, "faculty": faculty, "students": students,
        "course": course, "enrollment": enrollment, "grade": grade,
        "attendance": attendance,
    }


def _success_client() -> FakeMoodleClient:
    client = FakeMoodleClient()
    client.response_overrides["core_webservice_get_site_info"] = {
        "userid": 3, "sitename": "Test LMS",
    }
    client.response_overrides["core_user_get_users_by_field"] = [{"id": 1}]
    client.response_overrides["core_course_get_courses_by_field"] = {
        "courses": [{"id": 2}]
    }
    client.response_overrides["core_user_create_users"] = [{"id": 1}]
    client.response_overrides["core_course_create_courses"] = [{"id": 2}]
    client.response_overrides["core_course_get_contents"] = [
        {"modules": [
            {"id": 1, "modname": "forum", "instance": 1, "name": "Announcements"},
            {"id": 21, "modname": "attendance", "instance": 1, "name": "Attendance"},
        ]}
    ]
    client.response_overrides["enrol_manual_enrol_users"] = []
    client.response_overrides["core_grades_update_grades"] = 0
    client.response_overrides["mod_attendance_get_sessions"] = [
        {
            "id": 10,
            "sessdate": int(datetime(2025, 8, 1).timestamp()),
            "statusset": 0,
        },
    ]
    client.response_overrides["mod_attendance_get_session"] = {
        "statuses": [{"id": 5, "description": "Present"}],
    }
    client.response_overrides["mod_attendance_update_user_status"] = None
    return client


# --------------------------------------------------------------------------- #
# sync_students
# --------------------------------------------------------------------------- #


def test_sync_students_creates_new_users(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = []
    client.response_overrides["core_user_create_users"] = [{"id": 1}]

    log = MoodleSyncService(db_session, client).sync_students()
    assert log.module == "moodle"
    assert log.action == "sync_students"
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_user_create_users"]
    assert len(created) == 2


def test_sync_students_skips_existing_users(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = [{"id": 5}]

    log = MoodleSyncService(db_session, client).sync_students()
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_user_create_users"]
    assert created == []


def test_sync_students_partial_failure(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_user_get_users_by_field"] = []
    client.error_overrides["core_user_create_users"] = [
        MoodleAPIError("invalidparameter", "bad email")
    ]

    log = MoodleSyncService(db_session, client).sync_students()
    assert log.status == "Failed"
    assert "1 of 2 students failed" in log.message
    assert "bad email" in log.message


# --------------------------------------------------------------------------- #
# sync_courses
# --------------------------------------------------------------------------- #


def test_sync_courses_creates_new_courses(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_course_get_courses_by_field"] = {"courses": []}
    client.response_overrides["core_course_create_courses"] = [{"id": 9}]

    log = MoodleSyncService(db_session, client).sync_courses()
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_course_create_courses"]
    assert len(created) == 1


def test_sync_courses_skips_existing_courses(db_session):
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_course_get_courses_by_field"] = {
        "courses": [{"id": 9}]
    }

    log = MoodleSyncService(db_session, client).sync_courses()
    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_course_create_courses"]
    assert created == []


# --------------------------------------------------------------------------- #
# sync_enrollments
# --------------------------------------------------------------------------- #


def test_sync_enrollments_success(db_session):
    _seed_erp(db_session)
    client = _success_client()
    log = MoodleSyncService(db_session, client).sync_enrollments()
    assert log.status == "Success"
    enrolled = [c for c in client.calls if c[0] == "enrol_manual_enrol_users"]
    assert len(enrolled) == 1


def test_sync_enrollments_failure_when_user_missing(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.response_overrides["core_user_get_users_by_field"] = []

    log = MoodleSyncService(db_session, client).sync_enrollments()
    assert log.status == "Failed"
    assert "not found in Moodle" in log.message
    assert "1 of 1 enrollments failed" in log.message


# --------------------------------------------------------------------------- #
# sync_grades
# --------------------------------------------------------------------------- #


def test_sync_grades_success(db_session):
    _seed_erp(db_session)
    client = _success_client()
    log = MoodleSyncService(db_session, client).sync_grades()
    assert log.status == "Success"
    graded = [c for c in client.calls if c[0] == "core_grades_update_grades"]
    assert len(graded) == 1
    params = graded[0][1]
    assert params["component"] == "mod_forum"
    assert params["activityid"] == "1"
    assert params["grades[0][grade]"] == "70.0"
    assert params["grades[0][str_feedback]"] == "ERP final grade: B+"


def test_sync_grades_failure_when_result_not_ok(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.response_overrides["core_grades_update_grades"] = 1

    log = MoodleSyncService(db_session, client).sync_grades()
    assert log.status == "Failed"
    assert "Moodle returned status 1" in log.message
    assert "1 of 1 courses failed" in log.message


# --------------------------------------------------------------------------- #
# sync_attendance
# --------------------------------------------------------------------------- #


def test_sync_attendance_success(db_session):
    _seed_erp(db_session)
    client = _success_client()
    log = MoodleSyncService(db_session, client).sync_attendance()
    assert log.status == "Success"
    submitted = [c for c in client.calls if c[0] == "mod_attendance_update_user_status"]
    assert len(submitted) == 1
    params = submitted[0][1]
    assert params["sessionid"] == "10"
    assert params["studentid"] == "1"
    assert params["statusid"] == "5"
    assert params["takenbyid"] == "3"


def test_sync_attendance_creates_missing_session(db_session):
    _seed_erp(db_session)
    client = _success_client()
    created = {"id": 11, "sessdate": int(datetime(2025, 8, 1).timestamp()),
               "statusset": 0}
    client.response_sequences["mod_attendance_get_sessions"] = [[], [created]]
    client.response_overrides["mod_attendance_add_session"] = {"sessionid": 11}
    log = MoodleSyncService(db_session, client).sync_attendance()
    assert log.status == "Success"
    assert any(c[0] == "mod_attendance_add_session" for c in client.calls)


def test_sync_attendance_failure(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.error_overrides["mod_attendance_update_user_status"] = [
        MoodleAPIError("nopermissions", "not allowed")
    ]
    log = MoodleSyncService(db_session, client).sync_attendance()
    assert log.status == "Failed"
    assert "1 of 1 records failed" in log.message


def test_sync_attendance_failure_when_status_unknown(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.response_overrides["mod_attendance_get_session"] = {
        "statuses": [{"id": 6, "description": "Absent"}],
    }
    log = MoodleSyncService(db_session, client).sync_attendance()
    assert log.status == "Failed"
    assert "no status 'Present'" in log.message


# --------------------------------------------------------------------------- #
# Connection / orchestration
# --------------------------------------------------------------------------- #


def test_check_connection_returns_site_info(db_session):
    client = FakeMoodleClient()
    client.response_overrides["core_webservice_get_site_info"] = {
        "sitename": "Test LMS", "version": "2024042200",
    }
    info = MoodleSyncService(db_session, client).check_connection()
    assert info["sitename"] == "Test LMS"


def test_sync_all_records_five_logs(db_session):
    _seed_erp(db_session)
    client = _success_client()
    logs = MoodleSyncService(db_session, client).sync_all()
    assert len(logs) == 5
    assert all(log.status == "Success" for log in logs)


def test_sync_all_raises_when_not_configured(db_session):
    client = FakeMoodleClient(is_configured=False)
    with pytest.raises(MoodleNotConfiguredError):
        MoodleSyncService(db_session, client).sync_all()

# --------------------------------------------------------------------------- #
# Attendance idempotency, read-back verification, timezone, locking
# --------------------------------------------------------------------------- #

# 2025-08-01 00:00:00 Asia/Kolkata == 2025-07-31 18:30:00 UTC
IST_MIDNIGHT_2025_08_01 = 1753986600

PRESENT_STATUSES = [
    {"id": 5, "description": "Present", "acronym": "P"},
    {"id": 6, "description": "Absent", "acronym": "A"},
]


class StatefulAttendanceClient(FakeMoodleClient):
    """Fake that keeps sessions and marks like the Attendance plugin does."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sessions: list[dict] = []
        self.marks: dict[tuple[int, int], int] = {}
        self._next_session_id = 11

    def call(self, wsfunction: str, params: dict) -> object:
        if wsfunction == "mod_attendance_get_sessions":
            self.calls.append((wsfunction, params))
            return [
                {
                    **session,
                    "statuses": PRESENT_STATUSES,
                    "attendance_log": [
                        {"studentid": user_id, "statusid": str(status_id)}
                        for (sid, user_id), status_id in self.marks.items()
                        if sid == session["id"]
                    ],
                }
                for session in self.sessions
            ]
        if wsfunction == "mod_attendance_add_session":
            self.calls.append((wsfunction, params))
            session_id = self._next_session_id
            self._next_session_id += 1
            self.sessions.append(
                {
                    "id": session_id,
                    "sessdate": int(params["sessiontime"]),
                    "statusset": 0,
                }
            )
            return {"sessionid": session_id}
        if wsfunction == "mod_attendance_update_user_status":
            self.calls.append((wsfunction, params))
            self.marks[
                (int(params["sessionid"]), int(params["studentid"]))
            ] = int(params["statusid"])
            return None
        if wsfunction == "mod_attendance_add_attendance":
            self.calls.append((wsfunction, params))
            return {"attendanceid": 1}
        return super().call(wsfunction, params)


def _stateful_client() -> StatefulAttendanceClient:
    client = StatefulAttendanceClient()
    client.response_overrides["core_webservice_get_site_info"] = {"userid": 3}
    client.response_overrides["core_user_get_users_by_field"] = [{"id": 1}]
    client.response_overrides["core_course_get_courses_by_field"] = {
        "courses": [{"id": 2}]
    }
    client.response_overrides["core_course_get_contents"] = [
        {
            "modules": [
                {"id": 1, "modname": "forum", "instance": 1, "name": "Forum"},
                {
                    "id": 21,
                    "modname": "attendance",
                    "instance": 1,
                    "name": "Attendance",
                },
            ]
        }
    ]
    return client


def _hold_sync_lock(test_engine):
    conn = test_engine.connect()
    conn.execute(
        text("SELECT pg_try_advisory_lock(:ns, :channel)"),
        {"ns": SYNC_LOCK_KEY[0], "channel": SYNC_LOCK_KEY[1]},
    )
    return conn


def _release_sync_lock(conn) -> None:
    try:
        conn.execute(
            text("SELECT pg_advisory_unlock(:ns, :channel)"),
            {"ns": SYNC_LOCK_KEY[0], "channel": SYNC_LOCK_KEY[1]},
        )
    finally:
        conn.close()


def test_session_time_helpers_use_site_timezone():
    assert attendance_session_time(date(2025, 8, 1)) == IST_MIDNIGHT_2025_08_01
    assert attendance_session_date(IST_MIDNIGHT_2025_08_01) == date(2025, 8, 1)
    # A timestamp from another zone still resolves to the ERP date.
    assert attendance_session_date(IST_MIDNIGHT_2025_08_01 + 3600) == date(
        2025, 8, 1
    )


def test_sync_attendance_uses_site_timezone_for_session_time(db_session):
    _seed_erp(db_session)
    client = _success_client()
    created = {
        "id": 11,
        "sessdate": IST_MIDNIGHT_2025_08_01,
        "statusset": 0,
        "statuses": PRESENT_STATUSES,
    }
    client.response_sequences["mod_attendance_get_sessions"] = [[], [created]]
    client.response_overrides["mod_attendance_add_session"] = {"sessionid": 11}

    log = MoodleSyncService(db_session, client).sync_attendance()

    assert log.status == "Success"
    added = [c for c in client.calls if c[0] == "mod_attendance_add_session"]
    assert len(added) == 1
    # Exact local midnight in Asia/Kolkata, independent of the process TZ.
    assert added[0][1]["sessiontime"] == str(IST_MIDNIGHT_2025_08_01)


def test_sync_attendance_skips_marks_moodle_already_has(db_session):
    _seed_erp(db_session)
    client = _success_client()
    session = {
        "id": 10,
        "sessdate": IST_MIDNIGHT_2025_08_01,
        "statusset": 0,
        "attendance_log": [
            {"studentid": 1, "statusid": "5", "remarks": "", "id": "1"}
        ],
    }
    client.response_overrides["mod_attendance_get_sessions"] = [session]

    log = MoodleSyncService(db_session, client).sync_attendance()

    assert log.status == "Success"
    assert "0 written" in log.message
    assert "1 already up-to-date" in log.message
    assert not any(
        c[0] == "mod_attendance_update_user_status" for c in client.calls
    )


def test_sync_attendance_rewrites_stale_marks(db_session):
    _seed_erp(db_session)
    client = _success_client()
    stale = {
        "id": 10,
        "sessdate": IST_MIDNIGHT_2025_08_01,
        "statusset": 0,
        "attendance_log": [
            {"studentid": 1, "statusid": "6", "remarks": "", "id": "1"}
        ],
    }
    fixed = {
        **stale,
        "attendance_log": [
            {"studentid": 1, "statusid": "5", "remarks": "", "id": "1"}
        ],
    }
    # First fetch drives the decision, second is the read-back verification.
    client.response_sequences["mod_attendance_get_sessions"] = [[stale], [fixed]]

    log = MoodleSyncService(db_session, client).sync_attendance()

    assert log.status == "Success"
    submitted = [
        c for c in client.calls if c[0] == "mod_attendance_update_user_status"
    ]
    assert len(submitted) == 1
    assert submitted[0][1]["statusid"] == "5"
    assert "1 written" in log.message
    assert "0 already up-to-date" in log.message


def test_sync_attendance_fails_when_mark_not_visible_after_write(db_session):
    """A WS 200 is not proof: the mark must appear in attendance_log."""
    _seed_erp(db_session)
    client = _success_client()
    without_log = {"id": 10, "sessdate": IST_MIDNIGHT_2025_08_01, "statusset": 0}
    with_empty_log = {**without_log, "attendance_log": []}
    client.response_sequences["mod_attendance_get_sessions"] = [
        [without_log],
        [with_empty_log],
    ]

    log = MoodleSyncService(db_session, client).sync_attendance()

    assert log.status == "Failed"
    assert "not visible in Moodle after write" in log.message
    assert any(
        c[0] == "mod_attendance_update_user_status" for c in client.calls
    )


def test_sync_attendance_picks_lowest_attendance_instance(db_session):
    _seed_erp(db_session)
    client = _success_client()
    client.response_overrides["core_course_get_contents"] = [
        {
            "modules": [
                {
                    "id": 30,
                    "modname": "attendance",
                    "instance": 7,
                    "name": "Attendance",
                },
                {
                    "id": 31,
                    "modname": "attendance",
                    "instance": 3,
                    "name": "Attendance",
                },
                {"id": 1, "modname": "forum", "instance": 1},
            ]
        }
    ]
    session = {
        "id": 10,
        "sessdate": IST_MIDNIGHT_2025_08_01,
        "statusset": 0,
        "attendance_log": [
            {"studentid": 1, "statusid": "5", "remarks": "", "id": "1"}
        ],
    }
    client.response_overrides["mod_attendance_get_sessions"] = [session]

    log = MoodleSyncService(db_session, client).sync_attendance()

    assert log.status == "Success"
    lookups = [
        c for c in client.calls if c[0] == "mod_attendance_get_sessions"
    ]
    assert lookups[0][1] == {"attendanceid": "3"}
    assert not any(c[0] == "mod_attendance_add_attendance" for c in client.calls)


def test_sync_attendance_second_run_writes_nothing(db_session):
    _seed_erp(db_session)
    client = _stateful_client()

    first = MoodleSyncService(db_session, client).sync_attendance()
    second = MoodleSyncService(db_session, client).sync_attendance()

    assert first.status == "Success"
    assert second.status == "Success"
    assert "1 written" in first.message
    assert "0 written, 1 already up-to-date" in second.message
    added = [c for c in client.calls if c[0] == "mod_attendance_add_session"]
    submitted = [
        c for c in client.calls if c[0] == "mod_attendance_update_user_status"
    ]
    assert len(added) == 1, "second run must not create a duplicate session"
    assert len(submitted) == 1, "second run must not rewrite the same mark"
    assert not any(
        c[0] == "mod_attendance_add_attendance" for c in client.calls
    )
    # Statuses come from the get_sessions payload, no extra lookup needed.
    assert not any(c[0] == "mod_attendance_get_session" for c in client.calls)


def test_sync_attendance_fails_fast_when_lock_held(db_session, test_engine):
    _seed_erp(db_session)
    conn = _hold_sync_lock(test_engine)
    try:
        client = _success_client()
        log = MoodleSyncService(db_session, client).sync_attendance()
        assert log.status == "Failed"
        assert "already running" in log.message
        assert client.calls == [], "must not touch Moodle while locked"
    finally:
        _release_sync_lock(conn)


def test_sync_students_fails_fast_when_lock_held(db_session, test_engine):
    _seed_erp(db_session)
    conn = _hold_sync_lock(test_engine)
    try:
        client = FakeMoodleClient()
        log = MoodleSyncService(db_session, client).sync_students()
        assert log.status == "Failed"
        assert "already running" in log.message
        assert client.calls == []
    finally:
        _release_sync_lock(conn)


def test_sync_all_raises_when_lock_held(db_session, test_engine):
    _seed_erp(db_session)
    conn = _hold_sync_lock(test_engine)
    try:
        with pytest.raises(SyncInProgressError):
            MoodleSyncService(db_session, _success_client()).sync_all()
    finally:
        _release_sync_lock(conn)


def test_sync_courses_sets_startdate_from_first_attendance(db_session):
    """New courses start at their earliest ERP attendance date, not today."""
    _seed_erp(db_session)
    client = FakeMoodleClient()
    client.response_overrides["core_course_get_courses_by_field"] = {"courses": []}
    client.response_overrides["core_course_create_courses"] = [{"id": 9}]

    log = MoodleSyncService(db_session, client).sync_courses()

    assert log.status == "Success"
    created = [c for c in client.calls if c[0] == "core_course_create_courses"]
    assert len(created) == 1
    # Seeded attendance date is 2025-08-01 -> local midnight in Asia/Kolkata.
    assert created[0][1]["courses[0][startdate]"] == str(IST_MIDNIGHT_2025_08_01)
