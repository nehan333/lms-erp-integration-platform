import Link from "next/link";
import { api } from "@/lib/api";
import DeleteButton from "@/components/DeleteButton";

async function fetchEnrollments() {
  try {
    return await api.get("/enrollments?limit=100");
  } catch (err) {
    return { error: err.message };
  }
}

async function fetchNameMaps() {
  const maps = { students: {}, courses: {} };
  try {
    const students = await api.get("/students?limit=100");
    for (const s of students.items) {
      maps.students[s.id] = `${s.name} (${s.roll_number})`;
    }
  } catch {
    // leave empty; ids are shown as a fallback
  }
  try {
    const courses = await api.get("/courses?limit=100");
    for (const c of courses.items) {
      maps.courses[c.id] = `${c.course_code} — ${c.course_name}`;
    }
  } catch {
    // leave empty; ids are shown as a fallback
  }
  return maps;
}

function shortId(id) {
  return id.slice(0, 8);
}

export default async function EnrollmentsPage() {
  const [data, maps] = await Promise.all([fetchEnrollments(), fetchNameMaps()]);

  return (
    <>
      <div className="page-title">
        <h1>Enrollments</h1>
        <p className="subtitle">
          Student course enrollments across academic years
        </p>
        <Link href="/enrollments/bulk" className="btn">
          + Bulk Enroll
        </Link>
      </div>

      {data.error && <div className="error">Could not load: {data.error}</div>}

      {!data.error && data.items.length === 0 && (
        <p className="muted">No enrollments yet.</p>
      )}

      {!data.error && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Student</th>
              <th>Course</th>
              <th>Academic Year</th>
              <th>Semester</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((enrollment) => (
              <tr key={enrollment.id}>
                <td>
                  {maps.students[enrollment.student_id] ? (
                    <Link href={`/students/${enrollment.student_id}`}>
                      {maps.students[enrollment.student_id]}
                    </Link>
                  ) : (
                    <span className="muted">{shortId(enrollment.student_id)}</span>
                  )}
                </td>
                <td>
                  {maps.courses[enrollment.course_id] ?? (
                    <span className="muted">{shortId(enrollment.course_id)}</span>
                  )}
                </td>
                <td>{enrollment.academic_year}</td>
                <td>{enrollment.semester}</td>
                <td>
                  <DeleteButton path={`/enrollments/${enrollment.id}`} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
