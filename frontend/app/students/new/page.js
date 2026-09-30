import EntityForm from "@/components/EntityForm";
import { api } from "@/lib/api";

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

export default async function NewStudentPage() {
  const departmentOptions = await fetchOptions();

  const fields = [
    { name: "roll_number", label: "Roll Number", type: "text", required: true },
    { name: "name", label: "Name", type: "text", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "phone", label: "Phone", type: "text", required: false },
    { name: "semester", label: "Semester", type: "number", required: true, min: 1, max: 10 },
    { name: "section", label: "Section", type: "text", required: true },
    {
      name: "department_id",
      label: "Department",
      type: "select",
      required: true,
      options: departmentOptions,
    },
  ];

  return (
    <div className="page-title">
      <h1>New Student</h1>
      <div className="card" style={{ marginTop: 16, maxWidth: 520 }}>
        <EntityForm fields={fields} endpoint="/students" method="POST" />
      </div>
    </div>
  );
}