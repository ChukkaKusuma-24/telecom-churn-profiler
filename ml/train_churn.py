"""
train_churn.py
--------------
Train a DecisionTreeClassifier for churn prediction.

Saves:
  ml/models/churn_model.pkl   — full sklearn Pipeline (preprocess + tree)
  ml/models/feature_columns.pkl — metadata (numeric/categorical cols, feature names)
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

# Allow running as: python ml/train_churn.py
sys.path.insert(0, str(Path(__file__).resolve().parent))

from preprocess import (  # noqa: E402
    MODELS_DIR,
    RANDOM_STATE,
    build_preprocessor,
    ensure_dirs,
    get_feature_names_from_preprocessor,
    load_and_prepare,
    save_joblib,
)


def train_churn_model(
    max_depth: int = 8,
    min_samples_leaf: int = 20,
    test_size: float = 0.2,
) -> Pipeline:
    """
    Train Decision Tree churn model with stratified split.
    Returns the fitted Pipeline.
    """
    ensure_dirs()
    cleaned, X, y, numeric_cols, categorical_cols = load_and_prepare()

    print(f"[train_churn] Samples: {len(X)}, Features: {X.shape[1]}")
    print(f"[train_churn] Churn rate: {y.mean():.4f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    preprocessor = build_preprocessor(numeric_cols, categorical_cols)
    clf = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=RANDOM_STATE,
        class_weight="balanced",  # help with class imbalance
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", clf),
        ]
    )

    print("[train_churn] Fitting pipeline...")
    pipeline.fit(X_train, y_train)

    # Quick hold-out metrics (full report is in evaluate.py)
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print("\n--- Hold-out metrics ---")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.4f}")
    print(f"F1:        {f1_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC:   {roc_auc_score(y_test, y_proba):.4f}")
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=["No Churn", "Churn"]))

    # Feature names after transform (for driver analysis / predict explanations)
    fitted_pre = pipeline.named_steps["preprocess"]
    feature_names = get_feature_names_from_preprocessor(
        fitted_pre, numeric_cols, categorical_cols
    )

    meta = {
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "feature_names": feature_names,
        "random_state": RANDOM_STATE,
        "test_size": test_size,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "max_depth": max_depth,
        "min_samples_leaf": min_samples_leaf,
    }

    save_joblib(pipeline, "churn_model.pkl")
    save_joblib(meta, "feature_columns.pkl")

    # Also persist train/test indices indirectly by saving a small metrics dict
    # used by evaluate.py for consistency checks
    quick_metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }
    save_joblib(quick_metrics, "churn_holdout_metrics.pkl")

    print(f"\n[train_churn] Artifacts saved under {MODELS_DIR}")
    return pipeline


if __name__ == "__main__":
    try:
        train_churn_model()
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)
    print("[train_churn] Done.")
