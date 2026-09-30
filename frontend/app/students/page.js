import Link from "next/link";
import { api } from "@/lib/api";
import DeleteButton from "@/components/DeleteButton";

async function fetchStudents() {
  try {
    return await api.get("/students?limit=100");
  } catch (err) {
    return { error: err.message };
  }
}

export default async function StudentsPage() {
  const data = await fetchStudents();

  return (
    <>
      <div className="page-title">
        <h1>Students</h1>
        <p className="subtitle">Enrolled students</p>
        <Link href="/students/new" className="btn">
          + New Student
        </Link>
      </div>

      {data.error && <div className="error">Could not load: {data.error}</div>}

      {!data.error && (
        <table>
          <thead>
            <tr>
              <th>Roll No</th>
              <th>Name</th>
              <th>Email</th>
              <th>Semester</th>
              <th>Section</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((student) => (
              <tr key={student.id}>
                <td>{student.roll_number}</td>
                <td>{student.name}</td>
                <td>{student.email}</td>
                <td>{student.semester}</td>
                <td>{student.section}</td>
                <td>
                  {student.status ? (
                    <span className="badge badge-success">Active</span>
                  ) : (
                    <span className="badge badge-danger">Inactive</span>
                  )}
                </td>
                <td>
                  <div className="actions-cell">
                    <Link href={`/students/${student.id}/edit`} className="btn btn-secondary">
                      Edit
                    </Link>
                    <DeleteButton path={`/students/${student.id}`} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}