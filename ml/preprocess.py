"""
preprocess.py
-------------
Shared data loading and preprocessing for the Telecom Churn Profiler.

Important:
- Never invent data. If the CSV is missing, raise a clear error.
- Drop customerID (identifier, not a feature).
- Convert TotalCharges to numeric and handle missing values.
- Map Churn Yes/No -> 1/0 for supervised learning.
- Build a ColumnTransformer so train and predict use identical encoding.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ---------------------------------------------------------------------------
# Paths (project-root relative)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "telco_customer_churn.csv"
MODELS_DIR = Path(__file__).resolve().parent / "models"
OUTPUTS_DIR = Path(__file__).resolve().parent / "outputs"
CHARTS_DIR = OUTPUTS_DIR / "charts"

RANDOM_STATE = 42

# Columns that must never be used as ML features (leakage / ID)
ID_COL = "customerID"
TARGET_COL = "Churn"

# Expected columns in the IBM / Kaggle Telco Customer Churn dataset
EXPECTED_COLUMNS = [
    "customerID",
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
    "Churn",
]


def ensure_dirs() -> None:
    """Create models/outputs/charts directories if they do not exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def get_dataset_path() -> Path:
    """Return the CSV path or raise a helpful error if missing."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at:\n  {DATA_PATH}\n\n"
            "Please download the Telco Customer Churn CSV and place it exactly at:\n"
            f"  {DATA_PATH}\n\n"
            "Common source: Kaggle — 'Telco Customer Churn' (IBM sample).\n"
            "Do not invent or fabricate customer data."
        )
    return DATA_PATH


def load_raw_data(path: Path | None = None) -> pd.DataFrame:
    """
    Load the raw CSV and validate required columns exist.
    Does not invent rows or columns.
    """
    csv_path = path or get_dataset_path()
    df = pd.read_csv(csv_path)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing expected columns: {missing}\n"
            f"Found columns: {list(df.columns)}\n"
            "Please use the standard Telco Customer Churn dataset."
        )
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a raw telco dataframe:
    - Convert TotalCharges to numeric (blank strings -> NaN)
    - Drop rows with missing TotalCharges after conversion
    - Map Churn Yes/No -> 1/0 if present
    - Ensure SeniorCitizen is int
    """
    df = df.copy()

    # TotalCharges is often stored as object with blank strings
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    # Drop rows where TotalCharges could not be parsed
    before = len(df)
    df = df.dropna(subset=["TotalCharges"]).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"[preprocess] Dropped {dropped} row(s) with missing TotalCharges.")

    # Map target if present (Yes/No -> 1/0). Handles object / StringDtype / already numeric.
    if TARGET_COL in df.columns:
        sample = df[TARGET_COL].dropna().astype(str).str.strip().str.lower()
        if sample.isin(["yes", "no"]).any():
            mapped = (
                df[TARGET_COL]
                .astype(str)
                .str.strip()
                .str.lower()
                .map({"yes": 1, "no": 0, "1": 1, "0": 0})
            )
            if mapped.isna().any():
                bad = df.loc[mapped.isna(), TARGET_COL].unique()[:5]
                raise ValueError(f"Unexpected Churn values (examples): {bad}")
            df[TARGET_COL] = mapped.astype(int)
        else:
            df[TARGET_COL] = pd.to_numeric(df[TARGET_COL], errors="raise").astype(int)

    if "SeniorCitizen" in df.columns:
        df["SeniorCitizen"] = df["SeniorCitizen"].astype(int)

    return df


