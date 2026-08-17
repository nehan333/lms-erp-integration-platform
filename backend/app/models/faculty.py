"""Faculty model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Faculty(Base, BaseModelMixin):
    """A faculty member who teaches courses in a department."""

    __tablename__ = "faculty"
    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_faculty_employee_id"),
        UniqueConstraint("email", name="uq_faculty_email"),
        Index("ix_faculty_department_id", "department_id"),
    )

    employee_id: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("departments.id", name="fk_faculty_department_id_departments"),
        nullable=False,
    )
    status: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )

    department: Mapped["Department"] = relationship(back_populates="faculty")
    courses: Mapped[list["Course"]] = relationship(back_populates="faculty")
