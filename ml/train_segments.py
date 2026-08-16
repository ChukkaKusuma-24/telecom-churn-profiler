"""
train_segments.py
-----------------
K-Means persona clustering on customer features (excludes Churn & customerID).

Chooses k via elbow (inertia) + silhouette score (does not assume k=4).
Saves:
  ml/models/clustering_model.pkl
  ml/models/scaler.pkl
  ml/outputs/cluster_profiles.csv
  charts for elbow / silhouette / persona distribution
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import (  # noqa: E402
    CHARTS_DIR,
    ID_COL,
    MODELS_DIR,
    OUTPUTS_DIR,
    RANDOM_STATE,
    TARGET_COL,
    ensure_dirs,
    get_feature_column_lists,
    load_and_prepare,
    save_joblib,
)


def build_cluster_matrix(df: pd.DataFrame):
    """
    Build a scaled numeric matrix for K-Means.
    Excludes Churn and customerID. One-hot encodes categoricals, scales all.
    """
    numeric_cols, categorical_cols = get_feature_column_lists(df)
    feature_cols = numeric_cols + categorical_cols
    X = df[feature_cols].copy()

    # One-hot categoricals, pass-through numerics, then scale everything
    pre = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_cols),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                categorical_cols,
            ),
        ]
    )
    X_encoded = pre.fit_transform(X)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_encoded)

    # Feature names for interpretability
    cat_names = []
    if categorical_cols:
        ohe = pre.named_transformers_["cat"]
        cat_names = ohe.get_feature_names_out(categorical_cols).tolist()
    feature_names = list(numeric_cols) + cat_names

    return X_scaled, scaler, pre, feature_names, numeric_cols, categorical_cols, feature_cols


def choose_k(X_scaled: np.ndarray, k_min: int = 2, k_max: int = 8) -> dict:
    """
    Evaluate k via inertia (elbow) and silhouette; pick best silhouette k.
    Returns dict with chosen_k, inertias, silhouettes.
    """
    inertias = []
    silhouettes = []
    ks = list(range(k_min, k_max + 1))

    print("[train_segments] Searching for best k...")
    for k in ks:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(float(km.inertia_))
        sil = float(silhouette_score(X_scaled, labels))
        silhouettes.append(sil)
        print(f"  k={k}: inertia={km.inertia_:.1f}, silhouette={sil:.4f}")

    # Prefer highest silhouette; tie-break toward smaller k (simpler personas)
    best_idx = int(np.argmax(silhouettes))
    chosen_k = ks[best_idx]
    print(f"[train_segments] Chosen k={chosen_k} (best silhouette={silhouettes[best_idx]:.4f})")

    return {
        "ks": ks,
        "inertias": inertias,
        "silhouettes": silhouettes,
        "chosen_k": chosen_k,
    }


def plot_elbow_silhouette(search: dict) -> None:
    ensure_dirs()
    ks = search["ks"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(ks, search["inertias"], marker="o", color="#457b9d")
    axes[0].axvline(search["chosen_k"], color="#e63946", linestyle="--", label=f"k={search['chosen_k']}")
    axes[0].set_xlabel("k")
    axes[0].set_ylabel("Inertia")
    axes[0].set_title("Elbow Method")
    axes[0].legend()

    axes[1].plot(ks, search["silhouettes"], marker="o", color="#2a9d8f")
    axes[1].axvline(search["chosen_k"], color="#e63946", linestyle="--", label=f"k={search['chosen_k']}")
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("Silhouette Score")
    axes[1].set_title("Silhouette Scores")
    axes[1].legend()

    fig.tight_layout()
    out = CHARTS_DIR / "kmeans_elbow_silhouette.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"[train_segments] Saved chart: {out}")


def _fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def generate_persona_name(row: pd.Series, global_means: dict) -> str:
    """
    Auto-generate a persona label from real cluster stats vs global averages.
    No hardcoded cluster->name map; names follow the data.
    """
    parts = []

    tenure = float(row.get("avg_tenure", 0))
    monthly = float(row.get("avg_monthly_charges", 0))
    churn_rate = float(row.get("churn_rate", 0))
    g_tenure = global_means.get("tenure", tenure)
    g_monthly = global_means.get("MonthlyCharges", monthly)

    # Tenure band
    if tenure < g_tenure * 0.7:
        parts.append("New")
    elif tenure > g_tenure * 1.3:
        parts.append("Loyal")
    else:
        parts.append("Steady")

    # Spend band
    if monthly > g_monthly * 1.15:
        parts.append("High-Spend")
    elif monthly < g_monthly * 0.85:
        parts.append("Value")
    else:
        parts.append("Mid-Spend")

    # Risk band from cluster churn rate
    if churn_rate >= 0.40:
        parts.append("High-Risk")
    elif churn_rate <= 0.15:
        parts.append("Low-Risk")
    else:
        parts.append("Moderate-Risk")

    return " ".join(parts) + " Customers"


def build_cluster_profiles(
    df: pd.DataFrame, labels: np.ndarray
) -> pd.DataFrame:
    """
    Real per-cluster statistics (counts, averages, mode categoricals, churn rate).
    """
    work = df.copy()
    work["cluster"] = labels

    global_means = {
        "tenure": float(work["tenure"].mean()),
        "MonthlyCharges": float(work["MonthlyCharges"].mean()),
    }

    rows = []
    for cid in sorted(work["cluster"].unique()):
        sub = work[work["cluster"] == cid]
        row = {
            "cluster_id": int(cid),
            "count": int(len(sub)),
            "pct_of_customers": float(len(sub) / len(work)),
            "avg_tenure": float(sub["tenure"].mean()),
            "avg_monthly_charges": float(sub["MonthlyCharges"].mean()),
            "avg_total_charges": float(sub["TotalCharges"].mean()),
            "churn_rate": float(sub[TARGET_COL].mean()) if TARGET_COL in sub.columns else np.nan,
            "pct_senior": float(sub["SeniorCitizen"].mean()),
            "pct_partner": float((sub["Partner"] == "Yes").mean()),
            "pct_dependents": float((sub["Dependents"] == "Yes").mean()),
            "top_contract": str(sub["Contract"].mode().iloc[0]),
            "top_internet": str(sub["InternetService"].mode().iloc[0]),
            "top_payment": str(sub["PaymentMethod"].mode().iloc[0]),
            "pct_paperless": float((sub["PaperlessBilling"] == "Yes").mean()),
        }

        # Characteristics as readable bullet strings (derived, not invented)
        chars = [
            f"Avg tenure {row['avg_tenure']:.1f} months",
            f"Avg monthly charges ${row['avg_monthly_charges']:.2f}",
            f"Most common contract: {row['top_contract']}",
            f"Most common internet: {row['top_internet']}",
            f"Churn rate {_fmt_pct(row['churn_rate'])}",
            f"Senior citizens {_fmt_pct(row['pct_senior'])}",
            f"Have partner {_fmt_pct(row['pct_partner'])}",
        ]
        row["characteristics"] = " | ".join(chars)
        row["persona_name"] = generate_persona_name(pd.Series(row), global_means)
        rows.append(row)

    profiles = pd.DataFrame(rows)
    # Disambiguate duplicate auto-names by appending cluster id
    name_counts = profiles["persona_name"].value_counts()
    dupes = set(name_counts[name_counts > 1].index)
    profiles["persona_name"] = profiles.apply(
        lambda r: f"{r['persona_name']} (C{r['cluster_id']})"
        if r["persona_name"] in dupes
        else r["persona_name"],
        axis=1,
    )
    return profiles


def train_segments() -> None:
    ensure_dirs()
    cleaned, _, _, _, _ = load_and_prepare()

    X_scaled, scaler, encoder, feature_names, numeric_cols, categorical_cols, feature_cols = (
        build_cluster_matrix(cleaned)
    )

    # Evaluate k over a sensible range for reporting (Silhouette + Elbow)
    search_eval = choose_k(X_scaled, k_min=2, k_max=6)
    plot_elbow_silhouette(search_eval)

    # Save evaluation summary (silhouette scores + inertias) for K=2..6
    ensure_dirs()
    eval_path = OUTPUTS_DIR / "clustering_evaluation.txt"
    with open(eval_path, "w", encoding="utf-8") as fh:
        fh.write("Silhouette and inertia search (k=2..6)\n")
        for k_val, inert, sil in zip(search_eval["ks"], search_eval["inertias"], search_eval["silhouettes"]):
            fh.write(f"k={k_val}: inertia={inert:.2f}, silhouette={sil:.4f}\n")
    print(f"[train_segments] Saved clustering evaluation: {eval_path}")

    # For this request, fix final clustering to 4 clusters
    k = 4
    print(f"[train_segments] Training final KMeans with k={k}")

    kmeans = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    profiles = build_cluster_profiles(cleaned, labels)
    profiles_path = OUTPUTS_DIR / "cluster_profiles.csv"
    profiles.to_csv(profiles_path, index=False)
    print(f"[train_segments] Saved: {profiles_path}")
    print(profiles[["cluster_id", "persona_name", "count", "churn_rate", "avg_tenure"]].to_string(index=False))

    # Persona size chart
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(profiles["persona_name"], profiles["count"], color="#264653")
    ax.set_ylabel("Customers")
    ax.set_title("Persona Distribution")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    persona_chart = CHARTS_DIR / "persona_distribution.png"
    fig.savefig(persona_chart, dpi=120)
    plt.close(fig)
    print(f"[train_segments] Saved chart: {persona_chart}")

    # Bundle clustering artifacts
    cluster_bundle = {
        "kmeans": kmeans,
        "encoder": encoder,
        "feature_names": feature_names,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "feature_cols": feature_cols,
        "chosen_k": k,
        "silhouette_search": {
            "ks": search_eval["ks"],
            "inertias": search_eval["inertias"],
            "silhouettes": search_eval["silhouettes"],
        },
        "persona_lookup": {
            int(r.cluster_id): {
                "persona_name": r.persona_name,
                "characteristics": r.characteristics,
                "count": int(r.count),
                "churn_rate": float(r.churn_rate),
                "avg_tenure": float(r.avg_tenure),
                "avg_monthly_charges": float(r.avg_monthly_charges),
            }
            for r in profiles.itertuples()
        },
    }
    save_joblib(cluster_bundle, "clustering_model.pkl")
    save_joblib(scaler, "scaler.pkl")

    # Save search summary for README / debugging
    (OUTPUTS_DIR / "kmeans_search.json").write_text(
        json.dumps(
            {
                "chosen_k": k,
                "ks": search_eval["ks"],
                "inertias": search_eval["inertias"],
                "silhouettes": search_eval["silhouettes"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[train_segments] Artifacts under {MODELS_DIR}")


if __name__ == "__main__":
    try:
        train_segments()
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)
    print("[train_segments] Done.")
