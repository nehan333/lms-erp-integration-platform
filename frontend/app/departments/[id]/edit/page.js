import { notFound } from "next/navigation";
import EntityForm from "@/components/EntityForm";
import { api } from "@/lib/api";

const fields = [
  { name: "department_code", label: "Department Code", type: "text", required: true },
  { name: "department_name", label: "Department Name", type: "text", required: true },
];

export default async function EditDepartmentPage({ params }) {
  const { id } = await params;
  let department;
  try {
    department = await api.get(`/departments/${id}`);
  } catch {
    notFound();
  }

  return (
    <div className="page-title">
      <h1>Edit Department</h1>
      <div className="card" style={{ marginTop: 16, maxWidth: 480 }}>
        <EntityForm
          fields={fields}
          endpoint={`/departments/${id}`}
          method="PUT"
          initial={{
            department_code: department.department_code,
            department_name: department.department_name,
          }}
        />
      </div>
    </div>
  );
}
