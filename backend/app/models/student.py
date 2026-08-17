"""Student model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Student(Base, BaseModelMixin):
    """A student enrolled in a department."""

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("roll_number", name="uq_students_roll_number"),
        UniqueConstraint("email", name="uq_students_email"),
        Index("ix_students_department_id", "department_id"),
        Index("ix_students_semester", "semester"),
    )

    roll_number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", name="fk_students_department_id_departments"),
        nullable=False,
    )
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )

    department: Mapped["Department"] = relationship(back_populates="students")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="student")
    grades: Mapped[list["Grade"]] = relationship(back_populates="student")
