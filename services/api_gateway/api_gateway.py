from flask import Flask, jsonify, request, redirect
import requests
from config import config
import os

app = Flask(__name__)

# Load variables from .env
GATEWAY_PORT = config.GATEWAY_PORT
SERVICES = config.SERVICES

# Debug to check if gateway is running
@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "Flask API Gateway is running"}, 200


@app.route("/health/ml-engine", methods=["GET"])
def check_ml_engine():
    """Checks communication between API Gateway and ML Engine."""
    target_url = f"{config.SERVICES["ML_ENGINE_URL"]}/health"
    
    try:
        # Send request with a strict timeout so the Gateway doesn't hang
        response = requests.get(target_url, timeout=3.0)
        
        if response.status_code == 200:
            return jsonify({
                "status": "healthy",
                "message": "Gateway can communicate with ML Engine",
                "ml_engine_response": response.json()
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "message": f"ML Engine responded with status code {response.status_code}"
            }), 502

    except requests.exceptions.ConnectionError:
        return jsonify({
            "status": "unreachable",
            "message": f"Could not connect to ML Engine at {config.SERVICES["ML_ENGINE_URL"]}. Check network/container status."
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "timeout",
            "message": f"Request to ML Engine at {config.SERVICES["ML_ENGINE_URL"]} timed out."
        }), 504

@app.route("/dashboard", methods=["GET"])
def redirect_to_dashboard():
    external_dashboard_url = config.EXTERNAL_URLS["DASHBOARD_URL"]
    return redirect(external_dashboard_url, code=302)

if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://localhost:{GATEWAY_PORT}")
    app.run(host="0.0.0.0", port=GATEWAY_PORT, debug=True)
