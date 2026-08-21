from flask import Flask, jsonify, request, redirect, render_template
import requests
import pandas as pd
from config import config

app = Flask(__name__)

INTERNAL_DATABASE_URL = config.SERVICES["DATABASE_URL"].rstrip("/")
INTERNAL_ML_ENGINE_URL = config.SERVICES["ML_ENGINE_URL"].rstrip("/")
FEATURE_NAME_MAPPING = config.FEATURE_NAME_MAPPING

# Proxy requests to database
def _proxy_to_database(path, method):
    """
    Forward a request to the database microservice and relay its response.
    Args:
        path: HTML path to be sent to
        method: HTML method to be used
    Returns:
        JSON: The json response
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

# Readme page
@app.route('/readme')
def readme():
    return render_template('readme.html')

# Database page
@app.route('/database')
def database_gateway():
    return render_template('database_gateway.html')

# Get or post customers
@app.route("/database/customers", methods=["GET", "POST"])
def database_customers():
    return _proxy_to_database("customers", request.method)

# Get the full json list of customers
@app.route("/database/customers/full", methods=["GET"])
def database_customers_full():
    """
    Gets the full json list of customers
    Returns:
        JSON: Returns 2 key-value pairs, the total count and the actual values nested
    """
    return _proxy_to_database("customers/full", request.method)

# Get a specific customer from their ID
@app.route("/database/customers/full/<customer_id>", methods=["GET"])
def database_customer_full(customer_id):
    return _proxy_to_database(f"customers/full/{customer_id}", request.method)

# CSV upload
@app.route("/database/customers/upload", methods=["POST"])
def database_customers_upload():
    """Forward a CSV file upload to the database microservice's bulk-import
    route. Kept separate from _proxy_to_database because file uploads are
    multipart/form-data, not JSON."""

    # if empty
    if "file" not in request.files:
        return jsonify({"error": "No file provided (expected multipart field 'file')"}), 400

    upload = request.files["file"]
    try:
        response = requests.post(
            f"{INTERNAL_DATABASE_URL}/customers/upload",
            files={"file": (upload.filename, upload.stream, upload.mimetype)}, #filename: file name, stream: data, mimetype: data type
            timeout=30,
        )
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Database microservice unreachable",
            "details": str(e)
        }), 502

# Another way to get/put/delete customers
@app.route("/database/customers/<customer_id>", methods=["GET", "PUT", "DELETE"])
def database_customer(customer_id):
    return _proxy_to_database(f"customers/{customer_id}", request.method)

# Get/post inference logs
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
        return jsonify(metadata), 200
    else:
        return jsonify({
                        "error": "ML engine returned an error",
                        "details": response.text
                    }), response.status_code

# Get ml model info
@app.route('/ml/model/info')
def get_model_info():
    try:
        response = requests.get(f'{INTERNAL_ML_ENGINE_URL}/model/info', timeout=5)
        
        # If upstream service responded, pass back its JSON and exact status code
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "error": "ML engine returned an error",
                "details": response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        # Handles connection errors (e.g. downstream pod down or wrong DNS name)
        print(f"Failed to connect to ML Engine: {e}")
        return jsonify({
            "error": "Unable to connect to downstream ML service",
            "details": str(e)
        }), 503

# Reload ml model
@app.route('/ml/model/reload')
def reload_model():
    response = requests.post(f'{INTERNAL_ML_ENGINE_URL}/model/reload')
    if response.status_code == 200:
        print("Model reloaded successfully:")
        metadata = response.json()
        return jsonify(metadata), 200
    else:
        return jsonify({
                        "error": "ML engine returned an error",
                        "details": response.text
                    }), response.status_code

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
                # If not 200 status code
                else:
                    results.append({
                        "customer_id": record.get("customer_id", "N/A"),
                        "prediction": "Error",
                        "probability": None,
                        "error": pred_resp.text,
                    })
            # Request error
            except requests.RequestException as item_err:
                results.append({
                    "customer_id": record.get("customer_id", "N/A"),
                    "prediction": "Unreachable",
                    "probability": None,
                    "error": str(item_err),
                })

        return jsonify({"results": results}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}"}), 400


# Redirect to prediction service
@app.route("/ml_prediction", methods=["GET"])
def redirect_to_prediction():
    external_prediction_url = config.SERVICES["ML_PREDICTION_URL"]
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