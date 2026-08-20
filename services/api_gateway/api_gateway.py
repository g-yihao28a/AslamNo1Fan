from flask import Flask, jsonify, request, redirect, render_template
import requests
import os
from config import config

app = Flask(__name__)

DATABASE_URL = config.SERVICES["DATABASE_URL"].rstrip("/")


def _proxy_to_database(path, method):
    """Forward a request to the database microservice and relay its response.

    This is what lets the dashboard and ml model microservices reach the
    database through the gateway instead of calling it directly: they hit
    `/database/...` on the gateway, and the gateway relays the request/
    response to and from the database microservice.
    """
    try:
        response = requests.request(
            method,
            f"{DATABASE_URL}/{path}",
            params=request.args,
            json=request.get_json(silent=True),
            timeout=5,
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Database microservice unreachable",
            "details": str(e)
        }), 502

### Routing
# Display html page when users visit base address
@app.route('/')
def home():
    return render_template('index.html')

# Display html page when users visit base address
@app.route('/database')
def database_gateway():
    return render_template('database_gateway.html')

# ---------------------------------------------------------------------------
# Proxy routes: forward customer / inference-log requests from the dashboard
# and ml model microservices through to the database microservice.
# ---------------------------------------------------------------------------
@app.route("/database/customers", methods=["GET", "POST"])
def database_customers():
    return _proxy_to_database("customers", request.method)

@app.route("/database/customers/full", methods=["GET"])
def database_customers_full():
    """Merged view: all four customer tables joined into one flat record
    per customer, in a single request - this is what the ML model
    microservice should call to pull the whole dataset at once."""
    return _proxy_to_database("customers/full", request.method)

@app.route("/database/customers/full/<customer_id>", methods=["GET"])
def database_customer_full(customer_id):
    return _proxy_to_database(f"customers/full/{customer_id}", request.method)

@app.route("/database/customers/upload", methods=["POST"])
def database_customers_upload():
    """Forward a CSV file upload to the database microservice's bulk-import
    route. Kept separate from _proxy_to_database because file uploads are
    multipart/form-data, not JSON."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided (expected multipart field 'file')"}), 400

    upload = request.files["file"]
    try:
        response = requests.post(
            f"{DATABASE_URL}/customers/upload",
            files={"file": (upload.filename, upload.stream, upload.mimetype)},
            timeout=30,
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Database microservice unreachable",
            "details": str(e)
        }), 502

@app.route("/database/customers/<customer_id>", methods=["GET", "PUT", "DELETE"])
def database_customer(customer_id):
    return _proxy_to_database(f"customers/{customer_id}", request.method)

@app.route("/database/logs", methods=["GET", "POST"])
def database_logs():
    return _proxy_to_database("logs", request.method)

# Display html page when users visit base address
@app.route('/ml')
def ml_gateway():
    return render_template('ml_gateway.html')

# Train ml model
@app.route('/ml_train')
def train_model():
    response = requests.post(f'{config.SERVICES["ML_ENGINE_URL"].rstrip("/")}/train')
    if response.status_code == 200:
        print("Model retrained successfully:")
        metadata = response.json()
        return metadata
    else:
        print(f"Error ({response.status_code}):", response.json())
        return None

# Redirect to prediction service
@app.route("/ml_prediction", methods=["GET"])
def redirect_to_prediction():
    external_prediction_url = config.EXTERNAL_URLS["ML_PREDICTION_URL"]
    return redirect(external_prediction_url, code=302)

# Redirect to dashboard service
@app.route("/dashboard", methods=["GET"])
def redirect_to_dashboard():
    external_dashboard_url = config.EXTERNAL_URLS["DASHBOARD_URL"]
    return redirect(external_dashboard_url, code=302)

# Debug to check communication between services
@app.route("/health", methods=["GET"])
def health_check():
    service_statuses = {}
    all_healthy = True

    for name, base_url in config.SERVICES.items():
        # Prevent self-calls if a gateway URL accidentally gets added to SERVICES
        if base_url.rstrip("/").startswith(config.SERVICES["API_GATEWAY_URL"].rstrip("/")):
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

if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://0.0.0.0:{config.GATEWAY_PORT}")
    app.run(host="0.0.0.0", port=config.GATEWAY_PORT, debug=True)