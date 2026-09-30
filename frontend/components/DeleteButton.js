"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function DeleteButton({ path, label = "Delete" }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleDelete() {
    if (!window.confirm("Are you sure you want to delete this record?")) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.remove(path);
      router.refresh();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <span>
      <button type="button" className="btn-danger" onClick={handleDelete} disabled={busy}>
        {busy ? "Deleting..." : label}
      </button>
      {error && (
        <span className="error" style={{ display: "block", marginTop: 8 }}>
          {error}
        </span>
      )}
    </span>
  );
}
