"""Grade model."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Grade(Base, BaseModelMixin):
    """Final grade awarded to a student for a course."""

    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_grades_student_course"),
        Index("ix_grades_course_id", "course_id"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", name="fk_grades_student_id_students"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", name="fk_grades_course_id_courses"),
        nullable=False,
    )
    internal_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    external_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    final_grade: Mapped[str] = mapped_column(String(5), nullable=False)

    student: Mapped["Student"] = relationship(back_populates="grades")
    course: Mapped["Course"] = relationship(back_populates="grades")
