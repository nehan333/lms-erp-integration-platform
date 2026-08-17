# Database Design

## 1. Database Overview

The LMS–ERP Integration Platform uses **PostgreSQL** as its primary database.

The **ERP is the source of truth** for all academic information. Moodle is a downstream system that will be synchronized from the ERP by the Synchronization Engine in a future sprint. **No Moodle-specific data is stored in these tables.**

The schema models the core academic domain:

- Departments
- Faculty
- Students
- Courses
- Enrollments
- Attendance
- Grades
- Sync Logs

All tables use **UUID primary keys**, include `created_at` / `updated_at` audit timestamps, and are normalized to 3NF.

The database is managed with **SQLAlchemy 2.0** (ORM models) and **Alembic** (migrations).

---

## 2. Entity Relationship Overview

```
Department
    │
    ├── Faculty   (1:N)
    ├── Students  (1:N)
    └── Courses   (1:N)
           │
           ├── Enrollments  (Students <-> Courses, M:N)
           ├── Attendance   (per Student per Course per date)
           └── Grades       (per Student per Course)

Sync Logs  (standalone, records Moodle synchronization events)
```

See [docs/ERD.md](ERD.md) for the Mermaid entity relationship diagram.

---

## 3. Tables

### 3.1 departments

| Column          | Type                     | Constraints                          |
|-----------------|--------------------------|--------------------------------------|
| `id`            | UUID                     | Primary Key `pk_departments`         |
| `department_code` | VARCHAR(10)            | Not Null, Unique `uq_departments_department_code` |
| `department_name` | VARCHAR(100)           | Not Null, Unique `uq_departments_department_name` |
| `created_at`    | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`            |
| `updated_at`    | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`            |

---

### 3.2 faculty

| Column        | Type                     | Constraints                                  |
|---------------|--------------------------|----------------------------------------------|
| `id`          | UUID                     | Primary Key `pk_faculty`                     |
| `employee_id` | VARCHAR(20)              | Not Null, Unique `uq_faculty_employee_id`    |
| `name`        | VARCHAR(100)             | Not Null                                     |
| `email`       | VARCHAR(100)             | Not Null, Unique `uq_faculty_email`          |
| `phone`       | VARCHAR(20)              | Nullable                                     |
| `designation` | VARCHAR(100)             | Not Null                                     |
| `department_id` | UUID                   | Not Null, Foreign Key → `departments.id` `fk_faculty_department_id_departments` |
| `status`      | BOOLEAN                  | Not Null, Default `TRUE`                     |
| `created_at`  | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |
| `updated_at`  | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |

---

### 3.3 students

| Column        | Type                     | Constraints                                  |
|---------------|--------------------------|----------------------------------------------|
| `id`          | UUID                     | Primary Key `pk_students`                    |
| `roll_number` | VARCHAR(20)              | Not Null, Unique `uq_students_roll_number`   |
| `name`        | VARCHAR(100)             | Not Null                                     |
| `email`       | VARCHAR(100)             | Not Null, Unique `uq_students_email`         |
| `phone`       | VARCHAR(20)              | Nullable                                     |
| `department_id` | UUID                   | Not Null, Foreign Key → `departments.id` `fk_students_department_id_departments` |
| `semester`    | INTEGER                  | Not Null                                     |
| `section`     | VARCHAR(10)              | Not Null                                     |
| `status`      | BOOLEAN                  | Not Null, Default `TRUE`                     |
| `created_at`  | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |
| `updated_at`  | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |

---

### 3.4 courses

| Column         | Type                     | Constraints                                  |
|----------------|--------------------------|----------------------------------------------|
| `id`           | UUID                     | Primary Key `pk_courses`                     |
| `course_code`  | VARCHAR(20)              | Not Null, Unique `uq_courses_course_code`    |
| `course_name`  | VARCHAR(150)             | Not Null                                     |
| `credits`      | INTEGER                  | Not Null                                     |
| `semester`     | INTEGER                  | Not Null                                     |
| `department_id` | UUID                   | Not Null, Foreign Key → `departments.id` `fk_courses_department_id_departments` |
| `faculty_id`   | UUID                     | Nullable, Foreign Key → `faculty.id` `fk_courses_faculty_id_faculty` |
| `created_at`   | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |
| `updated_at`   | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |

---

### 3.5 enrollments

| Column          | Type                     | Constraints                                |
|-----------------|--------------------------|--------------------------------------------|
| `id`            | UUID                     | Primary Key `pk_enrollments`               |
| `student_id`    | UUID                     | Not Null, Foreign Key → `students.id` `fk_enrollments_student_id_students` |
| `course_id`     | UUID                     | Not Null, Foreign Key → `courses.id` `fk_enrollments_course_id_courses` |
| `academic_year` | VARCHAR(20)              | Not Null                                   |
| `semester`      | INTEGER                  | Not Null                                   |
| `created_at`    | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                  |
| `updated_at`    | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                  |

