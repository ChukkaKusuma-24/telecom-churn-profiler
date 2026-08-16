"""
schemas.py
----------
Pydantic models for request/response validation.
Designed so a MySQL (or other) persistence layer can be added later
without changing the public API shapes much.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CustomerInput(BaseModel):
    """Single-customer features for churn + persona prediction."""

    gender: str = Field(..., description="Male or Female")
    SeniorCitizen: int = Field(..., ge=0, le=1, description="0 = no, 1 = yes")
    Partner: str = Field(..., description="Yes or No")
    Dependents: str = Field(..., description="Yes or No")
    tenure: int = Field(..., ge=0, description="Months with the company")
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str
    MonthlyCharges: float = Field(..., ge=0)
    TotalCharges: float = Field(..., ge=0)

    @field_validator(
        "Partner",
        "Dependents",
        "PhoneService",
        "PaperlessBilling",
        mode="before",
    )
    @classmethod
    def normalize_yes_no(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    def to_feature_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class RiskFactor(BaseModel):
    feature: str
    importance: float
    value: float


class PersonaInfo(BaseModel):
    cluster_id: int
    persona_name: str
    characteristics: str = ""
    cluster_churn_rate: Optional[float] = None
    cluster_avg_tenure: Optional[float] = None
    cluster_avg_monthly_charges: Optional[float] = None


class PredictResponse(BaseModel):
    prediction: int
    prediction_label: str
    probability: float
    risk_level: str
    risk_factors: List[RiskFactor]
    persona: PersonaInfo
    explanation: str


class StatusResponse(BaseModel):
    status: str
    message: str
    models_loaded: bool


class DashboardResponse(BaseModel):
    total_customers: int
    churned_customers: int
    churn_rate: float
    high_risk_count: int
    persona_count: int
    avg_tenure: float
    avg_monthly_charges: float


class ChurnDriver(BaseModel):
    feature: str
    importance: float
    rank: int


class PersonaProfile(BaseModel):
    cluster_id: int
    persona_name: str
    count: int
    pct_of_customers: float
    avg_tenure: float
    avg_monthly_charges: float
    avg_total_charges: float
    churn_rate: float
    characteristics: str
    top_contract: str
    top_internet: str
    top_payment: str


class CustomerRecord(BaseModel):
    customerID: str
    tenure: int
    Contract: str
    MonthlyCharges: float
    InternetService: str
    Churn: str
    risk_level: Optional[str] = None
    persona_name: Optional[str] = None
    cluster_id: Optional[int] = None
    churn_probability: Optional[float] = None


class CustomersResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CustomerRecord]


class ChartSeriesResponse(BaseModel):
    """Generic chart payload for the React dashboard (real aggregated stats)."""
    churn_distribution: List[Dict[str, Any]]
    churn_by_contract: List[Dict[str, Any]]
    churn_by_tenure: List[Dict[str, Any]]
    persona_distribution: List[Dict[str, Any]]
    top_drivers: List[Dict[str, Any]]
