import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import DeleteButton from "@/components/DeleteButton";

async function fetchStudent(id) {
  try {
    return await api.get(`/students/${id}`);
  } catch {
    return null;
  }
}

async function fetchAttendance(id) {
  try {
    return await api.get(`/students/${id}/attendance-summary`);
  } catch {
    return null;
  }
}

function formatPercentage(value) {
  if (value === null || value === undefined) {
    return "—";
  }
  return `${value}%`;
}

export default async function StudentDetailPage({ params }) {
  const { id } = await params;
  const student = await fetchStudent(id);
  if (!student) {
    notFound();
  }
  const summary = await fetchAttendance(id);

  return (
    <>
      <div className="page-title">
        <h1>{student.name}</h1>
        <p className="subtitle">
          {student.roll_number} · Semester {student.semester} · Section{" "}
          {student.section}
        </p>
        <div className="actions-cell">
          <Link href={`/students/${student.id}/edit`} className="btn btn-secondary">
            Edit
          </Link>
          <DeleteButton path={`/students/${student.id}`} />
          <Link href="/students" className="btn btn-secondary">
            Back
          </Link>
        </div>
      </div>

      <div className="grid" style={{ marginBottom: 20 }}>
        <div className="stat">
          <div className="stat-value">
            {student.status ? (
              <span className="badge badge-success">Active</span>
            ) : (
              <span className="badge badge-danger">Inactive</span>
            )}
          </div>
          <div className="stat-label">Status</div>
        </div>
        <div className="stat">
          <div className="stat-value">{formatPercentage(summary?.percentage)}</div>
          <div className="stat-label">
            Attendance ({summary?.present ?? 0} / {summary?.total ?? 0})
          </div>
        </div>
        <div className="stat">
          <div className="stat-value">{summary?.courses?.length ?? 0}</div>
          <div className="stat-label">Courses with attendance</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <h2>Contact</h2>
        <p>
          <strong>Email:</strong> {student.email}
        </p>
        <p>
          <strong>Phone:</strong> {student.phone || "—"}
        </p>
        <p className="muted">
          Department ID: {student.department_id}
        </p>
      </div>

      <div className="card">
        <h2>Attendance by Course</h2>
        {summary === null && (
          <div className="error">Could not load attendance summary.</div>
        )}
        {summary && summary.courses.length === 0 && (
          <p className="muted">No attendance recorded yet.</p>
        )}
        {summary && summary.courses.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Course Code</th>
                <th>Course Name</th>
                <th>Present</th>
                <th>Total</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {summary.courses.map((course) => (
                <tr key={course.course_id}>
                  <td>{course.course_code}</td>
                  <td>{course.course_name}</td>
                  <td>{course.present}</td>
                  <td>{course.total}</td>
                  <td>
                    {course.percentage === null ? (
                      <span className="muted">—</span>
                    ) : course.percentage >= 75 ? (
                      <span className="badge badge-success">
                        {course.percentage}%
                      </span>
                    ) : (
                      <span className="badge badge-danger">
                        {course.percentage}%
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
