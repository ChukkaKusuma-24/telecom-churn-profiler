import { useEffect, useState } from "react";
import { getCharts, getChurnDrivers, getDashboard } from "../api";
import StatCard from "../components/StatCard";
import Charts from "../components/Charts";
import ChurnDrivers from "../components/ChurnDrivers";

function pct(n) {
  return `${(n * 100).toFixed(1)}%`;
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [charts, setCharts] = useState(null);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [dash, chartData, driverData] = await Promise.all([
          getDashboard(),
          getCharts(),
          getChurnDrivers(10),
        ]);
        if (!cancelled) {
          setStats(dash);
          setCharts(chartData);
          setDrivers(driverData);
        }
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load dashboard");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Churn analytics dashboard</h1>
          <p className="muted">
            Stats and charts are computed from the Telco dataset and trained models —
            nothing is hardcoded.
          </p>
        </div>
      </div>

      {error ? <div className="error-state">{error}</div> : null}

      {loading && !stats ? (
        <div className="loading-state">Loading dashboard…</div>
      ) : stats ? (
        <div className="stat-grid">
          <StatCard
            label="Total customers"
            value={stats.total_customers.toLocaleString()}
            hint={`Avg tenure ${stats.avg_tenure.toFixed(1)} mo`}
          />
          <StatCard
            label="Churn rate"
            value={pct(stats.churn_rate)}
            hint="Share who churned (label)"
            tone="warn"
          />
          <StatCard
            label="Churned"
            value={stats.churned_customers.toLocaleString()}
            tone="danger"
          />
          <StatCard
            label="High-risk (model)"
            value={stats.high_risk_count.toLocaleString()}
            hint="Predicted probability ≥ 66%"
            tone="danger"
          />
          <StatCard
            label="Personas"
            value={stats.persona_count}
            hint={`Avg monthly $${stats.avg_monthly_charges.toFixed(2)}`}
            tone="accent"
          />
        </div>
      ) : null}

      <Charts data={charts} loading={loading && !charts} error="" />

      <section className="panel">
        <div className="panel-header">
          <h2>Top churn drivers</h2>
          <p className="muted">Decision Tree feature importance (Gini)</p>
        </div>
        <ChurnDrivers drivers={drivers} loading={loading && !drivers.length} />
      </section>
    </div>
  );
}
