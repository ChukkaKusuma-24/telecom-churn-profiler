# Telecom Churn Driver Discovery & Persona Profiler

Undergraduate-level AIML project that predicts telecom customer churn, surfaces the main drivers of churn, segments customers into behavioral personas with K-Means, and serves everything through a FastAPI + React dashboard.

> Educational telecom analytics demo — **not** medical or financial advice. Metrics reflect this dataset and model only.

---

## Problem statement

Telecom providers lose revenue when customers leave (churn). Understanding *who* is likely to churn, *why*, and *how* customers group behaviorally helps retention teams prioritize outreach. This project turns the public **Telco Customer Churn** dataset into a reproducible ML pipeline and interactive app.

## Objectives

1. Predict churn with a **Decision Tree** classifier.
2. Discover major churn drivers via feature importance.
3. Segment customers into **K-Means** personas (k chosen by silhouette/elbow — not assumed).
4. Expose results through a **FastAPI** backend.
5. Visualize stats, drivers, personas, and single-customer predictions in a **React** dashboard.

## Tech stack

| Layer | Tools |
|-------|--------|
| ML | Python 3, Pandas, NumPy, Scikit-learn, Matplotlib, Seaborn, Joblib |
| Models | `DecisionTreeClassifier`, `KMeans` |
| Backend | FastAPI, Uvicorn, Pydantic |
| Frontend | React, Vite, JavaScript, CSS, Recharts |

No TensorFlow/PyTorch. No database yet (CSV + joblib artifacts; designed so MySQL can be added later).

## Architecture

```
CSV (data/) → preprocess → train_churn / train_segments / evaluate
                              ↓
                     ml/models/*.pkl + ml/outputs/*
                              ↓
                     FastAPI (backend/)  ←→  React (frontend/)
```

- **ML code** lives under `ml/` and is separate from the API.
- **API** loads artifacts and the CSV; it does not retrain models.
- **Frontend** only displays values returned by the API (no hardcoded business stats).

## Folder structure

```
telecom-churn-profiler/
├── data/telco_customer_churn.csv
├── ml/
│   ├── preprocess.py
│   ├── train_churn.py
│   ├── train_segments.py
│   ├── evaluate.py
│   ├── predict.py
│   ├── models/          # churn_model.pkl, scaler.pkl, clustering_model.pkl, ...
│   └── outputs/         # feature_importance.csv, cluster_profiles.csv, evaluation.txt, charts/
├── backend/
│   ├── main.py
│   └── schemas.py
├── frontend/
│   └── src/             # App, pages, components, api.js, styles
├── requirements.txt
├── README.md
└── .gitignore
```

## Dataset

**Telco Customer Churn** (IBM sample / Kaggle).

Place the file exactly here:

```
telecom-churn-profiler/data/telco_customer_churn.csv
```

Expected columns include: `customerID`, `gender`, `SeniorCitizen`, `Partner`, `Dependents`, `tenure`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges`, `Churn`.

If the CSV is missing, training and API data endpoints will fail with a clear path message — the project never invents customer rows.

## Preprocessing

Implemented in `ml/preprocess.py`:

- Drop identifier `customerID` from features (never used for ML).
- Convert `TotalCharges` to numeric; drop rows that cannot be parsed.
- Map `Churn` Yes/No → 1/0.
- One-hot encode categoricals via `ColumnTransformer` + `Pipeline`.
- Same preprocessor is embedded in the saved churn pipeline (train ≡ predict).
- Fixed `random_state=42`; stratified train/test split.

**Leakage rule:** `Churn` and `customerID` are never used as input features.

## Decision Tree model

`ml/train_churn.py` trains a `DecisionTreeClassifier` inside a sklearn `Pipeline` with balanced class weights, `max_depth=8`, `min_samples_leaf=20`.

Hold-out metrics are written by `ml/evaluate.py` to `ml/outputs/evaluation.txt` (Accuracy, Precision, Recall, F1, Confusion Matrix, ROC-AUC) plus charts under `ml/outputs/charts/`.

Do not over-interpret accuracy: this is a teaching project on one public dataset.

## Churn-driver analysis

Tree **Gini feature importances** are exported to `ml/outputs/feature_importance.csv` (`feature`, `importance`, `rank`, sorted descending) and plotted. The API serves `/churn-drivers`; the dashboard charts the top drivers from `/charts`.

## K-Means clustering & personas

`ml/train_segments.py`:

- Excludes `Churn` and `customerID`.
- One-hot encodes categoricals, then `StandardScaler`.
- Searches `k` from 2–8 using inertia (elbow) and **silhouette**; selects best silhouette.
- Writes `ml/outputs/cluster_profiles.csv` with real per-cluster stats.
- Auto-generates persona names from cluster characteristics (tenure / spend / churn-rate bands) — names are not hardcoded up front.

Artifacts: `clustering_model.pkl`, `scaler.pkl`.

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Status / models loaded |
| GET | `/dashboard` | Totals, churn rate, high-risk count, persona count |
| GET | `/churn-drivers` | Top drivers from CSV |
| GET | `/personas` | Persona profiles |
| POST | `/predict` | Single-customer prediction |
| GET | `/customers` | Searchable / filterable / paginated table |
| GET | `/charts` | Aggregations for Recharts |

CORS is enabled for the Vite dev server (`localhost:5173`). Validation via Pydantic; missing models/data return HTTP 503 with guidance.

## Frontend

React + Vite app with routes:

- **Dashboard** — stat cards + churn distribution, drivers, contract/tenure churn, persona sizes.
- **Predict** — form → risk level, probability, persona, risk factors.
- **Personas** — cards with count, avg tenure, charges, churn rate, characteristics.
- **Customers** — searchable / filterable / paginated table with risk & persona.

Distinct colors for Low / Medium / High risk. Loading, error, and empty states included.

---

## Installation

### 1. Python

```bash
cd telecom-churn-profiler
python -m pip install -r requirements.txt
```

### 2. Dataset

Ensure the CSV is at `data/telco_customer_churn.csv` (see Dataset section).

### 3. Frontend

```bash
cd frontend
npm install
```

## Exact commands

### Train models & evaluate

From the project root:

```bash
python ml/preprocess.py
python ml/train_churn.py
python ml/evaluate.py
python ml/train_segments.py
python ml/predict.py
```

### Start backend

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Start frontend

```bash
cd frontend
npm run dev
```

Open the URL Vite prints (usually http://127.0.0.1:5173).

Optional: set `VITE_API_URL` if the API is not on `http://127.0.0.1:8000`.

## Example prediction

`POST /predict` body (illustrative schema — results depend on your trained models):

```json
{
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
  "TotalCharges": 29.85
}
```

Response includes `prediction`, `probability`, `risk_level`, `risk_factors`, `persona`, and `explanation`.

## Future enhancements

- Persist customers / predictions in **MySQL** (API contracts already keep persistence behind loaders).
- Hyperparameter tuning / cross-validation for the tree.
- Compare Logistic Regression or Gradient Boosting as baselines.
- Auth for the dashboard; deploy API + UI separately.
- SHAP or permutation importance for richer explanations.

## License / data note

Use the Telco Customer Churn dataset according to its source license (IBM / Kaggle). This repository does not claim ownership of the dataset.
