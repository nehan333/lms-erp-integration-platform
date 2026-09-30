import Link from "next/link";
import { api } from "@/lib/api";
import DeleteButton from "@/components/DeleteButton";

async function fetchFaculty() {
  try {
    return await api.get("/faculty?limit=100");
  } catch (err) {
    return { error: err.message };
  }
}

export default async function FacultyPage() {
  const data = await fetchFaculty();

  return (
    <>
      <div className="page-title">
        <h1>Faculty</h1>
        <p className="subtitle">Faculty members</p>
        <Link href="/faculty/new" className="btn">
          + New Faculty
        </Link>
      </div>

      {data.error && <div className="error">Could not load: {data.error}</div>}

      {!data.error && (
        <table>
          <thead>
            <tr>
              <th>Employee ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Designation</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((fac) => (
              <tr key={fac.id}>
                <td>{fac.employee_id}</td>
                <td>{fac.name}</td>
                <td>{fac.email}</td>
                <td>{fac.designation}</td>
                <td>
                  {fac.status ? (
                    <span className="badge badge-success">Active</span>
                  ) : (
                    <span className="badge badge-danger">Inactive</span>
                  )}
                </td>
                <td>
                  <div className="actions-cell">
                    <Link href={`/faculty/${fac.id}/edit`} className="btn btn-secondary">
                      Edit
                    </Link>
                    <DeleteButton path={`/faculty/${fac.id}`} />
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
