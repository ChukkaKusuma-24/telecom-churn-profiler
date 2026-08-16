import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#5c7e8f", "#c06a74", "#7fb8b8", "#b8b5a1", "#58747f", "#c5a774"];

export default function Charts({ data, loading, error }) {
  if (loading) return <div className="loading-state">Loading charts…</div>;
  if (error) return <div className="error-state">{error}</div>;
  if (!data) return <div className="empty-state">No chart data available.</div>;

  const churnDist = data.churn_distribution || [];
  const byContract = (data.churn_by_contract || []).map((d) => ({
    ...d,
    churn_pct: Number((d.churn_rate * 100).toFixed(1)),
  }));
  const byTenure = (data.churn_by_tenure || []).map((d) => ({
    ...d,
    churn_pct: Number((d.churn_rate * 100).toFixed(1)),
  }));
  const personas = data.persona_distribution || [];
  const drivers = (data.top_drivers || []).map((d) => ({
    ...d,
    short: shorten(d.feature),
    imp_pct: Number((d.importance * 100).toFixed(2)),
  }));

  return (
    <div className="charts-grid">
      <ChartPanel title="Churn distribution">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={churnDist}
              dataKey="value"
              nameKey="label"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
            >
              {churnDist.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </ChartPanel>

      <ChartPanel title="Top churn drivers">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={drivers} layout="vertical" margin={{ left: 24 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d7e2e6" />
            <XAxis type="number" unit="%" />
            <YAxis type="category" dataKey="short" width={120} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => [`${v}%`, "Importance"]} />
            <Bar dataKey="imp_pct" fill="#7fb8b8" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>

      <ChartPanel title="Churn rate by contract">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={byContract}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d7e2e6" />
            <XAxis dataKey="contract" tick={{ fontSize: 11 }} />
            <YAxis unit="%" />
            <Tooltip formatter={(v) => [`${v}%`, "Churn rate"]} />
            <Bar dataKey="churn_pct" fill="#b8b5a1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>

      <ChartPanel title="Persona distribution">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={personas}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d7e2e6" />
            <XAxis dataKey="persona" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={70} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#5c7e8f" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>

      <ChartPanel title="Churn rate by tenure" wide>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={byTenure}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d7e2e6" />
            <XAxis dataKey="tenure_bin" />
            <YAxis unit="%" />
            <Tooltip formatter={(v) => [`${v}%`, "Churn rate"]} />
            <Bar dataKey="churn_pct" fill="#c06a74" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartPanel>
    </div>
  );
}

function ChartPanel({ title, children, wide }) {
  return (
    <section className={`chart-panel${wide ? " wide" : ""}`}>
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function shorten(name) {
  if (!name) return "";
  return name.length > 22 ? `${name.slice(0, 20)}…` : name;
}
