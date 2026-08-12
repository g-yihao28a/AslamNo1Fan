import os

from dotenv import load_dotenv

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
        "ml_engine": os.getenv(
            "ML_ENGINE_URL", f"http://{ML_ENGINE_NAME}:{ML_ENGINE_PORT}"
        ),
        "api_gateway": os.getenv(
            "GATEWAY_URL", f"http://{GATEWAY_NAME}:{GATEWAY_PORT}"
        ),
        "dashboard": os.getenv(
            "DASHBOARD_URL", f"http://{DASHBOARD_NAME}:{DASHBOARD_PORT}"
        ),
    }

    # ---- External URLs (Host Machine / Browser Access) ----
    EXTERNAL_URLS = {
        "gateway": f"http://localhost:{GATEWAY_PORT}",
        "ml_engine": f"http://localhost:{ML_ENGINE_PORT}",
        "dashboard": f"http://localhost:{DASHBOARD_PORT}",
    }


config = Config()
