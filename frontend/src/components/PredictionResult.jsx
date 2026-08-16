export default function PredictionResult({ result }) {
  if (!result) {
    return (
      <div className="empty-state">
        Submit the form to see churn risk, probability, persona, and drivers.
      </div>
    );
  }

  const riskClass = `risk-badge risk-${result.risk_level.toLowerCase()}`;
  const pct = `${(result.probability * 100).toFixed(1)}%`;

  return (
    <div className="prediction-result">
      <div className="prediction-header">
        <div>
          <p className="eyebrow">Model output</p>
          <h2>{result.prediction_label}</h2>
          <p className="muted">{result.explanation}</p>
        </div>
        <div className="prediction-metrics">
          <span className={riskClass}>{result.risk_level} risk</span>
          <div className="prob-block">
            <span className="prob-label">Churn probability</span>
            <span className="prob-value">{pct}</span>
          </div>
        </div>
      </div>

      <div className="prediction-grid">
        <section>
          <h3>Assigned persona</h3>
          <p className="persona-name">{result.persona.persona_name}</p>
          <p className="muted small">
            Cluster #{result.persona.cluster_id}
            {result.persona.cluster_churn_rate != null
              ? ` · cluster churn ${(result.persona.cluster_churn_rate * 100).toFixed(1)}%`
              : ""}
          </p>
          {result.persona.characteristics ? (
            <ul className="char-list">
              {result.persona.characteristics.split(" | ").map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          ) : null}
        </section>

        <section>
          <h3>Main risk factors</h3>
          {result.risk_factors?.length ? (
            <ul className="risk-factor-list">
              {result.risk_factors.map((f) => (
                <li key={f.feature}>
                  <span>{f.feature}</span>
                  <span className="imp">{(f.importance * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No active high-importance factors for this profile.</p>
          )}
        </section>
      </div>
    </div>
  );
}
