"""Payload builders mapping ERP records to Moodle Web Services request params.

These are pure functions (no I/O) so they are trivially unit-testable. Moodle
REST uses the ``param[i][field]`` convention for repeated structures.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.models.course import Course
from app.models.student import Student


def local_midnight_ts(day: date) -> int:
    """Unix timestamp of local midnight for ``day`` in the Moodle site TZ.

    Moodle interprets course/session timestamps in the site timezone, so all
    values we send are computed in ``MOODLE_SITE_TIMEZONE`` instead of the
    host process timezone.
    """
    tz = ZoneInfo(settings.MOODLE_SITE_TIMEZONE)
    return int(datetime.combine(day, time.min, tzinfo=tz).timestamp())


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    if not parts:
        return "", "Student"
    return parts[0], parts[1] if len(parts) > 1 else "Student"

def user_lookup_params(roll_number: str) -> dict[str, Any]:
    """Lookup a Moodle user by ERP roll number (mapped to lowercase username)."""
    return {
        "field": "username",
        "values[0]": roll_number.lower(),
    }


def user_create_params(student: Student) -> dict[str, Any]:
    """Create a Moodle user for an ERP student (``core_user_create_users``)."""
    firstname, lastname = _split_name(student.name)
    return {
        "users[0][username]": student.roll_number.lower(),
        "users[0][password]": settings.MOODLE_DEFAULT_PASSWORD,
        "users[0][firstname]": firstname,
        "users[0][lastname]": lastname,
        "users[0][email]": student.email,
    }



def course_lookup_params(course_code: str) -> dict[str, Any]:
    """Lookup a Moodle course by ERP course code (mapped to shortname)."""
    return {"field": "shortname", "value": course_code}


def course_create_params(
    course: Course, category_id: int, startdate: date | None = None
) -> dict[str, Any]:
    """Create a Moodle course from an ERP course (``core_course_create_courses``).

    ``startdate`` anchors the course's start date to the first ERP attendance
    record of that course (local midnight in the site timezone). Without it
    Moodle defaults to the creation date, and the attendance plugin's
    "This course" student view then hides every earlier session
    (``sessdate >= course.startdate``).
    """
    params: dict[str, Any] = {
        "courses[0][fullname]": course.course_name,
        "courses[0][shortname]": course.course_code,
        "courses[0][categoryid]": str(category_id),
    }
    if startdate is not None:
        params["courses[0][startdate]"] = str(local_midnight_ts(startdate))
    return params


def enrollment_params(
    moodle_user_id: int, moodle_course_id: int, role_id: int
) -> dict[str, Any]:
    """Enrol a Moodle user in a Moodle course (``enrol_manual_enrol_users``)."""
    return {
        "enrolments[0][roleid]": str(role_id),
        "enrolments[0][userid]": str(moodle_user_id),
        "enrolments[0][courseid]": str(moodle_course_id),
    }


def grade_params(
    moodle_course_id: int,
    component: str,
    activityid: int,
    rows: list[tuple[int, float, str | None]],
    itemname: str = "FinalGrade",
) -> dict[str, Any]:
    """Push final grades for one course (``core_grades_update_grades``).

    ``core_grades_update_grades`` (Moodle 5.0) requires ``source``, ``courseid``,
    ``component`` (e.g. ``mod_forum``), ``activityid`` (course module id),
    ``itemnumber`` and numeric ``grades[i][grade]`` values. Moodle creates the
    grade item when it does not exist yet (via ``itemdetails``) and returns an
    integer status flag (0 = GRADE_UPDATE_OK).
    """
    params: dict[str, Any] = {
        "source": "lms-erp",
        "courseid": str(moodle_course_id),
        "component": component,
        "activityid": str(activityid),
        "itemnumber": "0",
        "itemdetails[itemname]": itemname,
        "itemdetails[gradetype]": "1",
        "itemdetails[grademin]": "0",
        "itemdetails[grademax]": "100",
    }
    for index, (moodle_user_id, grade, feedback) in enumerate(rows):
        params[f"grades[{index}][studentid]"] = str(moodle_user_id)
        params[f"grades[{index}][grade]"] = str(grade)
        if feedback:
            params[f"grades[{index}][str_feedback]"] = feedback
    return params


# ERP letter grades -> points on the 0-100 scale (lower bound of the band that
# grants the letter, see scripts/seed.py::final_grade).
GRADE_LETTER_POINTS: dict[str, float] = {
    "A+": 90.0,
    "A": 80.0,
    "B+": 70.0,
    "B": 60.0,
    "C": 50.0,
    "D": 40.0,
    "F": 0.0,
}


def final_grade_to_points(final_grade: str) -> float:
    """Convert an ERP ``final_grade`` into a numeric Moodle grade (0-100).

    Numeric values pass through unchanged. Letter grades map to the lower
    bound of the ERP grading band. Raises ``ValueError`` for unknown formats so
    callers can record an honest failure instead of pushing garbage.
    """
    raw = final_grade.strip()
    try:
        return float(raw)
    except ValueError:
        pass
    key = raw.upper()
    if key in GRADE_LETTER_POINTS:
        return GRADE_LETTER_POINTS[key]
    raise ValueError(f"Unsupported final_grade '{final_grade}'")


def attendance_instance_params(course_id: int, name: str = "Attendance") -> dict[str, Any]:
    """Create an attendance activity in a Moodle course (``mod_attendance_add_attendance``)."""
    return {
        "courseid": str(course_id),
        "name": name,
        "groupmode": "0",
    }


def attendance_session_params(
    attendance_id: int, sessiontime: int, description: str = ""
) -> dict[str, Any]:
    """Create a session on an attendance instance (``mod_attendance_add_session``).

    ``sessiontime`` is the unix timestamp of local midnight for the ERP
    attendance date in ``MOODLE_SITE_TIMEZONE``. ``groupid`` 0 matches the
    instance created with ``groupmode`` 0.
    """
    return {
        "attendanceid": str(attendance_id),
        "description": description,
        "sessiontime": str(sessiontime),
        "duration": "0",
        "groupid": "0",
        "addcalendarevent": "0",
    }


def attendance_status_params(
    session_id: int,
    moodle_user_id: int,
    taken_by_id: int,
    status_id: int,
    status_set: int,
) -> dict[str, Any]:
    """Record one student's attendance (``mod_attendance_update_user_status``).

    Moodle matches on (sessionid, studentid), so repeated synchronization
    updates the existing log row instead of duplicating it.
    """
    return {
        "sessionid": str(session_id),
        "studentid": str(moodle_user_id),
        "takenbyid": str(taken_by_id),
        "statusid": str(status_id),
        "statusset": str(status_set),
    }
