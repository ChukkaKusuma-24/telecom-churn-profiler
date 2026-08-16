import { useState } from "react";
import { predictCustomer } from "../api";
import ChurnForm from "../components/ChurnForm";
import PredictionResult from "../components/PredictionResult";

export default function Predict() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(payload) {
    setLoading(true);
    setError("");
    try {
      const data = await predictCustomer(payload);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err.message || "Prediction failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Inference</p>
          <h1>Predict customer churn</h1>
          <p className="muted">
            Enter a customer profile. The Decision Tree returns probability and risk
            factors; K-Means assigns a behavioral persona.
          </p>
        </div>
      </div>

      <div className="predict-layout">
        <section className="panel">
          <div className="panel-header">
            <h2>Customer features</h2>
          </div>
          <ChurnForm onSubmit={handleSubmit} loading={loading} />
        </section>

        <section className="panel">
          <div className="panel-header">
            <h2>Result</h2>
          </div>
          {error ? <div className="error-state">{error}</div> : null}
          <PredictionResult result={result} />
        </section>
      </div>
    </div>
  );
}
