/**
 * api.js — API communication with the FastAPI backend
 */

const API_BASE = "https://telecom-churn-profiler-1.onrender.com" || "http://localhost:8000";

/**
 * Generic API request
 */
async function request(path, options = {}) {
  // Build the URL safely
  const url = new URL(path, API_BASE).toString();

  console.log("API Request:", url);

  const config = {
    ...options,
    headers: {
      ...(options.body
        ? {
            "Content-Type": "application/json",
          }
        : {}),
      ...(options.headers || {}),
    },
  };

  let res;

  try {
    res = await fetch(url, config);
  } catch (err) {
    console.error("API connection error:", err);

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
      body &&
      typeof body === "object" &&
      body.detail
        ? typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail)
        : res.statusText;

    throw new Error(
      detail || `Request failed (${res.status})`
    );
  }

  return body;
}


/* =========================
   API ENDPOINTS
   ========================= */

/**
 * GET /
 */
export const getStatus = () => {
  return request("/");
};


/**
 * GET /dashboard
 */
export const getDashboard = () => {
  return request("/dashboard");
};


/**
 * GET /churn-drivers
 */
export const getChurnDrivers = (topN = 15) => {
  return request(`/churn-drivers?top_n=${topN}`);
};


/**
 * GET /personas
 */
export const getPersonas = () => {
  return request("/personas");
};


/**
 * GET /charts
 */
export const getCharts = () => {
  return request("/charts");
};


/**
 * POST /predict
 */
export const predictCustomer = (payload) => {
  return request("/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};


/**
 * GET /customers
 */
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

  if (search) {
    params.set("search", search);
  }

  if (contract) {
    params.set("contract", contract);
  }

  if (churn) {
    params.set("churn", churn);
  }

  if (riskLevel) {
    params.set("risk_level", riskLevel);
  }

  if (persona) {
    params.set("persona", persona);
  }

  return request(`/customers?${params.toString()}`);
}


/**
 * Export API base URL
 */
export { API_BASE };