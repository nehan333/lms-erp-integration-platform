"""Enrollment model."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Enrollment(Base, BaseModelMixin):
    """A student enrolled in a course for a given academic year and semester."""

    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            "academic_year",
            "semester",
            name="uq_enrollments_student_course_year_semester",
        ),
        Index("ix_enrollments_course_id", "course_id"),
        Index("ix_enrollments_semester", "semester"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", name="fk_enrollments_student_id_students"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", name="fk_enrollments_course_id_courses"),
        nullable=False,
    )
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