Unique Constraint `uq_enrollments_student_course_year_semester` on `(student_id, course_id, academic_year, semester)` — a student cannot be enrolled in the same course twice within the same academic year and semester.

---

### 3.6 attendance

| Column      | Type                     | Constraints                                              |
|-------------|--------------------------|----------------------------------------------------------|
| `id`        | UUID                     | Primary Key `pk_attendance`                              |
| `student_id`| UUID                     | Not Null, Foreign Key → `students.id` `fk_attendance_student_id_students` |
| `course_id` | UUID                     | Not Null, Foreign Key → `courses.id` `fk_attendance_course_id_courses` |
| `date`      | DATE                     | Not Null                                                 |
| `status`    | VARCHAR(20)              | Not Null, Check `status IN ('Present', 'Absent')` `ck_attendance_status` |
| `created_at`| TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                                |
| `updated_at`| TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                                |

Unique Constraint `uq_attendance_student_course_date` on `(student_id, course_id, date)` — one attendance record per student, per course, per day.

---

### 3.7 grades

| Column          | Type                     | Constraints                                      |
|-----------------|--------------------------|--------------------------------------------------|
| `id`            | UUID                     | Primary Key `pk_grades`                          |
| `student_id`    | UUID                     | Not Null, Foreign Key → `students.id` `fk_grades_student_id_students` |
| `course_id`     | UUID                     | Not Null, Foreign Key → `courses.id` `fk_grades_course_id_courses` |
| `internal_marks`| DECIMAL(5,2)             | Not Null                                        |
| `external_marks`| DECIMAL(5,2)             | Not Null                                        |
| `final_grade`   | VARCHAR(5)               | Not Null                                        |
| `created_at`    | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                       |
| `updated_at`    | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                       |

Unique Constraint `uq_grades_student_course` on `(student_id, course_id)` — a student receives one final grade per course.

---

### 3.8 sync_logs

| Column       | Type                     | Constraints                                  |
|--------------|--------------------------|----------------------------------------------|
| `id`         | UUID                     | Primary Key `pk_sync_logs`                   |
| `module`     | VARCHAR(50)              | Not Null                                     |
| `action`     | VARCHAR(50)              | Not Null                                     |
| `status`     | VARCHAR(20)              | Not Null, Check `status IN ('Success', 'Failed')` `ck_sync_logs_status` |
| `message`    | TEXT                     | Nullable                                     |
| `created_at` | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |
| `updated_at` | TIMESTAMP WITH TIME ZONE | Not Null, Default `now()`                    |

`sync_logs` has no foreign keys — it records generic synchronization events (module, action, status, message) and intentionally stays decoupled from entity tables.

---

## 4. Relationships & Cardinality

| From       | To         | Cardinality | Through       | Foreign Key              |
|------------|------------|-------------|---------------|--------------------------|
| Department | Faculty    | 1 : N       | —             | `faculty.department_id`  |
| Department | Students   | 1 : N       | —             | `students.department_id` |
| Department | Courses    | 1 : N       | —             | `courses.department_id`  |
| Faculty    | Courses    | 1 : N       | —             | `courses.faculty_id`     |
| Students   | Courses    | M : N       | `enrollments` | `enrollments.student_id`, `enrollments.course_id` |
| Students   | Attendance | 1 : N       | —             | `attendance.student_id`  |
| Courses    | Attendance | 1 : N       | —             | `attendance.course_id`   |
| Students   | Grades     | 1 : N       | —             | `grades.student_id`      |
| Courses    | Grades     | 1 : N       | —             | `grades.course_id`       |

**Cardinality rationale**

- **Department 1:N Faculty / Students / Courses** — every faculty member, student, and course belongs to exactly one department. A department may have many of each.
- **Faculty 1:N Courses** — a course has at most one primary instructor. The `faculty_id` on `courses` is **nullable** so a course can exist before an instructor is assigned.
- **Students M:N Courses via Enrollments** — a student can enroll in many courses and a course can have many students. The join is modeled with the `enrollments` table, which also stores the `academic_year` and `semester` for which the enrollment is valid.
- **Students/Courses 1:N Attendance and Grades** — attendance and grades are child records of the student–course pair.

---

## 5. Index Recommendations

Indexes are implemented in the migration. Additional recommendation notes:

