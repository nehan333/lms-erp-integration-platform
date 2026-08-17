"""Attendance model."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Attendance(Base, BaseModelMixin):
    """A single attendance record for a student in a course on a given date."""

    __tablename__ = "attendance"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Present', 'Absent')",
            name="ck_attendance_status",
        ),
        UniqueConstraint(
            "student_id",
            "course_id",
            "date",
            name="uq_attendance_student_course_date",
        ),
        Index("ix_attendance_course_id", "course_id"),
        Index("ix_attendance_date", "date"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", name="fk_attendance_student_id_students"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", name="fk_attendance_course_id_courses"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    student: Mapped["Student"] = relationship(back_populates="attendance")
    course: Mapped["Course"] = relationship(back_populates="attendance")
