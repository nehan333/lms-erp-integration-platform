import Link from "next/link";
import { api } from "@/lib/api";

async function fetchOverview() {
  try {
    return await api.get("/dashboard/overview");
  } catch (err) {
    return { error: err.message };
  }
}

export default async function HomePage() {
  const overview = await fetchOverview();

  if (overview.error) {
    return (
      <div className="page-title">
        <h1>Dashboard</h1>
        <div className="error">
          Could not reach the ERP API: {overview.error}
        </div>
      </div>
    );
  }

  const stats = [
    { label: "Departments", value: overview.departments },
    { label: "Faculty", value: overview.faculty },
    { label: "Students", value: overview.students },
    { label: "Courses", value: overview.courses },
    { label: "Enrollments", value: overview.enrollments },
    { label: "Grades", value: overview.grades },
    { label: "Attendance Present", value: overview.attendance_present },
    { label: "Attendance Absent", value: overview.attendance_absent },
  ];

  return (
    <>
      <div className="page-title">
        <h1>Dashboard</h1>
        <p className="subtitle">ERP overview statistics</p>
      </div>

      <div className="grid">
        {stats.map((stat) => (
          <div className="stat" key={stat.label}>
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", marginTop: 20 }}>
        <div className="card">
          <h2>Grade Distribution</h2>
          <table>
            <thead>
              <tr>
                <th>Grade</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {overview.grade_distribution.map((row) => (
                <tr key={row.grade}>
                  <td>{row.grade}</td>
                  <td>{row.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>Students by Department</h2>
          <table>
            <thead>
              <tr>
                <th>Department</th>
                <th>Students</th>
              </tr>
            </thead>
            <tbody>
              {overview.students_by_department.map((row) => (
                <tr key={row.department_id}>
                  <td>
                    {row.department_code} — {row.department_name}
                  </td>
                  <td>{row.student_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="muted" style={{ marginTop: 24 }}>
        Manage records under{" "}
        <Link href="/students">Students</Link>,{" "}
        <Link href="/departments">Departments</Link>,{" "}
        <Link href="/faculty">Faculty</Link>, or{" "}
        <Link href="/courses">Courses</Link>. View{" "}
        <Link href="/reports">Reports</Link> or the{" "}
        <Link href="/sync">Moodle Sync</Link> status.
      </p>
    </>
  );
}
