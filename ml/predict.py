"""
predict.py
----------
Inference helpers for a single customer:
  - Churn prediction + probability
  - Risk level + top risk factors (from feature importances on active features)
  - Persona assignment via saved K-Means pipeline
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import load_joblib  # noqa: E402

# Fields the API / form may send (must match training feature columns)
CUSTOMER_INPUT_FIELDS = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
]


def _risk_level(proba: float) -> str:
    if proba >= 0.66:
        return "High"
    if proba >= 0.33:
        return "Medium"
    return "Low"


def _customer_to_dataframe(customer: Dict[str, Any], feature_cols: List[str]) -> pd.DataFrame:
    """Build a one-row DataFrame aligned to training feature columns."""
    row = {}
    for col in feature_cols:
        if col not in customer:
            raise ValueError(f"Missing required field: {col}")
        row[col] = customer[col]
    return pd.DataFrame([row])


def top_risk_factors(
    pipeline,
    X_row: pd.DataFrame,
    feature_names: List[str],
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """
    Approximate risk factors using Decision Tree feature importances
    on features that are active for this customer (one-hot value ~1 or numeric).
    """
    pre = pipeline.named_steps["preprocess"]
    tree = pipeline.named_steps["model"]
    X_t = pre.transform(X_row)
    importances = tree.feature_importances_

    numeric_prefixes = ("tenure", "MonthlyCharges", "TotalCharges", "SeniorCitizen")
    factors = []
    for i, name in enumerate(feature_names):
        val = float(X_t[0, i])
        imp = float(importances[i])
        if imp <= 0:
            continue
        is_numeric = name in numeric_prefixes or name.startswith(numeric_prefixes)
        if (not is_numeric) and val < 0.5:
            # inactive one-hot category
            continue
        factors.append(
            {
                "feature": name,
                "importance": round(imp, 6),
                "value": round(val, 4),
            }
        )

    factors.sort(key=lambda d: d["importance"], reverse=True)
    return factors[:top_n]


def assign_persona(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Transform customer with cluster encoder+scaler and predict cluster."""
    bundle = load_joblib("clustering_model.pkl")
    scaler = load_joblib("scaler.pkl")
    feature_cols = bundle["feature_cols"]
    encoder = bundle["encoder"]
    kmeans = bundle["kmeans"]
    lookup = bundle["persona_lookup"]

    X = _customer_to_dataframe(customer, feature_cols)
    X_enc = encoder.transform(X)
    X_scaled = scaler.transform(X_enc)
    cid = int(kmeans.predict(X_scaled)[0])

    # Keys may be int after joblib round-trip
    info = lookup.get(cid)
    if info is None:
        info = lookup.get(str(cid), {})

    return {
        "cluster_id": cid,
        "persona_name": info.get("persona_name", f"Cluster {cid}"),
        "characteristics": info.get("characteristics", ""),
        "cluster_churn_rate": info.get("churn_rate"),
        "cluster_avg_tenure": info.get("avg_tenure"),
        "cluster_avg_monthly_charges": info.get("avg_monthly_charges"),
    }


def predict_customer(customer: Dict[str, Any]) -> Dict[str, Any]:
    """Full single-customer prediction payload for the API."""
    pipeline = load_joblib("churn_model.pkl")
    meta = load_joblib("feature_columns.pkl")
    feature_cols = meta["numeric_cols"] + meta["categorical_cols"]
    feature_names = meta["feature_names"]

    X = _customer_to_dataframe(customer, feature_cols)
    proba = float(pipeline.predict_proba(X)[0, 1])
    pred = int(pipeline.predict(X)[0])
    risk = _risk_level(proba)
    factors = top_risk_factors(pipeline, X, feature_names, top_n=5)
    persona = assign_persona(customer)

    explanation = (
        f"Predicted {'churn' if pred == 1 else 'no churn'} with probability {proba:.1%}. "
        f"Risk level: {risk}. Assigned persona: {persona['persona_name']}."
    )

    return {
        "prediction": pred,
        "prediction_label": "Churn" if pred == 1 else "No Churn",
        "probability": round(proba, 4),
        "risk_level": risk,
        "risk_factors": factors,
        "persona": persona,
        "explanation": explanation,
    }


if __name__ == "__main__":
    sample = {
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 1,
        "PhoneService": "No",
        "MultipleLines": "No phone service",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 29.85,
        "TotalCharges": 29.85,
    }
    try:
        result = predict_customer(sample)
        print(result)
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)
