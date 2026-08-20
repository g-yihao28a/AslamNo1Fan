import os


class Config:
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))

    # Where to reach the other services from inside the dashboard container.
    # The dashboard no longer talks to Postgres directly - all customer and
    # inference-log data comes through the API gateway.
    API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api_gateway:8008")
    ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://ml_engine:8010")


config = Config()
