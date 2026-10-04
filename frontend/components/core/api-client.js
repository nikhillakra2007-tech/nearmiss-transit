/* Core API client: resilient fetch helpers, error formatting, and escaping */
const $ = (id) => document.getElementById(id);
const API = "/api/v1";

async function jget(path) {
  const r = await fetch(API + path);
  if (!r.ok) {
    const e = new Error(`${r.status} on ${path}`);
    e.status = r.status;
    throw e;
  }
  return r.json();
}

async function jpost(path, body) {
  const r = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const e = new Error(`${r.status} on ${path}`);
    e.status = r.status;
    try {
      e.detail = await r.json();
    } catch {
      /* ignore non-json error responses */
    }
    return Promise.reject(e);
  }
  return r.json();
}

function errMsg(e, what) {
  const s = e && e.status;
  if (s === 404) return `${what}: not found.`;
  if (s === 422) return `${what}: invalid request was rejected.`;
  if (s >= 500) return `${what}: server error.`;
  return `${what} unavailable.`;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function fmtT(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return String(iso);
  }
}

function shortId(id) {
  return String(id || "").slice(0, 8);
}
