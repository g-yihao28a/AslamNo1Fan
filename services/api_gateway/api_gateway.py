from flask import Flask, request, Response
import requests
from config import config

app = Flask(__name__)

# Load variables from .env
gateway_port = config.GATEWAY_PORT

# Define backend microservice addresses
# SERVICES = {
# }

# Debug to check if gateway is running
@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "Flask API Gateway is running"}, 200

# Put routing below

if __name__ == "__main__":
    print(f"Flask API Gateway starting on http://localhost:{gateway_port}")
    app.run(host="0.0.0.0",port=gateway_port, debug=True)