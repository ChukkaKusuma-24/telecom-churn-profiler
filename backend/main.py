"""
main.py
-------
FastAPI backend for Telecom Churn Driver Discovery & Persona Profiler.

Endpoints:
  GET  /              — status
  GET  /dashboard     — aggregate stats
  GET  /churn-drivers — top feature importances
  GET  /personas      — cluster personas
  POST /predict       — single-customer prediction
  GET  /customers     — searchable/paginated customer table
  GET  /charts        — chart-ready aggregations for the dashboard

No database yet — reads CSV + trained artifacts. Designed so MySQL
can replace the CSV loaders later without changing route contracts.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
ML_DIR = PROJECT_ROOT / "ml"
OUTPUTS_DIR = ML_DIR / "outputs"

sys.path.insert(0, str(ML_DIR))

from preprocess import (  # noqa: E402
    TARGET_COL,
    clean_dataframe,
    load_joblib,
    load_raw_data,
)
from predict import predict_customer  # noqa: E402

# Support both `uvicorn backend.main:app` (project root) and `uvicorn main:app` (from backend/)
try:
    from schemas import (  # noqa: E402
        ChartSeriesResponse,
        ChurnDriver,
        CustomerInput,
        CustomerRecord,
        CustomersResponse,
        DashboardResponse,
        PersonaProfile,
        PredictResponse,
        StatusResponse,
    )
except ImportError:
    from backend.schemas import (  # noqa: E402
        ChartSeriesResponse,
        ChurnDriver,
        CustomerInput,
        CustomerRecord,
        CustomersResponse,
        DashboardResponse,
        PersonaProfile,
        PredictResponse,
        StatusResponse,
    )

app = FastAPI(
    title="Telecom Churn Driver Discovery & Persona Profiler",
    description=(
        "Educational telecom analytics API: churn prediction (Decision Tree), "
        "driver discovery, and K-Means personas. Not medical or financial advice."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _cleaned_df() -> pd.DataFrame:
    raw = load_raw_data()
    return clean_dataframe(raw)


def _models_ready() -> bool:
    needed = [
        ML_DIR / "models" / "churn_model.pkl",
        ML_DIR / "models" / "feature_columns.pkl",
        ML_DIR / "models" / "clustering_model.pkl",
        ML_DIR / "models" / "scaler.pkl",
    ]
    return all(p.exists() for p in needed)


def _risk_from_proba(p: float) -> str:
    if p >= 0.66:
        return "High"
    if p >= 0.33:
        return "Medium"
    return "Low"


@lru_cache(maxsize=1)
def _scored_customers() -> pd.DataFrame:
    """Score all customers once for the Customers table / high-risk counts."""
    if not _models_ready():
        raise FileNotFoundError("Models not trained yet.")

    df = _cleaned_df().copy()
    pipeline = load_joblib("churn_model.pkl")
    meta = load_joblib("feature_columns.pkl")
    bundle = load_joblib("clustering_model.pkl")
    scaler = load_joblib("scaler.pkl")

    feature_cols = meta["numeric_cols"] + meta["categorical_cols"]
    X = df[feature_cols]
    proba = pipeline.predict_proba(X)[:, 1]

    X_enc = bundle["encoder"].transform(df[bundle["feature_cols"]])
    X_scaled = scaler.transform(X_enc)
    clusters = bundle["kmeans"].predict(X_scaled)
    lookup = bundle["persona_lookup"]

    df = df.copy()
    df["churn_probability"] = proba
    df["risk_level"] = [_risk_from_proba(float(p)) for p in proba]
    df["cluster_id"] = clusters
    df["persona_name"] = [
        (lookup.get(int(c)) or lookup.get(str(c)) or {}).get(
            "persona_name", f"Cluster {c}"
        )
        for c in clusters
    ]
    df["Churn_label"] = df[TARGET_COL].map({1: "Yes", 0: "No"})
    return df


@app.get("/", response_model=StatusResponse)
def root() -> StatusResponse:
    ready = _models_ready()
    return StatusResponse(
        status="ok" if ready else "degraded",
        message=(
            "API is running. Models loaded."
            if ready
            else "API is running, but ML models are missing. Run training scripts first."
        ),
        models_loaded=ready,
    )


@app.get("/dashboard", response_model=DashboardResponse)
def dashboard() -> DashboardResponse:
    try:
        df = _cleaned_df()
        scored = _scored_customers() if _models_ready() else None
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    churned = int(df[TARGET_COL].sum())
    total = int(len(df))
    high_risk = int((scored["risk_level"] == "High").sum()) if scored is not None else 0

    persona_count = 0
    if _models_ready():
        bundle = load_joblib("clustering_model.pkl")
        persona_count = int(bundle.get("chosen_k", 0))

    return DashboardResponse(
        total_customers=total,
        churned_customers=churned,
        churn_rate=float(churned / total) if total else 0.0,
        high_risk_count=high_risk,
        persona_count=persona_count,
        avg_tenure=float(df["tenure"].mean()),
        avg_monthly_charges=float(df["MonthlyCharges"].mean()),
    )


@app.get("/churn-drivers", response_model=List[ChurnDriver])
def churn_drivers(top_n: int = Query(15, ge=1, le=50)) -> List[ChurnDriver]:
    path = OUTPUTS_DIR / "feature_importance.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="feature_importance.csv not found. Run: python ml/evaluate.py",
        )
    fi = pd.read_csv(path).head(top_n)
    return [
        ChurnDriver(
            feature=str(r.feature),
            importance=float(r.importance),
            rank=int(r.rank),
        )
        for r in fi.itertuples()
    ]


@app.get("/personas", response_model=List[PersonaProfile])
def personas() -> List[PersonaProfile]:
    path = OUTPUTS_DIR / "cluster_profiles.csv"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="cluster_profiles.csv not found. Run: python ml/train_segments.py",
        )
    profiles = pd.read_csv(path)
    out: List[PersonaProfile] = []
    for r in profiles.itertuples():
        out.append(
            PersonaProfile(
                cluster_id=int(r.cluster_id),
                persona_name=str(r.persona_name),
                count=int(r.count),
                pct_of_customers=float(r.pct_of_customers),
                avg_tenure=float(r.avg_tenure),
                avg_monthly_charges=float(r.avg_monthly_charges),
                avg_total_charges=float(r.avg_total_charges),
                churn_rate=float(r.churn_rate),
                characteristics=str(r.characteristics),
                top_contract=str(r.top_contract),
                top_internet=str(r.top_internet),
                top_payment=str(r.top_payment),
            )
        )
    return out


@app.post("/predict", response_model=PredictResponse)
def predict(payload: CustomerInput) -> PredictResponse:
    if not _models_ready():
        raise HTTPException(
            status_code=503,
            detail=(
                "Models not found. Run python ml/train_churn.py and "
                "python ml/train_segments.py"
            ),
        )
    try:
        result = predict_customer(payload.to_feature_dict())
        return PredictResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}") from e


@app.get("/customers", response_model=CustomersResponse)
def customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", description="Search by customerID"),
    contract: Optional[str] = Query(None),
    churn: Optional[str] = Query(None, description="Yes or No"),
    risk_level: Optional[str] = Query(None, description="Low, Medium, or High"),
    persona: Optional[str] = Query(None),
) -> CustomersResponse:
    try:
        df = _scored_customers()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    view = df
    if search:
        view = view[view["customerID"].str.contains(search, case=False, na=False)]
    if contract:
        view = view[view["Contract"] == contract]
    if churn:
        label = churn.strip().capitalize()
        if label in ("Yes", "No"):
            view = view[view["Churn_label"] == label]
    if risk_level:
        view = view[view["risk_level"].str.lower() == risk_level.strip().lower()]
    if persona:
        view = view[view["persona_name"].str.contains(persona, case=False, na=False)]

    total = int(len(view))
    start = (page - 1) * page_size
    end = start + page_size
    page_df = view.iloc[start:end]

    items: List[CustomerRecord] = []
    for r in page_df.itertuples():
        items.append(
            CustomerRecord(
                customerID=str(r.customerID),
                tenure=int(r.tenure),
                Contract=str(r.Contract),
                MonthlyCharges=float(r.MonthlyCharges),
                InternetService=str(r.InternetService),
                Churn=str(r.Churn_label),
                risk_level=str(r.risk_level),
                persona_name=str(r.persona_name),
                cluster_id=int(r.cluster_id),
                churn_probability=float(r.churn_probability),
            )
        )

    return CustomersResponse(
        total=total, page=page, page_size=page_size, items=items
    )


@app.get("/charts", response_model=ChartSeriesResponse)
def charts() -> ChartSeriesResponse:
    """Aggregations for Recharts — all computed from real data/outputs."""
    try:
        df = _cleaned_df()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    churn_dist = [
        {"label": "No Churn", "value": int((df[TARGET_COL] == 0).sum())},
        {"label": "Churn", "value": int((df[TARGET_COL] == 1).sum())},
    ]

    by_contract = (
        df.groupby("Contract")[TARGET_COL]
        .agg(churn_rate="mean", count="size")
        .reset_index()
    )
    churn_by_contract = [
        {
            "contract": str(r.Contract),
            "churn_rate": round(float(r.churn_rate), 4),
            "count": int(r.count),
        }
        for r in by_contract.itertuples()
    ]

    bins = [0, 12, 24, 48, 72]
    labels = ["0-12", "13-24", "25-48", "49-72"]
    tenure_bin = pd.cut(df["tenure"], bins=bins, labels=labels, include_lowest=True)
    by_tenure = (
        df.groupby(tenure_bin, observed=True)[TARGET_COL]
        .agg(churn_rate="mean", count="size")
        .reset_index()
    )
    by_tenure.columns = ["tenure_bin", "churn_rate", "count"]
    churn_by_tenure = [
        {
            "tenure_bin": str(r.tenure_bin),
            "churn_rate": round(float(r.churn_rate), 4),
            "count": int(r.count),
        }
        for r in by_tenure.itertuples()
    ]

    persona_distribution: List[Dict[str, Any]] = []
    profiles_path = OUTPUTS_DIR / "cluster_profiles.csv"
    if profiles_path.exists():
        profiles = pd.read_csv(profiles_path)
        persona_distribution = [
            {
                "persona": str(r.persona_name),
                "count": int(r.count),
                "churn_rate": round(float(r.churn_rate), 4),
            }
            for r in profiles.itertuples()
        ]

    top_drivers: List[Dict[str, Any]] = []
    fi_path = OUTPUTS_DIR / "feature_importance.csv"
    if fi_path.exists():
        fi = pd.read_csv(fi_path).head(10)
        top_drivers = [
            {
                "feature": str(r.feature),
                "importance": round(float(r.importance), 6),
            }
            for r in fi.itertuples()
        ]

    return ChartSeriesResponse(
        churn_distribution=churn_dist,
        churn_by_contract=churn_by_contract,
        churn_by_tenure=churn_by_tenure,
        persona_distribution=persona_distribution,
        top_drivers=top_drivers,
    )


@app.on_event("startup")
def startup_message() -> None:
    print("[backend] Telecom Churn API starting...")
    print(f"[backend] Project root: {PROJECT_ROOT}")
    print(f"[backend] Models ready: {_models_ready()}")
