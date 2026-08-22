import os


class Config:
    ML_ENGINE_PORT = int(os.getenv("ML_ENGINE_PORT", 8010))

    # Where the trained model artifacts live
    MODEL_DIR = os.getenv("MODEL_DIR", "model")
    MODEL_PATH = os.path.join(MODEL_DIR, "churn_model.joblib")
    METADATA_PATH = os.path.join(MODEL_DIR, "metadata.json")

    # Training data source. In Docker this is mounted read-only at /data.
    TRAINING_DATA_PATH = os.getenv(
        "TRAINING_DATA_PATH",
        os.path.join("data", "telco_data", "Telco_customer_churn.xlsx"),
    )

    # Where to reach the API gateway from inside the ml_engine container.
    # Predictions are logged to inference_logs through the gateway's
    # /database/logs route instead of connecting to Postgres directly.
    GATEWAY_NAME = os.getenv("GATEWAY_NAME", "api-gateway-service")
    GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8008))
    API_GATEWAY_URL = f"http://{GATEWAY_NAME}:{GATEWAY_PORT}"

config = Config()
