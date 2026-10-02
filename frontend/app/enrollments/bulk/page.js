import { api } from "@/lib/api";
import BulkEnrollForm from "@/components/BulkEnrollForm";

async function fetchOptions() {
  try {
    const departments = await api.get("/departments?limit=100");
    return departments.items.map((d) => ({
      value: d.id,
      label: `${d.department_code} — ${d.department_name}`,
    }));
  } catch {
    return [];
  }
}

async function fetchCourses() {
  try {
    const courses = await api.get("/courses?limit=100");
    return courses.items;
  } catch {
    return [];
  }
}

export default async function BulkEnrollPage() {
  const [departments, courses] = await Promise.all([
    fetchOptions(),
    fetchCourses(),
  ]);

  return (
    <div className="page-title">
      <h1>Bulk Enroll</h1>
      <p className="subtitle">
        Enroll every active student of a department cohort into selected
        courses, then sync to Moodle.
      </p>
      <div className="card" style={{ maxWidth: 720 }}>
        {departments.length === 0 && (
          <div className="error">
            Could not load departments. Create a department first.
          </div>
        )}
        <BulkEnrollForm departments={departments} courses={courses} />
      </div>
    </div>
  );
}
