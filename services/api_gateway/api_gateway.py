from flask import Flask, jsonify, request
import requests
from config import config

app = Flask(__name__)

# Load variables from .env
gateway_port = config.GATEWAY_PORT
SERVICES = config.SERVICES


# Debug to check if gateway is running
@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "Flask API Gateway is running"}, 200


HEALTH_PATHS = {
    "ml_engine": "/health",
    # Streamlit doesn't expose a Flask-style /health route
    "dashboard": "/_stcore/health",
}


@app.route("/health/all", methods=["GET"])
def health_check_all():
    """Aggregates health checks across every downstream microservice."""
    results = {"api_gateway": {"status": "ok"}}
    for name, base_url in SERVICES.items():
        path = HEALTH_PATHS.get(name, "/health")
        try:
            resp = requests.get(f"{base_url}{path}", timeout=3)
            detail = resp.json() if "application/json" in resp.headers.get("Content-Type", "") else resp.text
            results[name] = {"status": "ok" if resp.ok else "error", "detail": detail}
        except requests.RequestException as exc:
            results[name] = {"status": "unreachable", "detail": str(exc)}
    return jsonify(results), 200


# ---- ML engine routes ----

@app.route("/api/ml/predict", methods=["POST"])
def ml_predict():
    try:
        resp = requests.post(
            f"{SERVICES['ml_engine']}/predict", json=request.get_json(silent=True), timeout=10
        )
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as exc:
        return {"error": f"ml_engine unreachable: {exc}"}, 502


@app.route("/api/ml/train", methods=["POST"])
def ml_train():
    try:
        resp = requests.post(f"{SERVICES['ml_engine']}/train", timeout=120)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as exc:
        return {"error": f"ml_engine unreachable: {exc}"}, 502


@app.route("/api/ml/model/info", methods=["GET"])
def ml_model_info():
    try:
        resp = requests.get(f"{SERVICES['ml_engine']}/model/info", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as exc:
        return {"error": f"ml_engine unreachable: {exc}"}, 502


if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://localhost:{gateway_port}")
    app.run(host="0.0.0.0", port=gateway_port, debug=True)
