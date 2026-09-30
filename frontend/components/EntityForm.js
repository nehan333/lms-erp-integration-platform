"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

// Generic create/edit form.
//   fields: [{ name, label, type, required, options: [{value,label}] }]
//   endpoint: base path, e.g. "/departments" or "/departments/{id}"
//   method: "POST" (create) or "PUT" (update)
//   initial: values for edit mode
export default function EntityForm({ fields, endpoint, method, initial }) {
  const router = useRouter();
  const [values, setValues] = useState(initial || {});
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function setValue(name, value) {
    setValues((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {};
      for (const [key, value] of Object.entries(values)) {
        // Omit empty optional fields so the backend applies defaults / leaves them unchanged.
        if (value === "" || value === undefined) {
          continue;
        }
        payload[key] = value;
      }
      if (method === "PUT") {
        await api.update(endpoint, payload);
      } else {
        await api.create(endpoint, payload);
      }
      router.push(endpoint.split("/").slice(0, 2).join("/") || "/");
      router.refresh();
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      {fields.map((field) => (
        <label key={field.name}>
          {field.label}
          {field.type === "select" ? (
            <select
              name={field.name}
              required={field.required}
              value={values[field.name] ?? ""}
              onChange={(e) => setValue(field.name, e.target.value)}
            >
              <option value="">-- Select --</option>
              {(field.options || []).map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={field.type || "text"}
              name={field.name}
              required={field.required}
              value={values[field.name] ?? ""}
              onChange={(e) => setValue(field.name, e.target.value)}
              placeholder={field.placeholder || ""}
              min={field.min}
              max={field.max}
            />
          )}
        </label>
      ))}
      <div className="form-actions">
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : method === "PUT" ? "Save" : "Create"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => router.back()}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
