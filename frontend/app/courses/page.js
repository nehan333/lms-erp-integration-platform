import Link from "next/link";
import { api } from "@/lib/api";
import DeleteButton from "@/components/DeleteButton";

async function fetchCourses() {
  try {
    return await api.get("/courses?limit=100");
  } catch (err) {
    return { error: err.message };
  }
}

export default async function CoursesPage() {
  const data = await fetchCourses();

  return (
    <>
      <div className="page-title">
        <h1>Courses</h1>
        <p className="subtitle">Courses offered</p>
        <Link href="/courses/new" className="btn">
          + New Course
        </Link>
      </div>

      {data.error && <div className="error">Could not load: {data.error}</div>}

      {!data.error && (
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Credits</th>
              <th>Semester</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((course) => (
              <tr key={course.id}>
                <td>{course.course_code}</td>
                <td>{course.course_name}</td>
                <td>{course.credits}</td>
                <td>{course.semester}</td>
                <td>
                  <div className="actions-cell">
                    <Link href={`/courses/${course.id}/edit`} className="btn btn-secondary">
                      Edit
                    </Link>
                    <DeleteButton path={`/courses/${course.id}`} />
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
