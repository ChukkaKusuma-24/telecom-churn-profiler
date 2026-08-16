/**
 * api.js — thin fetch wrappers for the FastAPI backend.
 * All UI stats must come from these endpoints (never hardcode).
 */
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  let res;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch (err) {
    throw new Error(
      `Cannot reach API at ${API_BASE}. Is the backend running? (${err.message})`
    );
  }

  let body = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!res.ok) {
    const detail =
      body && typeof body === "object" && body.detail
        ? typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail)
        : res.statusText;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return body;
}

export const getStatus = () => request("/");
export const getDashboard = () => request("/dashboard");
export const getChurnDrivers = (topN = 15) =>
  request(`/churn-drivers?top_n=${topN}`);
export const getPersonas = () => request("/personas");
export const getCharts = () => request("/charts");
export const predictCustomer = (payload) =>
  request("/predict", { method: "POST", body: JSON.stringify(payload) });

export function getCustomers({
  page = 1,
  pageSize = 20,
  search = "",
  contract = "",
  churn = "",
  riskLevel = "",
  persona = "",
} = {}) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  if (search) params.set("search", search);
  if (contract) params.set("contract", contract);
  if (churn) params.set("churn", churn);
  if (riskLevel) params.set("risk_level", riskLevel);
  if (persona) params.set("persona", persona);
  return request(`/customers?${params.toString()}`);
}

export { API_BASE };
