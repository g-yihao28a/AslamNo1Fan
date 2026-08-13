from flask import Flask, jsonify, request, redirect, render_template
import requests
import os
from config import config

app = Flask(__name__)

# Load variables from config or environment
GATEWAY_PORT = config.GATEWAY_PORT
SERVICES=config.SERVICES


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

if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://localhost:{GATEWAY_PORT}")
    app.run(host="0.0.0.0", port=GATEWAY_PORT, debug=True)
