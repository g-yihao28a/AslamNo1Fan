from flask import Flask, jsonify, request, redirect, render_template
import requests
import pandas as pd
import io
import os
from config import config

app = Flask(__name__)

INTERNAL_DATABASE_URL = config.SERVICES["DATABASE_URL"].rstrip("/")
INTERNAL_ML_ENGINE_URL = config.SERVICES["ML_ENGINE_URL"].rstrip("/")
FEATURE_NAME_MAPPING = config.FEATURE_NAME_MAPPING


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
            f"{INTERNAL_DATABASE_URL}/{path}",
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
# Home page
@app.route('/')
def home():
    return render_template('index.html')


# Database page
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
            f"{INTERNAL_DATABASE_URL}/customers/upload",
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


# ML Gateway
@app.route('/ml')
def ml_gateway():
    return render_template('ml_gateway.html')


# Train ml model
@app.route('/ml/train')
def train_model():
    response = requests.post(f'{INTERNAL_ML_ENGINE_URL}/train')
    if response.status_code == 200:
        print("Model retrained successfully:")
        metadata = response.json()
        return metadata
    else:
        print(f"Error ({response.status_code}):", response.json())
        return None


# Iterate through CSV rows and send single prediction calls
@app.route("/ml/predict_csv_single", methods=["POST"])
def predict_csv_single():
    # Check there is a file
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    upload = request.files["file"]

    # Check is csv file
    if not upload.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported for single prediction iteration"}), 400

    try:
        df = pd.read_csv(upload.stream)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        df = df.where(pd.notnull(df), None)
        records = df.to_dict(orient="records")

        results = []
        for record in records:
            # Build payload mapped with Title Case features required by ml_engine/predict
            model_payload = {}
            for k, v in record.items():
                if k in FEATURE_NAME_MAPPING:
                    model_payload[FEATURE_NAME_MAPPING[k]] = v
                else:
                    model_payload[k] = v

            try:
                # Issue individual single prediction request
                pred_resp = requests.post(f"{INTERNAL_ML_ENGINE_URL}/predict", json=model_payload, timeout=10,)
                if pred_resp.status_code == 200:
                    pred_data = pred_resp.json()
                    item_result = {
                        "customer_id": record.get("customer_id", "N/A"),
                        "prediction": pred_data.get("predicted_churn", pred_data.get("prediction", "No")),
                        "probability": pred_data.get("churn_probability", pred_data.get("probability", None)),
                        "raw_response": pred_data,
                    }
                    results.append(item_result)
                else:
                    results.append({
                        "customer_id": record.get("customer_id", "N/A"),
                        "prediction": "Error",
                        "probability": None,
                        "error": pred_resp.text,
                    })
            except requests.RequestException as item_err:
                results.append({
                    "customer_id": record.get("customer_id", "N/A"),
                    "prediction": "Unreachable",
                    "probability": None,
                    "error": str(item_err),
                })

        # Save inference run to database microservice logs
        try:
            requests.post(
                f"{INTERNAL_DATABASE_URL}/logs",
                json={"type": "csv_single_prediction_batch", "results": results},
                timeout=10,
            )
        except requests.RequestException:
            pass

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400


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
        "services": service_statuses,
    }, status_code


if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://0.0.0.0:{config.GATEWAY_PORT}")
    app.run(host="0.0.0.0", port=config.GATEWAY_PORT, debug=True)