export default function PersonaCard({ persona }) {
  const churnPct = `${(persona.churn_rate * 100).toFixed(1)}%`;
  const sharePct = `${(persona.pct_of_customers * 100).toFixed(1)}%`;
  const chars = persona.characteristics
    ? persona.characteristics.split(" | ")
    : [];

  return (
    <article className="persona-card">
      <header>
        <p className="eyebrow">Cluster {persona.cluster_id}</p>
        <h3>{persona.persona_name}</h3>
      </header>
      <div className="persona-stats">
        <div>
          <span className="label">Customers</span>
          <strong>
            {persona.count.toLocaleString()} ({sharePct})
          </strong>
        </div>
        <div>
          <span className="label">Avg tenure</span>
          <strong>{persona.avg_tenure.toFixed(1)} mo</strong>
        </div>
        <div>
          <span className="label">Avg monthly</span>
          <strong>${persona.avg_monthly_charges.toFixed(2)}</strong>
        </div>
        <div>
          <span className="label">Churn rate</span>
          <strong className={persona.churn_rate >= 0.3 ? "text-high" : "text-low"}>
            {churnPct}
          </strong>
        </div>
      </div>
      <p className="muted small">
        Typical: {persona.top_contract} · {persona.top_internet} ·{" "}
        {persona.top_payment}
      </p>
      <ul className="char-list">
        {chars.map((c) => (
          <li key={c}>{c}</li>
        ))}
      </ul>
    </article>
  );
}
