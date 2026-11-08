"""Sprint 7 — Moodle payload builder tests (pure mapping functions)."""

from __future__ import annotations

from app.integrations.moodle import payloads


def test_user_lookup_params():
    assert payloads.user_lookup_params("CS25001") == {
        "field": "username",
        "values[0]": "cs25001",
    }


def test_user_create_params_split_name():
    student = type(
        "S",
        (),
        {
            "roll_number": "CS25001",
            "name": "Jane Doe",
            "email": "j@college.edu",
        },
    )()

    assert payloads.user_create_params(student) == {
        "users[0][username]": "cs25001",
        "users[0][password]": "Nehan@12345",
        "users[0][firstname]": "Jane",
        "users[0][lastname]": "Doe",
        "users[0][email]": "j@college.edu",
    }

def test_user_create_params_single_name():
    student = type("S", (), {"roll_number": "CS1", "name": "Prince", "email": "p@college.edu"})()
    params = payloads.user_create_params(student)
    assert params["users[0][firstname]"] == "Prince"
    assert params["users[0][lastname]"] == "Student"

def test_course_lookup_params():
    assert payloads.course_lookup_params("CS101") == {
        "field": "shortname",
        "value": "CS101",
    }


def test_course_create_params():
    course = type("C", (), {"course_code": "CS101", "course_name": "Data Structures"})()
    assert payloads.course_create_params(course, 3) == {
        "courses[0][fullname]": "Data Structures",
        "courses[0][shortname]": "CS101",
        "courses[0][categoryid]": "3",
    }


def test_enrollment_params():
    assert payloads.enrollment_params(11, 22, 5) == {
        "enrolments[0][roleid]": "5",
        "enrolments[0][userid]": "11",
        "enrolments[0][courseid]": "22",
    }


def test_grade_params():
    rows = [(1, 85.0, "ERP final grade: A"), (2, 70.0, None)]
    params = payloads.grade_params(2, "mod_forum", 3, rows)
    assert params["source"] == "lms-erp"
    assert params["courseid"] == "2"
    assert params["component"] == "mod_forum"
    assert params["activityid"] == "3"
    assert params["itemnumber"] == "0"
    assert params["itemdetails[itemname]"] == "FinalGrade"
    assert params["itemdetails[gradetype]"] == "1"
    assert params["itemdetails[grademin]"] == "0"
    assert params["itemdetails[grademax]"] == "100"
    assert params["grades[0][studentid]"] == "1"
    assert params["grades[0][grade]"] == "85.0"
    assert params["grades[0][str_feedback]"] == "ERP final grade: A"
    assert params["grades[1][studentid]"] == "2"
    assert params["grades[1][grade]"] == "70.0"
    assert "grades[1][str_feedback]" not in params


def test_final_grade_to_points_letters():
    assert payloads.final_grade_to_points("A+") == 90.0
    assert payloads.final_grade_to_points("B+") == 70.0
    assert payloads.final_grade_to_points("F") == 0.0
    assert payloads.final_grade_to_points("  a  ") == 80.0


def test_final_grade_to_points_numeric_passthrough():
    assert payloads.final_grade_to_points("88.5") == 88.5


def test_final_grade_to_points_rejects_unknown():
    import pytest

    with pytest.raises(ValueError):
        payloads.final_grade_to_points("A-")


def test_attendance_instance_params():
    params = payloads.attendance_instance_params(9, "Attendance")
    assert params["courseid"] == "9"
    assert params["name"] == "Attendance"
    assert params["groupmode"] == "0"


def test_attendance_session_params():
    params = payloads.attendance_session_params(
        7, 1753986600, description="ERP 2025-08-01"
    )
    assert params["attendanceid"] == "7"
    assert params["sessiontime"] == "1753986600"
    assert params["description"] == "ERP 2025-08-01"
    assert params["duration"] == "0"
    assert params["groupid"] == "0"
    assert params["addcalendarevent"] == "0"


def test_attendance_status_params():
    params = payloads.attendance_status_params(
        session_id=1, moodle_user_id=4, taken_by_id=3, status_id=5, status_set=0
    )
    assert params["sessionid"] == "1"
    assert params["studentid"] == "4"
    assert params["takenbyid"] == "3"
    assert params["statusid"] == "5"
    assert params["statusset"] == "0"


def test_course_create_params_with_startdate():
    from datetime import date

    course = type("C", (), {"course_code": "CS101", "course_name": "Data Structures"})()
    params = payloads.course_create_params(course, 3, date(2025, 8, 6))
    # 2025-08-06 00:00 Asia/Kolkata == 2025-08-05 18:30 UTC
    assert params["courses[0][startdate]"] == "1754418600"
    assert params["courses[0][shortname]"] == "CS101"


def test_local_midnight_ts_uses_site_timezone():
    from datetime import date

    assert payloads.local_midnight_ts(date(2025, 8, 1)) == 1753986600
