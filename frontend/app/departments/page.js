import Link from "next/link";
import { api } from "@/lib/api";
import DeleteButton from "@/components/DeleteButton";

async function fetchDepartments() {
  try {
    return await api.get("/departments?limit=100");
  } catch (err) {
    return { error: err.message };
  }
}

export default async function DepartmentsPage() {
  const data = await fetchDepartments();

  return (
    <>
      <div className="page-title">
        <h1>Departments</h1>
        <p className="subtitle">Academic departments</p>
        <Link href="/departments/new" className="btn">
          + New Department
        </Link>
      </div>

      {data.error && <div className="error">Could not load: {data.error}</div>}

      {!data.error && (
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((dept) => (
              <tr key={dept.id}>
                <td>{dept.department_code}</td>
                <td>{dept.department_name}</td>
                <td>
                  <div className="actions-cell">
                    <Link href={`/departments/${dept.id}/edit`} className="btn btn-secondary">
                      Edit
                    </Link>
                    <DeleteButton path={`/departments/${dept.id}`} />
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
