"""Populate the ERP database with realistic engineering college sample data.

Run from the ``backend`` directory (the schema must exist first):

    uv run alembic upgrade head
    uv run python -m scripts.seed            # fail if data already exists
    uv run python -m scripts.seed --reset    # truncate all tables and reseed

The seed is deterministic: it uses a fixed random seed so that every run
produces the same data.
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text

from app.db.session import SessionLocal
from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student

DEPARTMENTS = [
    ("CSE", "Computer Science and Engineering"),
    ("ECE", "Electronics and Communication Engineering"),
    ("MECH", "Mechanical Engineering"),
    ("CIVIL", "Civil Engineering"),
    ("EEE", "Electrical and Electronics Engineering"),
]

COURSES = {
    "CSE": [
        ("CS101", "Data Structures", 4, 1),
        ("CS102", "Database Management Systems", 4, 2),
        ("CS201", "Operating Systems", 3, 3),
        ("CS202", "Computer Networks", 3, 4),
    ],
    "ECE": [
        ("EC101", "Digital Electronics", 4, 1),
        ("EC102", "Signals and Systems", 4, 2),
        ("EC201", "Microprocessors", 3, 3),
        ("EC202", "Communication Systems", 3, 4),
    ],
    "MECH": [
        ("ME101", "Engineering Mechanics", 4, 1),
        ("ME102", "Thermodynamics", 4, 2),
        ("ME201", "Fluid Mechanics", 3, 3),
        ("ME202", "Machine Design", 3, 4),
    ],
    "CIVIL": [
        ("CE101", "Engineering Geology", 4, 1),
        ("CE102", "Structural Analysis", 4, 2),
        ("CE201", "Geotechnical Engineering", 3, 3),
        ("CE202", "Transportation Engineering", 3, 4),
    ],
    "EEE": [
        ("EE101", "Electrical Circuits", 4, 1),
        ("EE102", "Electromagnetic Theory", 4, 2),
        ("EE201", "Power Systems", 3, 3),
        ("EE202", "Control Systems", 3, 4),
    ],
}

FIRST_NAMES = [
    "Aarav", "Aditi", "Aisha", "Aman", "Ananya", "Ankit", "Anmol", "Arjun",
    "Aryan", "Asha", "Bhavna", "Chirag", "Deepak", "Dev", "Divya", "Esha",
    "Farhan", "Gaurav", "Harsh", "Ishaan", "Ishita", "Jay", "Karan", "Kavya",
    "Kiran", "Lakshmi", "Manish", "Meera", "Mohan", "Nandini", "Neha", "Nikhil",
    "Nisha", "Pooja", "Pranav", "Priya", "Rahul", "Rakesh", "Ravi", "Ritika",
    "Rohan", "Rohit", "Sakshi", "Sameer", "Sanjay", "Sneha", "Sonia", "Suresh",
    "Tanvi", "Varun",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Singh", "Kumar", "Reddy", "Nair",
    "Iyer", "Rao", "Mehta", "Jain", "Yadav", "Mishra", "Agarwal", "Das",
    "Bose", "Choudhary", "Khan", "Desai",
]

DESIGNATIONS = ["Professor", "Associate Professor", "Assistant Professor"]
SECTIONS = ["A", "B"]

ACADEMIC_YEAR = "2025-2026"

FACULTY_PER_DEPARTMENT = 2
STUDENTS_PER_DEPARTMENT = 10

ATTENDANCE_START = date(2025, 8, 1)
ATTENDANCE_END = date(2025, 11, 30)

TABLES = [
    "sync_logs",
    "grades",
    "attendance",
    "enrollments",
    "courses",
    "students",
    "faculty",
    "departments",
]


def random_phone() -> str:
    return f"+91 9{random.randint(100000000, 999999999)}"


def unique_email(first: str, last: str, domain: str, used: set[str]) -> str:
    base = f"{first.lower()}.{last.lower()}@{domain}"
    email = base
    counter = 1
    while email in used:
        counter += 1
        email = f"{first.lower()}.{last.lower()}{counter}@{domain}"
    used.add(email)
    return email


def create_faculty(session, departments) -> list[Faculty]:
    used_emails: set[str] = set()
    faculty_list: list[Faculty] = []
    for dept in departments.values():
        for _ in range(FACULTY_PER_DEPARTMENT):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            faculty_list.append(
                Faculty(
                    employee_id=f"FAC{len(faculty_list) + 1:03d}",
                    name=f"{first} {last}",
                    email=unique_email(first, last, "college.edu", used_emails),
                    phone=random_phone(),
                    designation=random.choice(DESIGNATIONS),
                    department_id=dept.id,
                    status=True,
                )
            )
    session.add_all(faculty_list)
    session.flush()
    return faculty_list


def create_students(session, departments) -> list[Student]:
    students: list[Student] = []
    for code, dept in departments.items():
        for index in range(STUDENTS_PER_DEPARTMENT):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            admission_year = random.choice([2022, 2023, 2024, 2025])
            roll_number = f"{code}{admission_year % 100:02d}{index + 1:03d}"
            students.append(
                Student(
                    roll_number=roll_number,
                    name=f"{first} {last}",
                    email=f"{roll_number.lower()}@student.college.edu",
                    phone=random_phone(),
                    department_id=dept.id,
                    semester=random.randint(1, 6),
                    section=random.choice(SECTIONS),
                    status=True,
                )
            )
    session.add_all(students)
    session.flush()
    return students


def create_courses(session, departments, faculty_list) -> list[Course]:
    faculty_by_department: dict = {}
    for faculty in faculty_list:
        faculty_by_department.setdefault(faculty.department_id, []).append(faculty)

    courses: list[Course] = []
    for code, dept in departments.items():
        department_faculty = faculty_by_department[dept.id]
        for index, (course_code, course_name, credits, semester) in enumerate(
            COURSES[code]
        ):
            courses.append(
                Course(
                    course_code=course_code,
                    course_name=course_name,
                    credits=credits,
                    semester=semester,
                    department_id=dept.id,
                    faculty_id=department_faculty[index % len(department_faculty)].id,
                )
            )
    session.add_all(courses)
    session.flush()
    return courses


def create_enrollments(session, students, courses) -> list[Enrollment]:
    courses_by_department: dict = {}
    for course in courses:
        courses_by_department.setdefault(course.department_id, []).append(course)

    enrollments: list[Enrollment] = []
    for index, student in enumerate(students):
        department_courses = courses_by_department[student.department_id]
        count = 3 if index < 20 else 2
        for course in random.sample(department_courses, min(count, len(department_courses))):
            enrollments.append(
                Enrollment(
                    student_id=student.id,
                    course_id=course.id,
                    academic_year=ACADEMIC_YEAR,
                    semester=course.semester,
                )
            )
    session.add_all(enrollments)
    session.flush()
    return enrollments


def create_attendance(session, enrollments) -> list[Attendance]:
    weekdays: list[date] = []
    cursor = ATTENDANCE_START
    while cursor <= ATTENDANCE_END:
        if cursor.weekday() < 5:
            weekdays.append(cursor)
        cursor += timedelta(days=1)

    records: list[Attendance] = []
    for index, enrollment in enumerate(enrollments):
        count = 5 if index < 20 else 4
        for day in random.sample(weekdays, count):
            records.append(
                Attendance(
                    student_id=enrollment.student_id,
                    course_id=enrollment.course_id,
                    date=day,
                    status="Present" if random.random() < 0.85 else "Absent",
                )
            )
    session.add_all(records)
    session.flush()
    return records


def final_grade(total: float) -> str:
    if total >= 90:
        return "A+"
    if total >= 80:
        return "A"
    if total >= 70:
        return "B+"
    if total >= 60:
        return "B"
    if total >= 50:
        return "C"
    if total >= 40:
        return "D"
    return "F"


def create_grades(session, enrollments) -> list[Grade]:
    grades: list[Grade] = []
    for enrollment in enrollments:
        internal = Decimal(str(round(random.uniform(10, 40), 2)))
        external = Decimal(str(round(random.uniform(25, 60), 2)))
        grades.append(
            Grade(
                student_id=enrollment.student_id,
                course_id=enrollment.course_id,
                internal_marks=internal,
                external_marks=external,
                final_grade=final_grade(float(internal) + float(external)),
            )
        )
    session.add_all(grades)
    session.flush()
    return grades


def reset_database(session) -> None:
    for table in TABLES:
        session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
    session.commit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the ERP database with realistic sample data."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate all tables before seeding.",
    )
    args = parser.parse_args()

    random.seed(42)
    session = SessionLocal()
    try:
        if args.reset:
            reset_database(session)

        if session.scalar(select(func.count()).select_from(Department)):
            print("Database already contains data. Run with --reset to reseed.")
            sys.exit(0)

        departments = {
            code: Department(department_code=code, department_name=name)
            for code, name in DEPARTMENTS
        }
        session.add_all(departments.values())
        session.flush()

        faculty = create_faculty(session, departments)
        students = create_students(session, departments)
        courses = create_courses(session, departments, faculty)
        enrollments = create_enrollments(session, students, courses)
        attendance = create_attendance(session, enrollments)
        grades = create_grades(session, enrollments)

        session.commit()

        print("Database seeded successfully.")
        print(f"  Departments : {len(departments)}")
        print(f"  Faculty     : {len(faculty)}")
        print(f"  Students    : {len(students)}")
        print(f"  Courses     : {len(courses)}")
        print(f"  Enrollments : {len(enrollments)}")
        print(f"  Attendance  : {len(attendance)}")
        print(f"  Grades      : {len(grades)}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
