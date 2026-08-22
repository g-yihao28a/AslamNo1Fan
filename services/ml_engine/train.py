"""
Trains a customer churn classifier on the Telco churn dataset.

Can be run directly:
    python train.py
or imported and called from the Flask app (see app.py -> POST /train).
"""
import json
import logging
import os
import time

import joblib
import pandas as pd
import requests
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Maps database snake_case columns to the pipeline's expected Title Case features
DB_COLUMN_MAPPING = {
    "tenure_in_months": "Tenure Months",
    "monthly_charge": "Monthly Charges",
    "total_charges": "Total Charges",
    "gender": "Gender",
    "senior_citizen": "Senior Citizen",
    "partner": "Partner",
    "dependents": "Dependents",
    "phone_service": "Phone Service",
    "multiple_lines": "Multiple Lines",
    "internet_service": "Internet Service",
    "online_security": "Online Security",
    "online_backup": "Online Backup",
    "device_protection": "Device Protection",
    "tech_support": "Tech Support",
    "streaming_tv": "Streaming TV",
    "streaming_movies": "Streaming Movies",
    "contract": "Contract",
    "paperless_billing": "Paperless Billing",
    "payment_method": "Payment Method",
    "churn_value": "Churn Value",
}


def _load_dataset(endpoint_url=None):
    """Fetch live data from the database microservice via a GET request."""
    url = endpoint_url or f"{config.API_GATEWAY_URL.rstrip('/')}/database/customers/full"
    logger.info(f"Fetching dataset via GET: {url}")
    
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch data from {url}: HTTP {response.status_code}")

    payload = response.json()
    records = payload if isinstance(payload, list) else payload.get("customers", [])
    if not records:
        raise ValueError("Database returned 0 customer records for training.")

    df = pd.DataFrame(records)

    # Standardize database column names
    df = df.rename(columns=DB_COLUMN_MAPPING)

    # Convert numeric fields
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Ensure target column exists and is numeric integer
    if TARGET not in df.columns and "churn_label" in df.columns:
        df[TARGET] = (df["churn_label"].astype(str).str.strip().str.lower() == "yes").astype(int)
    elif TARGET in df.columns:
        df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce").fillna(0).astype(int)

    missing = [c for c in ALL_FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Database dataset is missing expected columns: {missing}")

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


def train_model(endpoint_url=None):
    df = _load_dataset(endpoint_url)

    X = df[ALL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(round(accuracy_score(y_test, y_pred), 4)),
        "precision": float(round(precision_score(y_test, y_pred, zero_division=0), 4)),
        "recall": float(round(recall_score(y_test, y_pred, zero_division=0), 4)),
        "f1": float(round(f1_score(y_test, y_pred, zero_division=0), 4)),
        "roc_auc": float(round(roc_auc_score(y_test, y_prob), 4)) if len(y.unique()) > 1 else 0.0,
    }

    # Extract Top 15 Feature Importances
    feature_names = pipeline.named_steps["preprocess"].get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    
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