| Table         | Index                                          | Purpose                                             |
|---------------|------------------------------------------------|-----------------------------------------------------|
| `faculty`     | `ix_faculty_department_id` (department_id)     | List faculty by department                          |
| `students`    | `ix_students_department_id` (department_id)    | List students by department                         |
| `students`    | `ix_students_semester` (semester)              | Filter students by current semester                 |
| `courses`     | `ix_courses_department_id` (department_id)     | List courses by department                          |
| `courses`     | `ix_courses_faculty_id` (faculty_id)           | List courses taught by a faculty member             |
| `courses`     | `ix_courses_semester` (semester)               | Filter courses by semester                          |
| `enrollments` | `ix_enrollments_course_id` (course_id)         | List all students enrolled in a course              |
| `enrollments` | `ix_enrollments_semester` (semester)           | Filter enrollments by semester                      |
| `attendance`  | `ix_attendance_course_id` (course_id)          | Attendance report for a course                      |
| `attendance`  | `ix_attendance_date` (date)                    | Attendance for a specific date                      |
| `grades`      | `ix_grades_course_id` (course_id)              | Grade report for a course                           |
| `sync_logs`   | `ix_sync_logs_module`, `ix_sync_logs_status`, `ix_sync_logs_created_at` | Query synchronization history by module, status, or time |

Notes

- `students.roll_number`, `students.email`, `faculty.employee_id`, `faculty.email`, `courses.course_code`, `departments.department_code`, and `departments.department_name` are backed by unique indexes created from their unique constraints.
- Lookups by `students.id` and `courses.id` are covered by the primary keys. Lookups by `enrollments.student_id`, `attendance.student_id`, and `grades.student_id` are covered by the leading column of their unique constraints.

---

## 6. Normalization

The schema is normalized to **Third Normal Form (3NF)**.

- **1NF** — Every column holds atomic values (e.g., a student's name is a single string; attendance status is a single value). There are no repeating groups or arrays.
- **2NF** — Every non-key column depends on the **entire** primary key. Tables use surrogate UUID primary keys, so there are no partial-key dependencies. For example, `enrollments.academic_year` depends on the whole enrollment row, not on just `student_id` or just `course_id`.
- **3NF** — No transitive dependencies. Faculty, student, and course details are stored once in their own tables and referenced by foreign keys (`department_id`, `faculty_id`, `student_id`, `course_id`). Derived values such as `final_grade` are stored on `grades` as business data, not recomputed from other tables.

The Many-to-Many `students ↔ courses` relationship is decomposed into the `enrollments` association table, which is the standard 3NF treatment of a many-to-many relationship with its own attributes (`academic_year`, `semester`).

---

## 7. Database Design Decisions

1. **ERP as source of truth.** The schema contains only ERP domain data. No Moodle identifiers or Moodle-specific columns are stored. Synchronization state is captured separately in `sync_logs`.

2. **UUID primary keys.** UUIDs avoid enumeration of records, work across distributed/synchronized systems, and never collide. They are generated in Python (`uuid.uuid4`) with PostgreSQL native `UUID` columns.

3. **No `users` table in this sprint.** Authentication is a future sprint. Login accounts will be designed when the Authentication module is implemented; students and faculty carry their own contact data here.

4. **`status` as BOOLEAN.** Faculty and student records are soft-deactivated via `status` instead of being deleted, preserving academic history.

5. **Grades reference students and courses directly.** Grades intentionally follow the draft design (internal + external marks plus a final grade) and reference `student_id`/`course_id`, with a unique constraint allowing one final grade per student–course pair. If a student repeats a course, an additional grade-bearing semester column can be introduced in a future migration.

6. **Attendance uniqueness.** The `(student_id, course_id, date)` unique constraint prevents duplicate attendance marks while allowing multiple attendance dates per course.

7. **Check constraints over enums.** Attendance status and sync status use `VARCHAR` columns with check constraints rather than PostgreSQL enum types. This keeps migrations simple and avoids `ALTER TYPE` complexity when allowed values change.

8. **Uniform audit timestamps.** Every table has `created_at` and `updated_at` (`TIMESTAMP WITH TIME ZONE`, default `now()`). `updated_at` is refreshed by SQLAlchemy's `onupdate` on writes.

9. **Explicitly named constraints and indexes.** Every primary key, foreign key, unique constraint, check constraint, and index has an explicit, deterministic name (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`), making schema review and future Alembic autogenerate diffs stable.

10. **`sync_logs` intentionally decoupled.** It has no foreign keys so the synchronization engine can log events for any entity type without schema changes.

---

## 8. Seed Data

The seed script (`backend/scripts/seed.py`) populates:

| Table         | Rows |
|---------------|------|
| departments   | 5    |
| faculty       | 10   |
| students      | 50   |
| courses       | 20   |
| enrollments   | 120  |
| attendance    | 500  |
| grades        | 120  |

`sync_logs` is left empty — it is populated by the Synchronization Engine in a future sprint.

---

## 9. Future Notes

- The `users` table will be introduced with the Authentication module.
- The Synchronization Engine will write to `sync_logs` and will map ERP records to Moodle in future sprints.
- Retake/reexam handling may require a semester-aware grade model.
