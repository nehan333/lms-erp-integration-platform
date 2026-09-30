"use client";

import { useState } from "react";
import { BASE_URL } from "@/lib/api";

export default function SyncPanel() {
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function checkStatus() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${BASE_URL}/integrations/moodle/status`, {
        cache: "no-store",
      });
      setStatus(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function runSync() {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${BASE_URL}/integrations/moodle/sync`, {
        method: "POST",
        cache: "no-store",
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.detail || `Sync failed (${res.status})`);
      }
      setResult(body);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="form-actions" style={{ marginTop: 0 }}>
        <button type="button" onClick={checkStatus} disabled={busy}>
          Check Status
        </button>
        <button type="button" onClick={runSync} disabled={busy} className="btn-secondary">
          Run Full Sync
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {!error && status && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>Moodle Status</h2>
          <p>
            <span
              className={status.connected ? "badge badge-success" : "badge badge-danger"}
            >
              {status.connected ? "Connected" : "Disconnected"}
            </span>{" "}
            {status.site_name && (
              <span className="muted">
                — {status.site_name} (v{status.moodle_version})
              </span>
            )}
          </p>
          {!status.connected && <p className="muted">{status.message}</p>}
        </div>
      )}

      {!error && result && (
        <div className="card" style={{ marginTop: 16 }}>
          <h2>Sync Result</h2>
          <p>
            Total: <strong>{result.total}</strong> · Success:{" "}
            <strong className="badge badge-success">{result.success}</strong> · Failed:{" "}
            <strong className="badge badge-danger">{result.failed}</strong>
          </p>
          <table>
            <thead>
              <tr>
                <th>Action</th>
                <th>Status</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {result.logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.action}</td>
                  <td>
                    {log.status === "Success" ? (
                      <span className="badge badge-success">{log.status}</span>
                    ) : (
                      <span className="badge badge-danger">{log.status}</span>
                    )}
                  </td>
                  <td>{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}