def get_feature_column_lists(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Split feature columns into numeric vs categorical.
    Excludes customerID and Churn.
    """
    feature_df = df.drop(columns=[c for c in [ID_COL, TARGET_COL] if c in df.columns])

    numeric_cols = feature_df.select_dtypes(
        include=["number"]
    ).columns.tolist()

    # Include object, category, bool, and pandas StringDtype
    categorical_cols = [
        c
        for c in feature_df.columns
        if c not in numeric_cols
    ]

    return numeric_cols, categorical_cols


def build_preprocessor(
    numeric_cols: List[str], categorical_cols: List[str]
) -> ColumnTransformer:
    """
    Build a ColumnTransformer:
    - Numeric: median impute (safety net)
    - Categorical: most-frequent impute + one-hot encode
    """
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ],
        remainder="drop",
    )
    return preprocessor


def get_feature_names_from_preprocessor(
    preprocessor: ColumnTransformer,
    numeric_cols: List[str],
    categorical_cols: List[str],
) -> List[str]:
    """Recover human-readable feature names after one-hot encoding."""
    names: List[str] = list(numeric_cols)
    try:
        ohe = preprocessor.named_transformers_["cat"].named_steps["onehot"]
        cat_names = ohe.get_feature_names_out(categorical_cols).tolist()
        names.extend(cat_names)
    except Exception:
        names.extend(categorical_cols)
    return names


def prepare_xy(
    df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.Series, List[str], List[str]]:
    """
    From a cleaned dataframe, return X (features), y (target),
    and the numeric/categorical column lists.
    """
    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found after cleaning.")

    numeric_cols, categorical_cols = get_feature_column_lists(df)
    feature_cols = numeric_cols + categorical_cols

    X = df[feature_cols].copy()
    y = df[TARGET_COL].copy()
    return X, y, numeric_cols, categorical_cols


def load_and_prepare() -> Tuple[
    pd.DataFrame, pd.DataFrame, pd.Series, List[str], List[str]
]:
    """
    Convenience: load raw CSV -> clean -> split into full cleaned df, X, y, col lists.
    """
    ensure_dirs()
    raw = load_raw_data()
    cleaned = clean_dataframe(raw)
    X, y, numeric_cols, categorical_cols = prepare_xy(cleaned)
    return cleaned, X, y, numeric_cols, categorical_cols


def save_joblib(obj, filename: str) -> Path:
    """Save a joblib artifact under ml/models/."""
    ensure_dirs()
    path = MODELS_DIR / filename
    joblib.dump(obj, path)
    # Avoid UnicodeEncodeError on Windows consoles with non-ASCII paths
    print(f"[preprocess] Saved: {path.name} -> ml/models/")
    return path


def load_joblib(filename: str):
    """Load a joblib artifact from ml/models/."""
    path = MODELS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found: {path}\n"
            "Run the training scripts first:\n"
            "  python ml/train_churn.py\n"
            "  python ml/train_segments.py"
        )
    return joblib.load(path)


def dataset_summary(df: pd.DataFrame) -> dict:
    """Return basic real stats from the cleaned dataframe (no invented numbers)."""
    summary = {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "columns": list(df.columns),
    }
    if TARGET_COL in df.columns:
        churn_count = int(df[TARGET_COL].sum())
        summary["churn_count"] = churn_count
        summary["churn_rate"] = float(churn_count / len(df)) if len(df) else 0.0
    return summary


if __name__ == "__main__":
    print("=" * 60)
    print("Telecom Churn — preprocess verification")
    print("=" * 60)
    try:
        cleaned, X, y, num_cols, cat_cols = load_and_prepare()
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)

    summary = dataset_summary(cleaned)
    print(f"Rows: {summary['n_rows']}")
    print(f"Columns: {summary['n_columns']}")
    print(f"Churn count: {summary.get('churn_count')}")
    print(f"Churn rate: {summary.get('churn_rate'):.4f}")
    print(f"Numeric features ({len(num_cols)}): {num_cols}")
    print(f"Categorical features ({len(cat_cols)}): {cat_cols}")
    print(f"X shape: {X.shape}, y shape: {y.shape}")
    print("Missing values per feature column:")
    print(X.isna().sum()[X.isna().sum() > 0] if X.isna().any().any() else "  (none)")
    print("OK — preprocessing pipeline is ready.")
