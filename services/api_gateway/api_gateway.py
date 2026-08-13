from flask import Flask, jsonify, request
import requests
import os
from config import config

app = Flask(__name__)

# Load variables from config or environment
GATEWAY_PORT = getattr(config, "GATEWAY_PORT", 8008)
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", getattr(config, "ML_ENGINE_URL", "http://ml_engine:8010"))


# ---------------------------------------------------------------------------
# Health Check Endpoints
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health_check():
    """Local Gateway health check."""
    return jsonify({"status": "Flask API Gateway is running"}), 200


@app.route("/health/ml-engine", methods=["GET"])
def check_ml_engine():
    """Checks communication between API Gateway and ML Engine."""
    target_url = f"{ML_ENGINE_URL}/health"
    
    try:
        response = requests.get(target_url, timeout=3.0)
        
        # Safely parse JSON from ML engine
        try:
            ml_response = response.json()
        except ValueError:
            ml_response = response.text

        if response.status_code == 200:
            return jsonify({
                "status": "healthy",
                "message": "Gateway can communicate with ML Engine",
                "ml_engine_response": ml_response
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "message": f"ML Engine responded with status code {response.status_code}",
                "ml_engine_response": ml_response
            }), 502

    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "unreachable",
            "message": f"Could not connect to ML Engine at {ML_ENGINE_URL}. Check network/container status."
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "timeout",
            "message": f"Request to ML Engine at {ML_ENGINE_URL} timed out."
        }), 504


# ---------------------------------------------------------------------------
# Prediction Proxy Routes
# ---------------------------------------------------------------------------

@app.route("/api/ml/predict", methods=["POST"])
@app.route("/predict", methods=["POST"])  # Alias to support both route formats
def proxy_predict():
    """
    Proxies customer prediction payloads from Streamlit/Web UI to ML Engine.
    Handles non-JSON or error payloads safely to avoid crashing downstream callers.
    """
    target_url = f"{ML_ENGINE_URL}/predict"

    # 1. Validate incoming JSON payload from frontend
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "Request payload must be valid JSON."}), 400

    try:
        # 2. Forward request to ML Engine
        response = requests.post(target_url, json=payload, timeout=10.0)

        # 3. Safely decode response from ML Engine
        try:
            data = response.json()
        except ValueError:
            # Fallback if ML Engine panics or returns HTML error page
            data = {
                "error": "ML Engine returned a non-JSON response.",
                "status_code": response.status_code,
                "raw_response": response.text
            }

        return jsonify(data), response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": f"Gateway cannot connect to ML Engine at {ML_ENGINE_URL}. Check container status."
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "ML Engine timed out while processing prediction."
        }), 504

    except Exception as exc:
        return jsonify({
            "error": f"An unexpected gateway error occurred: {str(exc)}"
        }), 500


# ---------------------------------------------------------------------------
# Start Gateway Server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://0.0.0.0:{GATEWAY_PORT}")
    app.run(host="0.0.0.0", port=GATEWAY_PORT, debug=True)