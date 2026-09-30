import { test, before, after } from "node:test";
import assert from "node:assert/strict";

process.env.NEXT_PUBLIC_API_URL = "http://test-backend";

const calls = [];
const realFetch = global.fetch;

function stubFetch(status, body) {
  global.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    return new Response(body === undefined ? null : JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  };
}

before(() => {
  stubFetch(409, { detail: "boom" });
});

after(() => {
  global.fetch = realFetch;
});

const { api, BASE_URL } = await import("../lib/api.js");

test("BASE_URL defaults to NEXT_PUBLIC_API_URL", () => {
  assert.equal(BASE_URL, "http://test-backend");
});

test("create sends a POST with a JSON body", { concurrency: false }, async () => {
  await assert.rejects(() => api.create("/departments", { department_code: "X" }));
  const { url, options } = calls.at(-1);
  assert.equal(url, "http://test-backend/departments");
  assert.equal(options.method, "POST");
  assert.equal(options.body, JSON.stringify({ department_code: "X" }));
  assert.equal(options.headers["Content-Type"], "application/json");
});

test("update sends a PUT with a JSON body", { concurrency: false }, async () => {
  await assert.rejects(() =>
    api.update("/departments/abc", { department_name: "Y" })
  );
  const { url, options } = calls.at(-1);
  assert.equal(url, "http://test-backend/departments/abc");
  assert.equal(options.method, "PUT");
  assert.equal(options.body, JSON.stringify({ department_name: "Y" }));
});

test("get sends a GET without a body", { concurrency: false }, async () => {
  stubFetch(200, { items: [] });
  const data = await api.get("/students");
  assert.deepEqual(data, { items: [] });
  const call = calls.at(-1);
  assert.equal(call.options.method ?? "GET", "GET");
  assert.equal(call.options.body, undefined);
});

test("error detail is surfaced from the response body", { concurrency: false }, async () => {
  stubFetch(409, { detail: "boom" });
  await assert.rejects(() => api.get("/departments"), /boom/);
});

test("a 204 response returns null", { concurrency: false }, async () => {
  stubFetch(204);
  const result = await api.remove("/departments/abc");
  assert.equal(result, null);
});
