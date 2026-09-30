import { notFound } from "next/navigation";
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

export default async function EditFacultyPage({ params }) {
  const { id } = await params;
  let faculty;
  try {
    faculty = await api.get(`/faculty/${id}`);
  } catch {
    notFound();
  }
  const departmentOptions = await fetchOptions();

  const fields = [
    { name: "employee_id", label: "Employee ID", type: "text", required: true },
    { name: "name", label: "Name", type: "text", required: true },
    { name: "email", label: "Email", type: "email", required: true },
    { name: "phone", label: "Phone", type: "text", required: false },
    { name: "designation", label: "Designation", type: "text", required: true },
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
      <h1>Edit Faculty</h1>
      <div className="card" style={{ marginTop: 16, maxWidth: 520 }}>
        <EntityForm
          fields={fields}
          endpoint={`/faculty/${id}`}
          method="PUT"
          initial={{
            employee_id: faculty.employee_id,
            name: faculty.name,
            email: faculty.email,
            phone: faculty.phone || "",
            designation: faculty.designation,
            department_id: faculty.department_id,
          }}
        />
      </div>
    </div>
  );
}
