"""Department model."""

from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import BaseModelMixin


class Department(Base, BaseModelMixin):
    """An academic department within the college."""

    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("department_code", name="uq_departments_department_code"),
        UniqueConstraint("department_name", name="uq_departments_department_name"),
    )

    department_code: Mapped[str] = mapped_column(String(10), nullable=False)
    department_name: Mapped[str] = mapped_column(String(100), nullable=False)

    faculty: Mapped[list["Faculty"]] = relationship(back_populates="department")
    students: Mapped[list["Student"]] = relationship(back_populates="department")
    courses: Mapped[list["Course"]] = relationship(back_populates="department")
