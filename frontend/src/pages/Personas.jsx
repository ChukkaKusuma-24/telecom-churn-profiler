import { useEffect, useState } from "react";
import { getPersonas } from "../api";
import PersonaCard from "../components/PersonaCard";

export default function Personas() {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await getPersonas();
        if (!cancelled) setPersonas(data);
      } catch (err) {
        if (!cancelled) setError(err.message || "Failed to load personas");
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
          <p className="eyebrow">Segmentation</p>
          <h1>Customer personas</h1>
          <p className="muted">
            Personas are auto-named from real K-Means cluster statistics (tenure,
            spend, churn rate) — not hardcoded labels.
          </p>
        </div>
      </div>

      {loading ? <div className="loading-state">Loading personas…</div> : null}
      {error ? <div className="error-state">{error}</div> : null}

      {!loading && !error && personas.length === 0 ? (
        <div className="empty-state">
          No cluster profiles found. Run <code>python ml/train_segments.py</code>.
        </div>
      ) : null}

      <div className="persona-grid">
        {personas.map((p) => (
          <PersonaCard key={p.cluster_id} persona={p} />
        ))}
      </div>
    </div>
  );
}
