export default function ChurnDrivers({ drivers, loading, error }) {
  if (loading) return <div className="loading-state">Loading drivers…</div>;
  if (error) return <div className="error-state">{error}</div>;
  if (!drivers?.length) {
    return (
      <div className="empty-state">
        No feature importance data yet. Run <code>python ml/evaluate.py</code>.
      </div>
    );
  }

  const max = Math.max(...drivers.map((d) => d.importance), 0.0001);

  return (
    <div className="drivers-list">
      {drivers.map((d) => (
        <div className={`driver-row ${d.rank <= 3 ? 'top-driver' : ''}`} key={d.feature}>
          <div className="driver-meta">
            <span className="driver-rank">{d.rank}</span>
            <span className="driver-name">{d.feature}</span>
            <span className="driver-imp">{(d.importance * 100).toFixed(2)}%</span>
          </div>
          <div className="driver-bar-track">
            <div
              className="driver-bar-fill"
              style={{ width: `${(d.importance / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
