"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function BulkEnrollForm({ departments, courses }) {
  const [departmentId, setDepartmentId] = useState("");
  const [semester, setSemester] = useState("1");
  const [academicYear, setAcademicYear] = useState("");
  const [courseIds, setCourseIds] = useState([]);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const payload = {
    department_id: departmentId,
    semester: Number(semester),
    academic_year: academicYear,
    course_ids: courseIds,
  };

  const deptCourses = courses.filter((c) => c.department_id === departmentId);

  function toggleCourse(id) {
    setCourseIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
    setPreview(null);
  }

  function reset() {
    setPreview(null);
    setResult(null);
    setError(null);
  }

  async function handlePreview(event) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      setPreview(await api.create("/enrollments/bulk/preview", payload));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm() {
    setBusy(true);
    setError(null);
    try {
      setResult(await api.create("/enrollments/bulk", payload));
      setPreview(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <div>
        <div className="success">
          Enrolled <strong>{result.created}</strong> of{" "}
          <strong>{result.students_total * result.courses.length}</strong>{" "}
          possible enrollments ({result.skipped} already enrolled).
        </div>
        <table>
          <thead>
            <tr>
              <th>Course</th>
              <th>Created</th>
              <th>Skipped</th>
            </tr>
          </thead>
          <tbody>
            {result.courses.map((course) => (
              <tr key={course.course_id}>
                <td>
                  {course.course_code}
                </td>
                <td>
                  <span className="badge badge-success">{course.created}</span>
                </td>
                <td>{course.skipped}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {result.sync_log && (
          <p className="muted" style={{ marginTop: 12 }}>
            Moodle sync: {result.sync_log.status}
            {result.sync_log.message ? ` — ${result.sync_log.message}` : ""}
          </p>
        )}
        <div className="form-actions">
          <Link href="/enrollments" className="btn">
            View Enrollments
          </Link>
          <button type="button" className="btn-secondary" onClick={reset}>
            Enroll Another Cohort
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handlePreview}>
      {error && <div className="error">{error}</div>}

      <label>
        Department
        <select
          required
          value={departmentId}
          onChange={(e) => {
            setDepartmentId(e.target.value);
            setCourseIds([]);
            reset();
          }}
        >
          <option value="">-- Select --</option>
          {departments.map((dept) => (
            <option key={dept.value} value={dept.value}>
              {dept.label}
            </option>
          ))}
        </select>
      </label>

      <label>
        Semester
        <input
          type="number"
          min={1}
          max={10}
          required
          value={semester}
          onChange={(e) => {
            setSemester(e.target.value);
            reset();
          }}
        />
      </label>

      <label>
        Academic Year (e.g. 2025-26)
        <input
          type="text"
          required
          value={academicYear}
          onChange={(e) => {
            setAcademicYear(e.target.value);
            reset();
          }}
          placeholder="2025-26"
        />
      </label>

      <label>Courses</label>
      {departmentId === "" && (
        <p className="muted">Select a department to see its courses.</p>
      )}
      {departmentId !== "" && deptCourses.length === 0 && (
        <p className="muted">No courses in this department yet.</p>
      )}
      {deptCourses.map((course) => (
        <label
          key={course.id}
          style={{ display: "flex", alignItems: "center", gap: 8 }}
        >
          <input
            type="checkbox"
            checked={courseIds.includes(course.id)}
            onChange={() => toggleCourse(course.id)}
            style={{ width: "auto" }}
          />
          {course.course_code} — {course.course_name} (sem {course.semester})
        </label>
      ))}

      <div className="form-actions">
        <button type="submit" disabled={busy || courseIds.length === 0}>
          {busy ? "Working..." : "Preview"}
        </button>
        <Link href="/enrollments" className="btn btn-secondary">
          Cancel
        </Link>
      </div>

      {preview && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>Preview — nothing has been saved</h2>
          <p>
            {preview.students_total} active students in this cohort will be
            enrolled in {preview.courses.length} course(s).
          </p>
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>To Create</th>
                <th>Already Enrolled</th>
              </tr>
            </thead>
            <tbody>
              {preview.courses.map((course) => (
                <tr key={course.course_id}>
                  <td>
                    {course.course_code} — {course.course_name}
                  </td>
                  <td>
                    <span className="badge badge-success">{course.to_create}</span>
                  </td>
                  <td>{course.already_enrolled}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ marginTop: 12 }}>
            Total new enrollments: <strong>{preview.total_to_create}</strong>
            {preview.total_already_enrolled > 0 &&
              ` · ${preview.total_already_enrolled} already enrolled (skipped)`}
          </p>
          <div className="form-actions">
            <button
              type="button"
              onClick={handleConfirm}
              disabled={busy || preview.total_to_create === 0}
            >
              {busy ? "Enrolling..." : "Confirm & Sync to Moodle"}
            </button>
            <button type="button" className="btn-secondary" onClick={reset}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </form>
  );
}
