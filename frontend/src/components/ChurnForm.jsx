import React, { useState } from "react";

/**
 * Churn prediction form — fields match the Telco dataset feature columns
 * (excluding customerID and Churn).
 */
const YES_NO = ["Yes", "No"];
const YES_NO_PHONE = ["Yes", "No", "No phone service"];
const YES_NO_INTERNET = ["Yes", "No", "No internet service"];

const INITIAL = {
  gender: "Female",
  SeniorCitizen: 0,
  Partner: "No",
  Dependents: "No",
  tenure: 12,
  PhoneService: "Yes",
  MultipleLines: "No",
  InternetService: "Fiber optic",
  OnlineSecurity: "No",
  OnlineBackup: "No",
  DeviceProtection: "No",
  TechSupport: "No",
  StreamingTV: "No",
  StreamingMovies: "No",
  Contract: "Month-to-month",
  PaperlessBilling: "Yes",
  PaymentMethod: "Electronic check",
  MonthlyCharges: 70,
  TotalCharges: 840,
};

export default function ChurnForm({ onSubmit, loading }) {
  const [form, setForm] = useState(INITIAL);

  function update(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const payload = {
      ...form,
      SeniorCitizen: Number(form.SeniorCitizen),
      tenure: Number(form.tenure),
      MonthlyCharges: Number(form.MonthlyCharges),
      TotalCharges: Number(form.TotalCharges),
    };
    onSubmit(payload);
  }

  return (
    <form className="churn-form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <Field label="Gender">
          <select
            value={form.gender}
            onChange={(e) => update("gender", e.target.value)}
          >
            <option>Female</option>
            <option>Male</option>
          </select>
        </Field>

        <Field label="Senior Citizen">
          <select
            value={form.SeniorCitizen}
            onChange={(e) => update("SeniorCitizen", e.target.value)}
          >
            <option value={0}>No</option>
            <option value={1}>Yes</option>
          </select>
        </Field>

        <Field label="Partner">
          <Select
            value={form.Partner}
            options={YES_NO}
            onChange={(v) => update("Partner", v)}
          />
        </Field>

        <Field label="Dependents">
          <Select
            value={form.Dependents}
            options={YES_NO}
            onChange={(v) => update("Dependents", v)}
          />
        </Field>

        <Field label="Tenure (months)">
          <input
            type="number"
            min={0}
            value={form.tenure}
            onChange={(e) => update("tenure", e.target.value)}
            required
          />
        </Field>

        <Field label="Phone Service">
          <Select
            value={form.PhoneService}
            options={YES_NO}
            onChange={(v) => update("PhoneService", v)}
          />
        </Field>

        <Field label="Multiple Lines">
          <Select
            value={form.MultipleLines}
            options={YES_NO_PHONE}
            onChange={(v) => update("MultipleLines", v)}
          />
        </Field>

        <Field label="Internet Service">
          <Select
            value={form.InternetService}
            options={["DSL", "Fiber optic", "No"]}
            onChange={(v) => update("InternetService", v)}
          />
        </Field>

        <Field label="Online Security">
          <Select
            value={form.OnlineSecurity}
            options={YES_NO_INTERNET}
            onChange={(v) => update("OnlineSecurity", v)}
          />
        </Field>

        <Field label="Online Backup">
          <Select
            value={form.OnlineBackup}
            options={YES_NO_INTERNET}
            onChange={(v) => update("OnlineBackup", v)}
          />
        </Field>

        <Field label="Device Protection">
          <Select
            value={form.DeviceProtection}
            options={YES_NO_INTERNET}
            onChange={(v) => update("DeviceProtection", v)}
          />
        </Field>

        <Field label="Tech Support">
          <Select
            value={form.TechSupport}
            options={YES_NO_INTERNET}
            onChange={(v) => update("TechSupport", v)}
          />
        </Field>

        <Field label="Streaming TV">
          <Select
            value={form.StreamingTV}
            options={YES_NO_INTERNET}
            onChange={(v) => update("StreamingTV", v)}
          />
        </Field>

        <Field label="Streaming Movies">
          <Select
            value={form.StreamingMovies}
            options={YES_NO_INTERNET}
            onChange={(v) => update("StreamingMovies", v)}
          />
        </Field>

        <Field label="Contract">
          <Select
            value={form.Contract}
            options={["Month-to-month", "One year", "Two year"]}
            onChange={(v) => update("Contract", v)}
          />
        </Field>

        <Field label="Paperless Billing">
          <Select
            value={form.PaperlessBilling}
            options={YES_NO}
            onChange={(v) => update("PaperlessBilling", v)}
          />
        </Field>

        <Field label="Payment Method" wide>
          <Select
            value={form.PaymentMethod}
            options={[
              "Electronic check",
              "Mailed check",
              "Bank transfer (automatic)",
              "Credit card (automatic)",
            ]}
            onChange={(v) => update("PaymentMethod", v)}
          />
        </Field>

        <Field label="Monthly Charges ($)">
          <input
            type="number"
            min={0}
            step="0.01"
            value={form.MonthlyCharges}
            onChange={(e) => update("MonthlyCharges", e.target.value)}
            required
          />
        </Field>

        <Field label="Total Charges ($)">
          <input
            type="number"
            min={0}
            step="0.01"
            value={form.TotalCharges}
            onChange={(e) => update("TotalCharges", e.target.value)}
            required
          />
        </Field>
      </div>

      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? "Predicting…" : "Predict Churn Risk"}
      </button>
    </form>
  );
}

function Field({ label, children, wide }) {
  return (
    <label className={`field${wide ? " wide" : ""}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

function Select({ value, options, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  );
}
