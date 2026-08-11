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

    # Database connection, used only to log predictions to inference_logs
    DB_HOST = os.getenv("DB_HOST", "database")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "telco_churn_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgrespassword")


config = Config()
