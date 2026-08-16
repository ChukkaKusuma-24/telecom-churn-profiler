"""
evaluate.py
-----------
Full evaluation of the churn Decision Tree:
  - Accuracy, Precision, Recall, F1, Confusion Matrix, ROC-AUC
  - Feature importance CSV + chart
  - Writes ml/outputs/evaluation.txt and charts under ml/outputs/charts/
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # non-interactive backend for scripts
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    auc,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import (  # noqa: E402
    CHARTS_DIR,
    OUTPUTS_DIR,
    RANDOM_STATE,
    ensure_dirs,
    load_and_prepare,
    load_joblib,
)


def extract_feature_importances(pipeline, feature_names: list) -> pd.DataFrame:
    """Pull importances from the fitted DecisionTree and rank them."""
    tree = pipeline.named_steps["model"]
    importances = tree.feature_importances_
    if len(importances) != len(feature_names):
        raise ValueError(
            f"Importance length ({len(importances)}) != feature names ({len(feature_names)})"
        )

    fi = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importances,
        }
    )
    fi = fi.sort_values("importance", ascending=False).reset_index(drop=True)
    fi["rank"] = fi.index + 1
    return fi[["feature", "importance", "rank"]]


def plot_confusion_matrix(cm: np.ndarray, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["No Churn", "Churn"],
        yticklabels=["No Churn", "Churn"],
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix — Decision Tree")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"[evaluate] Saved chart: {out_path}")


def plot_roc_curve(y_true, y_proba, out_path: Path) -> float:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#1f77b4", lw=2, label=f"ROC (AUC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve — Decision Tree")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"[evaluate] Saved chart: {out_path}")
    return float(roc_auc)


def plot_feature_importance(fi: pd.DataFrame, out_path: Path, top_n: int = 15) -> None:
    top = fi.head(top_n).iloc[::-1]  # reverse for horizontal bar
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top["feature"], top["importance"], color="#2a9d8f")
    ax.set_xlabel("Importance")
    ax.set_title(f"Top {top_n} Churn Drivers (Decision Tree)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"[evaluate] Saved chart: {out_path}")


def run_evaluation() -> None:
    ensure_dirs()
    pipeline = load_joblib("churn_model.pkl")
    meta = load_joblib("feature_columns.pkl")
    feature_names = meta["feature_names"]

    cleaned, X, y, _, _ = load_and_prepare()

    # Same split as training for fair hold-out evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=meta.get("test_size", 0.2),
        random_state=RANDOM_STATE,
        stratify=y,
    )

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["No Churn", "Churn"])

    # Feature importances
    fi = extract_feature_importances(pipeline, feature_names)
    fi_path = OUTPUTS_DIR / "feature_importance.csv"
    fi.to_csv(fi_path, index=False)
    print(f"[evaluate] Saved: {fi_path}")

    # Charts
    plot_confusion_matrix(cm, CHARTS_DIR / "confusion_matrix.png")
    plot_roc_curve(y_test, y_proba, CHARTS_DIR / "roc_curve.png")
    plot_feature_importance(fi, CHARTS_DIR / "feature_importance.png")

    # Extra exploratory charts from real data (for dashboard context / docs)
    _plot_churn_distribution(cleaned, CHARTS_DIR / "churn_distribution.png")
    _plot_churn_by_contract(cleaned, CHARTS_DIR / "churn_by_contract.png")
    _plot_churn_by_tenure(cleaned, CHARTS_DIR / "churn_by_tenure.png")

    # Text report
    lines = [
        "Telecom Churn — Evaluation Report",
        "=" * 50,
        f"Model: DecisionTreeClassifier (max_depth={meta.get('max_depth')}, "
        f"min_samples_leaf={meta.get('min_samples_leaf')})",
        f"Random state: {RANDOM_STATE}",
        f"Train size: {meta.get('n_train')}, Test size: {meta.get('n_test')}",
        "",
        "Metrics (hold-out test set)",
        "-" * 30,
        f"Accuracy:  {acc:.4f}",
        f"Precision: {prec:.4f}",
        f"Recall:    {rec:.4f}",
        f"F1 Score:  {f1:.4f}",
        f"ROC-AUC:   {roc:.4f}",
        "",
        "Confusion Matrix [[TN, FP], [FN, TP]]:",
        str(cm.tolist()),
        "",
        "Classification Report:",
        report,
        "",
        "Top 10 Feature Importances:",
        fi.head(10).to_string(index=False),
        "",
        "Notes:",
        "- Metrics reflect this dataset and split only; they are not business guarantees.",
        "- Feature importance is model-based (Decision Tree Gini importance).",
        "- This is an educational telecom analytics project, not medical/financial advice.",
    ]
    report_path = OUTPUTS_DIR / "evaluation.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[evaluate] Saved: {report_path}")
    print("\n".join(lines[:20]))


def _plot_churn_distribution(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    counts = df["Churn"].value_counts().sort_index()
    labels = ["No Churn" if i == 0 else "Churn" for i in counts.index]
    ax.bar(labels, counts.values, color=["#457b9d", "#e63946"])
    ax.set_ylabel("Count")
    ax.set_title("Churn Distribution")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _plot_churn_by_contract(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    rate = df.groupby("Contract")["Churn"].mean().sort_values(ascending=False)
    ax.bar(rate.index.astype(str), rate.values, color="#f4a261")
    ax.set_ylabel("Churn Rate")
    ax.set_title("Churn Rate by Contract Type")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _plot_churn_by_tenure(df: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4))
    bins = [0, 12, 24, 48, 72]
    labels = ["0-12", "13-24", "25-48", "49-72"]
    tenure_bin = pd.cut(df["tenure"], bins=bins, labels=labels, include_lowest=True)
    rate = df.groupby(tenure_bin, observed=True)["Churn"].mean()
    ax.bar(rate.index.astype(str), rate.values, color="#2a9d8f")
    ax.set_ylabel("Churn Rate")
    ax.set_xlabel("Tenure (months)")
    ax.set_title("Churn Rate by Tenure Bin")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    try:
        run_evaluation()
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)
    print("[evaluate] Done.")
