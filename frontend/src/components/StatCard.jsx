export default function StatCard({ label, value, hint, tone = "default", icon }) {
  return (
    <article className={`stat-card tone-${tone}`}>
      <div className="stat-head">
        <div className="icon-wrap">{icon || <span className="dot" />}</div>
        <p className="stat-label">{label}</p>
      </div>
      <div className="stat-body">
        <p className="stat-value">{value}</p>
        {hint ? <p className="stat-hint">{hint}</p> : null}
      </div>
    </article>
  );
}
