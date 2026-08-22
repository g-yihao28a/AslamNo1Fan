import json
import os
import io

import joblib
import requests
import pandas as pd
from flask import Flask, jsonify, request

from config import config
from train import ALL_FEATURES, train_model

app = Flask(__name__)

_pipeline = None
_metadata = None


def _load_model():
    """Load the trained pipeline into memory (if it exists)."""
    global _pipeline, _metadata
    if os.path.exists(config.MODEL_PATH):
        _pipeline = joblib.load(config.MODEL_PATH)
    if os.path.exists(config.METADATA_PATH):
        with open(config.METADATA_PATH) as f:
            _metadata = json.load(f)


_load_model()


def _log_inference(customer_id, probability, prediction, model_version):
    """Best-effort write to inference_logs, via the API gateway's
    /database/logs route rather than a direct Postgres connection. Never
    blocks a prediction response."""
    if not customer_id:
        return
    try:
        requests.post(
            f"{config.API_GATEWAY_URL.rstrip('/')}/database/logs",
            json={
                "customer_id": customer_id,
                "churn_probability": probability,
                "predicted_churn": prediction,
                "model_version": model_version,
            },
            timeout=3,
        )
    except requests.exceptions.RequestException as exc:
        app.logger.warning(f"Could not log inference via gateway: {exc}")


@app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "ML engine is running",
        "model_loaded": _pipeline is not None,
    }, 200


@app.route("/model/info", methods=["GET"])
def model_info():
    if _metadata is None:
        return {"error": "No trained model yet. Call POST /train first."}, 404
    return jsonify(_metadata), 200


@app.route("/train", methods=["POST"])
def train():
    """Trains (or retrains) the churn model and reloads it into memory."""
    try:
        metadata = train_model()
        # Guard clause: ensure train_model() didn't silently return None
        if metadata is None:
            metadata = {"status": "success", "message": "Model trained, no metadata returned."}

        # Reload model into memory
        _load_model()
        return jsonify(metadata), 200
    
    except Exception as exc:
        # Always wrap error dictionaries in jsonify() to return a valid Flask response
        return jsonify({"error": str(exc)}), 500    


@app.route("/predict", methods=["POST"])
def predict():
    if _pipeline is None:
        return {
            "error": "No trained model available yet. Call POST /train first."
        }, 503

    payload = request.get_json(silent=True)
    if not payload:
        return {"error": "Request body must be JSON."}, 400

    # ---------------------------------------------------------------------------
    # Fallback normalization: map snake_case and type variations to ALL_FEATURES
    # ---------------------------------------------------------------------------
    feature_fallbacks = {
        "tenure_in_months": "Tenure Months",
        "tenure_months": "Tenure Months",
        "monthly_charge": "Monthly Charges",
        "monthly_charges": "Monthly Charges",
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
    }
    for k, v in list(payload.items()):
        if k in feature_fallbacks and feature_fallbacks[k] not in payload:
            payload[feature_fallbacks[k]] = v

    missing = [f for f in ALL_FEATURES if f not in payload]
    if missing:
        return {
            "error": "Missing required fields",
            "missing_fields": missing,
            "required_fields": ALL_FEATURES,
        }, 400

    row = {f: payload[f] for f in ALL_FEATURES}

    # Numeric coercion for single row DataFrame
    for num_col in ["Tenure Months", "Monthly Charges", "Total Charges"]:
        if num_col in row and row[num_col] is not None:
            try:
                row[num_col] = float(row[num_col])
            except (ValueError, TypeError):
                row[num_col] = 0.0

    X = pd.DataFrame([row])

    try:
        probability = float(_pipeline.predict_proba(X)[0][1])
        prediction = bool(_pipeline.predict(X)[0])
    except Exception as exc:
        return {"error": f"Prediction failed: {exc}"}, 400

    model_version = _metadata.get("model_version") if _metadata else None
    customer_id = payload.get("customer_id")
    _log_inference(customer_id, round(probability, 4), prediction, model_version)

    return jsonify(
        {
            "customer_id": customer_id,
            "churn_probability": round(probability, 4),
            "predicted_churn": prediction,
            "model_version": model_version,
        }
    ), 200

@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    if _pipeline is None:
        return jsonify({"error": "No trained model available yet. Call POST /train first."}), 503

    if "file" not in request.files:
        return jsonify({"error": "No file provided (expected multipart field 'file')"}), 400

    upload = request.files["file"]
    filename = upload.filename.lower()

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(upload.stream)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(upload.stream)
        else:
            return jsonify({"error": "Unsupported file type. Use .csv, .xlsx, or .xls"}), 400

        col_mapping = {
            "tenure_in_months": "Tenure Months",
            "tenure_months": "Tenure Months",
            "monthly_charge": "Monthly Charges",
            "monthly_charges": "Monthly Charges",
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
        }
        df = df.rename(columns=col_mapping)

        for col in ["Tenure Months", "Monthly Charges", "Total Charges"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        missing = [c for c in ALL_FEATURES if c not in df.columns]
        if missing:
            return jsonify({"error": f"Uploaded dataset is missing required features: {missing}"}), 400

        X = df[ALL_FEATURES]
        probabilities = _pipeline.predict_proba(X)[:, 1]
        predictions = _pipeline.predict(X)

        cust_ids = df["customer_id"].tolist() if "customer_id" in df.columns else [f"ROW_{i+1}" for i in range(len(df))]
        model_version = _metadata.get("model_version") if _metadata else None

        results = []
        for cid, prob, pred in zip(cust_ids, probabilities, predictions):
            prob_float = float(round(prob, 4))
            pred_bool = bool(pred)
            risk = "High" if prob_float >= 0.7 else ("Medium" if prob_float >= 0.4 else "Low")

            results.append({
                "customer_id": cid,
                "churn_probability": prob_float,
                "probability": prob_float,
                "predicted_churn": pred_bool,
                "prediction": "Yes" if pred_bool else "No",
                "risk_level": risk,
                "model_version": model_version,
            })

        return jsonify({"predictions": results, "total_records": len(results)}), 200

    except Exception as exc:
        return jsonify({"error": f"Batch prediction failed: {str(exc)}"}), 500


@app.route("/model/reload", methods=["POST"])
def model_reload():
    try:
        _load_model()
        return jsonify({
            "status": "Model and metadata reloaded successfully",
            "model_loaded": _pipeline is not None,
            "version": _metadata.get("model_version") if _metadata else None,
        }), 200
    except Exception as exc:
        return jsonify({"error": f"Reload failed: {str(exc)}"}), 500


if __name__ == "__main__":
    print(f"ML Engine starting on http://localhost:{config.ML_ENGINE_PORT}")
    app.run(host="0.0.0.0", port=config.ML_ENGINE_PORT, debug=True)
