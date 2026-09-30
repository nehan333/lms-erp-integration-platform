// Thin typed helper around the FastAPI backend.
// BASE_URL is resolved server-side for server components and falls back to
// NEXT_PUBLIC_API_URL for client-side fetches.

export const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body && body.detail) {
        detail = Array.isArray(body.detail)
          ? body.detail.map((d) => d.msg).join("; ")
          : String(body.detail);
      }
    } catch {
      // keep default detail
    }
    throw new Error(detail);
  }

  if (res.status === 204) {
    return null;
  }
  return res.json();
}

export const api = {
  get: (path) => request(path),

  create: (path, body) =>
    request(path, { method: "POST", body: JSON.stringify(body) }),

  update: (path, body) =>
    request(path, { method: "PUT", body: JSON.stringify(body) }),

  remove: (path) => request(path, { method: "DELETE" }),
};
