import os

from dotenv import load_dotenv
from pathlib import Path

# Get the directory of the current Python file
BASE_DIR = Path(__file__).resolve().parent

# Locate the .env file 2 levels up
ENV_PATH = BASE_DIR.parent.parent / ".env"

load_dotenv()


class Config:
# ---- Service Names ----
    GATEWAY_NAME = os.getenv("GATEWAY_NAME", "api_gateway")
    ML_ENGINE_NAME = os.getenv("ML_ENGINE_NAME", "ml_engine")
    DASHBOARD_NAME = os.getenv("DASHBOARD_NAME", "dashboard")

    # ---- Ports ----
    GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8008))
    ML_ENGINE_PORT = int(os.getenv("ML_ENGINE_PORT", 8010))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))

    SERVICES = {
        "ML_ENGINE_URL":f"http://{ML_ENGINE_NAME}:{ML_ENGINE_PORT}",
        "API_GATEWAY_URL": f"http://{GATEWAY_NAME}:{GATEWAY_PORT}",
        "DASHBOARD_URL": f"http://{DASHBOARD_NAME}:{DASHBOARD_PORT}",
    }

    # ---- External URLs (Host Machine / Browser Access) ----
    EXTERNAL_URLS = {
        "API_GATEWAY_URL": f"http://localhost:{GATEWAY_PORT}",
        "ML_ENGINE_URL": f"http://localhost:{ML_ENGINE_PORT}",
        "DASHBOARD_URL": f"http://localhost:{DASHBOARD_PORT}",
    }


config = Config()
