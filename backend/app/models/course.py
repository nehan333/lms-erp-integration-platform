"""Course model."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Course(Base, BaseModelMixin):
    """A course offered by a department and taught by a faculty member."""

    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("course_code", name="uq_courses_course_code"),
        Index("ix_courses_department_id", "department_id"),
        Index("ix_courses_faculty_id", "faculty_id"),
        Index("ix_courses_semester", "semester"),
    )

    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    course_name: Mapped[str] = mapped_column(String(150), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", name="fk_courses_department_id_departments"),
        nullable=False,
    )
    faculty_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("faculty.id", name="fk_courses_faculty_id_faculty"),
        nullable=True,
    )

    department: Mapped["Department"] = relationship(back_populates="courses")
    faculty: Mapped[Optional["Faculty"]] = relationship(back_populates="courses")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="course")
    grades: Mapped[list["Grade"]] = relationship(back_populates="course")
