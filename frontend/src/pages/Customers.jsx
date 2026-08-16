import { useCallback, useEffect, useState } from "react";
import { getCustomers, API_BASE } from "../api";

export default function Customers() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(15);
  const [search, setSearch] = useState("");
  const [contract, setContract] = useState("");
  const [churn, setChurn] = useState("");
  const [riskLevel, setRiskLevel] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getCustomers({
        page,
        pageSize,
        search,
        contract,
        churn,
        riskLevel,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      const msg = err.message || "Failed to load customers";
      if (msg.includes("Cannot reach API")) {
        setError(`${msg} Start the backend: cd backend && uvicorn backend.main:app --reload`);
      } else {
        setError(msg);
      }
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, contract, churn, riskLevel]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  function applyFilters(e) {
    e.preventDefault();
    setPage(1);
    load();
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Records</p>
          <h1>Customers</h1>
          <p className="muted">
            Searchable table scored with the trained churn model and persona clusters.
          </p>
        </div>
      </div>

      <form className="filters" onSubmit={applyFilters}>
        <input
          type="search"
          placeholder="Search customer ID…"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={contract}
          onChange={(e) => {
            setContract(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All contracts</option>
          <option>Month-to-month</option>
          <option>One year</option>
          <option>Two year</option>
        </select>
        <select
          value={churn}
          onChange={(e) => {
            setChurn(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All churn labels</option>
          <option value="Yes">Churned</option>
          <option value="No">Active</option>
        </select>
        <select
          value={riskLevel}
          onChange={(e) => {
            setRiskLevel(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All risk levels</option>
          <option>Low</option>
          <option>Medium</option>
          <option>High</option>
        </select>
        <button type="submit" className="btn-secondary">
          Refresh
        </button>
      </form>

      {error ? <div className="error-state">{error}</div> : null}

      <div className="table-wrap">
        {loading ? (
          <div className="loading-state">Loading customers…</div>
        ) : items.length === 0 ? (
          <div className="empty-state">No customers match these filters.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Tenure</th>
                <th>Contract</th>
                <th>Monthly</th>
                <th>Internet</th>
                <th>Churn</th>
                <th>Risk</th>
                <th>Prob.</th>
                <th>Persona</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.customerID}>
                  <td className="mono">{row.customerID}</td>
                  <td>{row.tenure}</td>
                  <td>{row.Contract}</td>
                  <td>${row.MonthlyCharges.toFixed(2)}</td>
                  <td>{row.InternetService}</td>
                  <td>{row.Churn}</td>
                  <td>
                    <span
                      className={`risk-badge risk-${(row.risk_level || "low").toLowerCase()}`}
                    >
                      {row.risk_level}
                    </span>
                  </td>
                  <td>
                    {row.churn_probability != null
                      ? `${(row.churn_probability * 100).toFixed(0)}%`
                      : "—"}
                  </td>
                  <td className="persona-cell">{row.persona_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="pagination">
        <button
          type="button"
          className="btn-secondary"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </button>
        <span>
          Page {page} of {totalPages} · {total.toLocaleString()} customers
        </span>
        <button
          type="button"
          className="btn-secondary"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
