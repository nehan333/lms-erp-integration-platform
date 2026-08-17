# Entity Relationship Diagram

## Overview

This diagram describes the ERP database for the LMS–ERP Integration Platform.
The ERP is the source of truth. Moodle data is synchronized from the ERP in a
future sprint and is **not** part of this schema.

See [docs/DATABASE.md](DATABASE.md) for the full column, constraint, and index
specification.

---

## Mermaid ER Diagram

```mermaid
erDiagram
    DEPARTMENT ||--o{ FACULTY : employs
    DEPARTMENT ||--o{ STUDENT : enrolls
    DEPARTMENT ||--o{ COURSE : offers
    FACULTY ||--o{ COURSE : teaches
    STUDENT ||--o{ ENROLLMENT : "enrolls in"
    COURSE ||--o{ ENROLLMENT : "has"
    STUDENT ||--o{ ATTENDANCE : "has attendance"
    COURSE ||--o{ ATTENDANCE : "recorded for"
    STUDENT ||--o{ GRADE : "receives"
    COURSE ||--o{ GRADE : "graded in"

    DEPARTMENT {
        uuid id PK
        varchar department_code UK
        varchar department_name UK
        timestamp created_at
        timestamp updated_at
    }

    FACULTY {
        uuid id PK
        varchar employee_id UK
        varchar name
        varchar email UK
        varchar phone
        varchar designation
        uuid department_id FK
        boolean status
        timestamp created_at
        timestamp updated_at
    }

    STUDENT {
        uuid id PK
        varchar roll_number UK
        varchar name
        varchar email UK
        varchar phone
        uuid department_id FK
        int semester
        varchar section
        boolean status
        timestamp created_at
        timestamp updated_at
    }

    COURSE {
        uuid id PK
        varchar course_code UK
        varchar course_name
        int credits
        int semester
        uuid department_id FK
        uuid faculty_id FK
        timestamp created_at
        timestamp updated_at
    }

    ENROLLMENT {
        uuid id PK
        uuid student_id FK
        uuid course_id FK
        varchar academic_year
        int semester
        timestamp created_at
        timestamp updated_at
    }

    ATTENDANCE {
        uuid id PK
        uuid student_id FK
        uuid course_id FK
        date date
        varchar status
        timestamp created_at
        timestamp updated_at
    }

    GRADE {
        uuid id PK
        uuid student_id FK
        uuid course_id FK
        decimal internal_marks
        decimal external_marks
        varchar final_grade
        timestamp created_at
        timestamp updated_at
    }

    SYNC_LOG {
        uuid id PK
        varchar module
        varchar action
        varchar status
        text message
        timestamp created_at
        timestamp updated_at
    }
```

---

## Cardinality Legend

| Symbol  | Meaning                          |
|---------|----------------------------------|
| `||`    | exactly one                     |
| `o{`    | zero or many                    |
| `o|`    | zero or one                     |
| `{`     | one or many                     |

Examples:

- `DEPARTMENT ||--o{ FACULTY` — a department employs zero or many faculty; each faculty member belongs to exactly one department.
- `STUDENT ||--o{ ENROLLMENT` — a student has zero or many enrollments; each enrollment belongs to exactly one student.
- `COURSE ||--o{ ENROLLMENT` — a course has zero or many enrollments; each enrollment is for exactly one course.

---

## Relationship Summary

| Relationship                          | Type        | Foreign Key                        |
|---------------------------------------|-------------|------------------------------------|
| Department → Faculty                  | 1 : N       | `faculty.department_id`            |
| Department → Student                  | 1 : N       | `students.department_id`           |
| Department → Course                   | 1 : N       | `courses.department_id`            |
| Faculty → Course                      | 1 : N       | `courses.faculty_id` (nullable)    |
| Student ↔ Course (via Enrollment)     | M : N       | `enrollments.student_id`, `enrollments.course_id` |
| Student → Attendance                  | 1 : N       | `attendance.student_id`            |
| Course → Attendance                   | 1 : N       | `attendance.course_id`             |
| Student → Grade                       | 1 : N       | `grades.student_id`                |
| Course → Grade                        | 1 : N       | `grades.course_id`                 |
| Sync Log                              | standalone  | (no foreign keys)                  |

---

## Notes

- `SyncLog` intentionally has no relationships; it records generic synchronization events for any entity type.
- No `users` table exists yet. It will be introduced with the Authentication module in a future sprint.
