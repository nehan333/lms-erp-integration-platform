"""Sprint 7 — Moodle payload builder tests (pure mapping functions)."""

from __future__ import annotations

from datetime import date

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
    params = payloads.grade_params("CS101", [(1, "A"), (2, "B+")])
    assert params["sourceidnumber"] == "CS101"
    assert params["gradeitemname"] == "Final Grade"
    assert params["grades[0][studentid]"] == "1"
    assert params["grades[0][str_grade]"] == "A"
    assert params["grades[1][studentid]"] == "2"
    assert params["grades[1][str_grade]"] == "B+"


def test_attendance_params():
    record = type(
        "A",
        (),
        {"date": date(2025, 8, 1), "status": "Present"},
    )()
    params = payloads.attendance_params(7, 9, record)
    assert params["courseid"] == "9"
    assert params["userid"] == "7"
    assert params["status"] == "Present"
    assert params["timetaken"] == "1753986600"
    assert params["timetaken"].isdigit()
