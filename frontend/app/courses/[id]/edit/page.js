import { notFound } from "next/navigation";
import EntityForm from "@/components/EntityForm";
import { api } from "@/lib/api";

async function fetchOptions() {
  const [departments, faculty] = await Promise.all([
    api.get("/departments?limit=100").catch(() => ({ items: [] })),
    api.get("/faculty?limit=100").catch(() => ({ items: [] })),
  ]);
  return {
    departmentOptions: departments.items.map((d) => ({
      value: d.id,
      label: `${d.department_code} — ${d.department_name}`,
    })),
    facultyOptions: faculty.items.map((f) => ({
      value: f.id,
      label: `${f.employee_id} — ${f.name}`,
    })),
  };
}

export default async function EditCoursePage({ params }) {
  const { id } = await params;
  let course;
  try {
    course = await api.get(`/courses/${id}`);
  } catch {
    notFound();
  }
  const { departmentOptions, facultyOptions } = await fetchOptions();

  const fields = [
    { name: "course_code", label: "Course Code", type: "text", required: true },
    { name: "course_name", label: "Course Name", type: "text", required: true },
    { name: "credits", label: "Credits", type: "number", required: true, min: 1, max: 10 },
    { name: "semester", label: "Semester", type: "number", required: true, min: 1, max: 10 },
    {
      name: "department_id",
      label: "Department",
      type: "select",
      required: true,
      options: departmentOptions,
    },
    {
      name: "faculty_id",
      label: "Faculty (optional)",
      type: "select",
      required: false,
      options: facultyOptions,
    },
  ];

  return (
    <div className="page-title">
      <h1>Edit Course</h1>
      <div className="card" style={{ marginTop: 16, maxWidth: 520 }}>
        <EntityForm
          fields={fields}
          endpoint={`/courses/${id}`}
          method="PUT"
          initial={{
            course_code: course.course_code,
            course_name: course.course_name,
            credits: course.credits,
            semester: course.semester,
            department_id: course.department_id,
            faculty_id: course.faculty_id || "",
          }}
        />
      </div>
    </div>
  );
}