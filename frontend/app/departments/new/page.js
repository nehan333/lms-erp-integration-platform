import EntityForm from "@/components/EntityForm";

const fields = [
  { name: "department_code", label: "Department Code", type: "text", required: true },
  { name: "department_name", label: "Department Name", type: "text", required: true },
];

export default function NewDepartmentPage() {
  return (
    <div className="page-title">
      <h1>New Department</h1>
      <div className="card" style={{ marginTop: 16, maxWidth: 480 }}>
        <EntityForm fields={fields} endpoint="/departments" method="POST" />
      </div>
    </div>
  );
}
