import json
import os

import joblib
import requests
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

    missing = [f for f in ALL_FEATURES if f not in payload]
    if missing:
        return {
            "error": "Missing required fields",
            "missing_fields": missing,
            "required_fields": ALL_FEATURES,
        }, 400

    row = {f: payload[f] for f in ALL_FEATURES}
    import pandas as pd

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

if __name__ == "__main__":
    print(f"ML Engine starting on http://localhost:{config.ML_ENGINE_PORT}")
    app.run(host="0.0.0.0", port=config.ML_ENGINE_PORT, debug=True)
