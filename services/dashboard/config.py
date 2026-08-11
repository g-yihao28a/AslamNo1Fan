import os


class Config:
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8501))

    # Database connection
    DB_HOST = os.getenv("DB_HOST", "database")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "telco_churn_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgrespassword")

    @property
    def DB_URL(self):
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Where to reach the other services from inside the dashboard container
    API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://api_gateway:8008")
    ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://ml_engine:8010")


config = Config()
