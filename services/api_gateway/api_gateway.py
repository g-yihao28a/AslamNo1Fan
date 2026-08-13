from flask import Flask, jsonify, request, redirect, render_template
import requests
import os
from config import config

app = Flask(__name__)

# Load variables from config or environment
GATEWAY_PORT = getattr(config, "GATEWAY_PORT", 8008)
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", getattr(config, "ML_ENGINE_URL", "http://ml_engine:8010"))


# Display html  page when users visit base address
@app.route('/')
def home():
    return render_template('index.html')

# Debug to check communication between services
@app.route("/health", methods=["GET"])
def health_check():
    service_statuses = {}
    all_healthy = True

    for name, base_url in SERVICES.items():
        # Prevent self-calls if a gateway URL accidentally gets added to SERVICES
        if base_url.rstrip("/").startswith(SERVICES["API_GATEWAY_URL"].rstrip("/")):
            service_statuses[name] = "UP"
            continue

        # Cleanly construct target health URL: http://service:port/health
        health_endpoint = f"{base_url.rstrip('/')}/health"

        try:
            response = requests.get(health_endpoint, timeout=2.0)
            
            if response.status_code == 200:
                service_statuses[name] = "UP"
            else:
                service_statuses[name] = f"DOWN (HTTP {response.status_code})"
                all_healthy = False

        except requests.exceptions.RequestException:
            service_statuses[name] = "DOWN (UNREACHABLE)"
            all_healthy = False

    status_code = 200 if all_healthy else 503
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": service_statuses
    }, status_code

    return {
        "gateway_status": "Flask API Gateway is running",
        "overall_status": overall_status,
        "services": service_statuses
    }, status_code

@app.route("/dashboard", methods=["GET"])
def redirect_to_dashboard():
    external_dashboard_url = config.EXTERNAL_URLS["DASHBOARD_URL"]
    return redirect(external_dashboard_url, code=302)

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