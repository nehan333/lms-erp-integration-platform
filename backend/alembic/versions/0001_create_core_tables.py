"""create core ERP tables

Revision ID: 0001
Revises:
Create Date: 2026-08-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_code", sa.String(length=10), nullable=False),
        sa.Column("department_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.UniqueConstraint("department_code", name="uq_departments_department_code"),
        sa.UniqueConstraint("department_name", name="uq_departments_department_name"),
    )

    op.create_table(
        "faculty",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("designation", sa.String(length=100), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_faculty_department_id_departments",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_faculty"),
        sa.UniqueConstraint("employee_id", name="uq_faculty_employee_id"),
        sa.UniqueConstraint("email", name="uq_faculty_email"),
    )
    op.create_index("ix_faculty_department_id", "faculty", ["department_id"])

    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("roll_number", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("section", sa.String(length=10), nullable=False),
        sa.Column(
            "status",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_students_department_id_departments",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_students"),
        sa.UniqueConstraint("roll_number", name="uq_students_roll_number"),
        sa.UniqueConstraint("email", name="uq_students_email"),
    )
    op.create_index("ix_students_department_id", "students", ["department_id"])
    op.create_index("ix_students_semester", "students", ["semester"])

    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_code", sa.String(length=20), nullable=False),
        sa.Column("course_name", sa.String(length=150), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("faculty_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_courses_department_id_departments",
        ),
        sa.ForeignKeyConstraint(
            ["faculty_id"],
            ["faculty.id"],
            name="fk_courses_faculty_id_faculty",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_courses"),
        sa.UniqueConstraint("course_code", name="uq_courses_course_code"),
    )
    op.create_index("ix_courses_department_id", "courses", ["department_id"])
    op.create_index("ix_courses_faculty_id", "courses", ["faculty_id"])
    op.create_index("ix_courses_semester", "courses", ["semester"])

    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("semester", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name="fk_enrollments_student_id_students",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_enrollments_course_id_courses",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_enrollments"),
        sa.UniqueConstraint(
            "student_id",
            "course_id",
            "academic_year",
            "semester",
            name="uq_enrollments_student_course_year_semester",
        ),
    )
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])
    op.create_index("ix_enrollments_semester", "enrollments", ["semester"])

    op.create_table(
        "attendance",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('Present', 'Absent')",
            name="ck_attendance_status",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name="fk_attendance_student_id_students",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_attendance_course_id_courses",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_attendance"),
        sa.UniqueConstraint(
            "student_id",
            "course_id",
            "date",
            name="uq_attendance_student_course_date",
        ),
    )
    op.create_index("ix_attendance_course_id", "attendance", ["course_id"])
    op.create_index("ix_attendance_date", "attendance", ["date"])

    op.create_table(
        "grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("internal_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("external_marks", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("final_grade", sa.String(length=5), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name="fk_grades_student_id_students",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_grades_course_id_courses",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_grades"),
        sa.UniqueConstraint("student_id", "course_id", name="uq_grades_student_course"),
    )
    op.create_index("ix_grades_course_id", "grades", ["course_id"])

    op.create_table(
        "sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('Success', 'Failed')",
            name="ck_sync_logs_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sync_logs"),
    )
    op.create_index("ix_sync_logs_module", "sync_logs", ["module"])
    op.create_index("ix_sync_logs_status", "sync_logs", ["status"])
    op.create_index("ix_sync_logs_created_at", "sync_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("sync_logs")
    op.drop_table("grades")
    op.drop_table("attendance")
    op.drop_table("enrollments")
    op.drop_table("courses")
    op.drop_table("students")
    op.drop_table("faculty")
    op.drop_table("departments")
