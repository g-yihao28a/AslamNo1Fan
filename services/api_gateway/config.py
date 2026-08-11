import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Read values with fallbacks if not defined in .env
    GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8008))

    # Grouped namespaces for microservices
    SERVICES = {
        "ml_engine": os.getenv("ML_ENGINE_URL", "http://ml_engine:8010"),
        "dashboard": os.getenv("DASHBOARD_URL", "http://dashboard:8501"),
    }


config = Config()
