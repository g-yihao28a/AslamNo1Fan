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
    DATABASE_NAME = os.getenv("DATABASE_NAME", "database_service")
    ML_PREDICTION_NAME = os.getenv("ML_PREDICTION_NAME","ml_prediction")

    # ---- Ports ----
    GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8008))
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5000))
    ML_ENGINE_PORT = int(os.getenv("ML_ENGINE_PORT", 8010))
    ML_PREDICTION_PORT = int(os.getenv("ML_PREDICTION_PORT", 8011))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))
    

    SERVICES = {
        "ML_ENGINE_URL":f"http://{ML_ENGINE_NAME}:{ML_ENGINE_PORT}",
        "ML_PREDICTION_URL":f"http://{ML_PREDICTION_NAME}:{ML_PREDICTION_PORT}",
        "API_GATEWAY_URL": f"http://{GATEWAY_NAME}:{GATEWAY_PORT}",
        "DASHBOARD_URL": f"http://{DASHBOARD_NAME}:{DASHBOARD_PORT}",
        "DATABASE_URL": f"http://{DATABASE_NAME}:{DATABASE_PORT}",
    }

    # ---- External URLs (Host Machine / Browser Access) ----
    # EXTERNAL_URLS = {
    #     "API_GATEWAY_URL": f"http://localhost:{GATEWAY_PORT}",
    #     "ML_ENGINE_URL": f"http://localhost:{ML_ENGINE_PORT}",
    #     "ML_PREDICTION_URL": f"http://localhost:{ML_PREDICTION_PORT}",
    #     "DASHBOARD_URL": f"http://localhost:{DASHBOARD_PORT}",
    #     "DATABASE_URL": f"http://localhost:{DATABASE_PORT}",
    # }

    EXTERNAL_URLS = {
    "API_GATEWAY_URL": f"http://telco-churn.local:{GATEWAY_PORT}",
    "ML_ENGINE_URL": f"http://telco-churn.local:{ML_ENGINE_PORT}",
    "ML_PREDICTION_URL": f"http://telco-churn.local:{ML_PREDICTION_PORT}",
    "DASHBOARD_URL": f"http://telco-churn.local:{DASHBOARD_PORT}",
    "DATABASE_URL": f"http://telco-churn.local:{DATABASE_PORT}",
}

    FEATURE_NAME_MAPPING = {
    "tenure_in_months": "Tenure Months",
    "tenure_months": "Tenure Months",
    "monthly_charge": "Monthly Charges",
    "monthly_charges": "Monthly Charges",
    "total_charges": "Total Charges",
    "gender": "Gender",
    "senior_citizen": "Senior Citizen",
    "partner": "Partner",
    "dependents": "Dependents",
    "phone_service": "Phone Service",
    "multiple_lines": "Multiple Lines",
    "internet_service": "Internet Service",
    "online_security": "Online Security",
    "online_backup": "Online Backup",
    "device_protection": "Device Protection",
    "tech_support": "Tech Support",
    "streaming_tv": "Streaming TV",
    "streaming_movies": "Streaming Movies",
    "contract": "Contract",
    "paperless_billing": "Paperless Billing",
    "payment_method": "Payment Method",
}
config = Config()
