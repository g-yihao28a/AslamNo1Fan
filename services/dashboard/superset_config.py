import os

# --- Core Superset settings, pulled from environment (see .env.example) ---
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "change-this-in-your-.env-file")

# Superset's own metadata database (dashboards, users, charts...) — kept as
# the default SQLite unless you want to point it at Postgres too.
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_METADATA_DB_URI", "sqlite:////app/superset_home/superset.db"
)

# --- Connection info for the telco churn database ---
# Not wired in automatically (Superset stores DB connections in its own
# metadata DB, added via the UI or `superset set-database-uri`), but exposed
# here so setup scripts / docs can reference a single source of truth.
TELCO_DB_URI = os.getenv(
    "TELCO_DB_URI",
    "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}".format(
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgrespassword"),
        host=os.getenv("DB_HOST", "database"),
        port=os.getenv("DB_PORT", "5432"),
        db=os.getenv("DB_NAME", "telco_churn_db"),
    ),
)

FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}
