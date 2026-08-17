"""ORM model registry.

Importing this module registers every model on ``Base.metadata`` so that
Alembic autogenerate can detect the full schema.
"""

from app.models.attendance import Attendance
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment
from app.models.faculty import Faculty
from app.models.grade import Grade
from app.models.student import Student
from app.models.sync_log import SyncLog

__all__ = [
    "Attendance",
    "Course",
    "Department",
    "Enrollment",
    "Faculty",
    "Grade",
    "Student",
    "SyncLog",
]
