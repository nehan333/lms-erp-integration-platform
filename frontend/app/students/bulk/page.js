import { api } from "@/lib/api";
import BulkStudentImport from "@/components/BulkStudentImport";

async function fetchDepartmentOptions() {
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

export default async function BulkStudentImportPage() {
  const departments = await fetchDepartmentOptions();

  return (
    <div className="page-title">
      <h1>Bulk Student Import</h1>
      <p className="subtitle">
        Paste CSV rows to create many students at once, optionally syncing them
        to Moodle.
      </p>
      <div className="card" style={{ maxWidth: 720 }}>
        {departments.length === 0 && (
          <div className="error">
            Could not load departments. Create a department first.
          </div>
        )}
        <BulkStudentImport departments={departments} />
      </div>
    </div>
  );
}
