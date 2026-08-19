"""
Trains a customer churn classifier on the Telco churn dataset.

Can be run directly:
    python train.py
or imported and called from the Flask app (see app.py -> POST /train).
"""
import json
import os
import time

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import config

NUMERIC_FEATURES = ["Tenure Months", "Monthly Charges", "Total Charges"]
CATEGORICAL_FEATURES = [
    "Gender",
    "Senior Citizen",
    "Partner",
    "Dependents",
    "Phone Service",
    "Multiple Lines",
    "Internet Service",
    "Online Security",
    "Online Backup",
    "Device Protection",
    "Tech Support",
    "Streaming TV",
    "Streaming Movies",
    "Contract",
    "Paperless Billing",
    "Payment Method",
]
TARGET = "Churn Value"
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def _load_dataset(path):
    df = pd.read_excel(path)

    # Total Charges is sometimes blank for brand-new customers (tenure 0)
    df["Total Charges"] = pd.to_numeric(df["Total Charges"], errors="coerce")
    df["Total Charges"] = df["Total Charges"].fillna(0)

    missing = [c for c in ALL_FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Training data is missing expected columns: {missing}")

    return df[ALL_FEATURES + [TARGET]].dropna()


def build_pipeline():
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline(steps=[("preprocess", preprocessor), ("model", model)])


def train_model(data_path=None):
    data_path = data_path or config.TRAINING_DATA_PATH
    df = _load_dataset(data_path)

    X = df[ALL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(round(accuracy_score(y_test, y_pred), 4)),
        "precision": float(round(precision_score(y_test, y_pred), 4)),
        "recall": float(round(recall_score(y_test, y_pred), 4)),
        "f1": float(round(f1_score(y_test, y_pred), 4)),
        "roc_auc": float(round(roc_auc_score(y_test, y_prob), 4)),
    }

    # Extract Top 15 Feature Importances
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    
    # Convert feature importances explicitly to float dictionary values
    top_importances = {
        k: float(v)
        for k, v in (
            pd.Series(importances, index=feature_names)
            .sort_values(ascending=False)
            .head(15)
            .round(4)
            .to_dict()
        ).items()
    }

    os.makedirs(config.MODEL_DIR, exist_ok=True)
    joblib.dump(pipeline, config.MODEL_PATH)

    metadata = {
        "model_version": time.strftime("v%Y%m%d-%H%M%S"),
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_train_rows": len(X_train),
        "n_test_rows": len(X_test),
        "features": ALL_FEATURES,
        "metrics": metrics,
        "top_feature_importances": top_importances,
    }
    
    with open(config.METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


if __name__ == "__main__":
    result = train_model()
    print(json.dumps(result, indent=2))
    