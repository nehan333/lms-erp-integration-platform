import { api } from "@/lib/api";

async function fetchReports() {
  try {
    const [attendance, enrollments, grades, coursesByDept] = await Promise.all([
      api.get("/reports/attendance-summary"),
      api.get("/reports/enrollments-by-course"),
      api.get("/reports/grade-distribution"),
      api.get("/reports/courses-by-department"),
    ]);
    return { attendance, enrollments, grades, coursesByDept };
  } catch (err) {
    return { error: err.message };
  }
}

export default async function ReportsPage() {
  const data = await fetchReports();

  if (data.error) {
    return (
      <div className="page-title">
        <h1>Reports</h1>
        <div className="error">Could not load reports: {data.error}</div>
      </div>
    );
  }

  const { attendance, enrollments, grades, coursesByDept } = data;

  return (
    <>
      <div className="page-title">
        <h1>Reports</h1>
        <p className="subtitle">Aggregate summaries from the ERP</p>
      </div>

      <div className="card">
        <h2>Attendance Summary</h2>
        <div className="grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
          <div className="stat">
            <div className="stat-value">{attendance.total}</div>
            <div className="stat-label">Total records</div>
          </div>
          <div className="stat">
            <div className="stat-value">{attendance.present}</div>
            <div className="stat-label">Present</div>
          </div>
          <div className="stat">
            <div className="stat-value">{attendance.absent}</div>
            <div className="stat-label">Absent</div>
          </div>
          <div className="stat">
            <div className="stat-value">{attendance.present_percent}%</div>
            <div className="stat-label">Present rate</div>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2>Enrollments by Course</h2>
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Course</th>
              <th>Enrollments</th>
            </tr>
          </thead>
          <tbody>
            {enrollments.map((row) => (
              <tr key={row.course_id}>
                <td>{row.course_code}</td>
                <td>{row.course_name}</td>
                <td>{row.enrollment_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
              {grades.map((row) => (
                <tr key={row.grade}>
                  <td>{row.grade}</td>
                  <td>{row.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>Courses by Department</h2>
          <table>
            <thead>
              <tr>
                <th>Department</th>
                <th>Courses</th>
              </tr>
            </thead>
            <tbody>
              {coursesByDept.map((row) => (
                <tr key={row.department_id}>
                  <td>
                    {row.department_code} — {row.department_name}
                  </td>
                  <td>{row.course_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
