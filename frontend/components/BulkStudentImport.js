"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function BulkStudentImport({ departments }) {
  const [csv, setCsv] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [dryRun, setDryRun] = useState(false);
  const [syncMoodle, setSyncMoodle] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!departmentId) {
      setError("Choose a department.");
      return;
    }
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const body = await api.create("/students/bulk", {
        csv,
        department_id: departmentId,
        dry_run: dryRun,
        sync_moodle: syncMoodle,
      });
      setResult(body);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}

      <label>
        Department
        <select
          required
          value={departmentId}
          onChange={(e) => setDepartmentId(e.target.value)}
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
        CSV (header required: roll_number,name,email,semester,section[,phone])
        <textarea
          required
          rows={10}
          value={csv}
          onChange={(e) => setCsv(e.target.value)}
          placeholder={"roll_number,name,email,semester,section\nCS25001,Ada Lovelace,ada@student.edu,1,A"}
          style={{
            width: "100%",
            padding: "8px 10px",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            fontSize: "0.95rem",
            fontFamily: "monospace",
          }}
        />
      </label>

      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="checkbox"
          checked={dryRun}
          onChange={(e) => setDryRun(e.target.checked)}
          style={{ width: "auto" }}
        />
        Dry run (validate only, import nothing)
      </label>

      <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <input
          type="checkbox"
          checked={syncMoodle}
          onChange={(e) => setSyncMoodle(e.target.checked)}
          style={{ width: "auto" }}
        />
        Sync created students to Moodle
      </label>

      <div className="form-actions">
        <button type="submit" disabled={busy}>
          {busy ? "Importing..." : dryRun ? "Validate" : "Import"}
        </button>
        <Link href="/students" className="btn btn-secondary">
          Cancel
        </Link>
      </div>

      {result && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>Import Result {result.dry_run ? "(dry run)" : ""}</h2>
          <p>
            Total rows: <strong>{result.total}</strong> · Created:{" "}
            <strong className="badge badge-success">{result.created}</strong> ·
            Skipped: <strong>{result.skipped}</strong> · Failed:{" "}
            <strong className="badge badge-danger">{result.failed}</strong>
          </p>
          {result.errors.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {result.errors.map((rowError) => (
                  <tr key={rowError.row}>
                    <td>{rowError.row}</td>
                    <td>{rowError.error}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {result.sync_log && (
            <p className="muted" style={{ marginTop: 12 }}>
              Moodle sync: {result.sync_log.status}
              {result.sync_log.message ? ` — ${result.sync_log.message}` : ""}
            </p>
          )}
          {result.created > 0 && !result.dry_run && (
            <p style={{ marginTop: 12 }}>
              <Link href="/students" className="btn">
                View Students
              </Link>
            </p>
          )}
        </div>
      )}
    </form>
  );
}
