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

export default async function EditStudentPage({ params }) {
  const { id } = await params;
  let student;
  try {
    student = await api.get(`/students/${id}`);
  } catch {
    notFound();
  }
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
      <h1>Edit Student</h1>
      <div className="card" style={{ marginTop: 16, maxWidth: 520 }}>
        <EntityForm
          fields={fields}
          endpoint={`/students/${id}`}
          method="PUT"
          initial={{
            roll_number: student.roll_number,
            name: student.name,
            email: student.email,
            phone: student.phone || "",
            semester: student.semester,
            section: student.section,
            department_id: student.department_id,
          }}
        />
      </div>
    </div>
  );
}