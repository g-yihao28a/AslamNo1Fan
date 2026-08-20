"""
Loads the real Telco customer churn Excel files into the Postgres database,
merging all four source files into a single combined dataset (one row per
customer) that gets upserted into the `customers` table.

Run this once after the database container is up and the schema has been
created (01-schema.sql runs automatically on first container start).

Usage:
    python load_data.py

Reads connection settings from environment variables (see .env.example):
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
"""
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_DATA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "telco_data"
)
# In Docker, ./data is mounted read-only at /data (see compose.yaml)
DATA_DIR = os.getenv("DATA_DIR", DEFAULT_DATA_DIR)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "telco_churn_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgrespassword")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def load_excel(filename):
    path = os.path.join(DATA_DIR, filename)
    return pd.read_excel(path)


def _read_location():
    df = load_excel("Telco_customer_churn_location.xlsx")
    df = df.rename(
        columns={
            "Customer ID": "customer_id",
            "Country": "country",
            "State": "state",
            "City": "city",
            "Zip Code": "zip_code",
            "Lat Long": "lat_long",
            "Latitude": "latitude",
            "Longitude": "longitude",
        }
    )[
        [
            "customer_id",
            "country",
            "state",
            "city",
            "zip_code",
            "lat_long",
            "latitude",
            "longitude",
        ]
    ]
    df["zip_code"] = df["zip_code"].astype(str)
    return df


def _read_demographics():
    df = load_excel("Telco_customer_churn_demographics.xlsx")
    return df.rename(
        columns={
            "Customer ID": "customer_id",
            "Gender": "gender",
            "Age": "age",
            "Under 30": "under_18",
            "Senior Citizen": "senior_citizen",
            "Married": "partner",
            "Dependents": "dependents",
            "Number of Dependents": "number_of_dependents",
        }
    )[
        [
            "customer_id",
            "gender",
            "age",
            "under_18",
            "senior_citizen",
            "partner",
            "dependents",
            "number_of_dependents",
        ]
    ]


def _read_services():
    df = load_excel("Telco_customer_churn_services.xlsx")
    df = df.rename(
        columns={
            "Customer ID": "customer_id",
            "Tenure in Months": "tenure_in_months",
            "Phone Service": "phone_service",
            "Multiple Lines": "multiple_lines",
            "Internet Service": "internet_service",
            "Internet Type": "internet_type",
            "Online Security": "online_security",
            "Online Backup": "online_backup",
            "Device Protection Plan": "device_protection",
            "Premium Tech Support": "tech_support",
            "Streaming TV": "streaming_tv",
            "Streaming Movies": "streaming_movies",
            "Contract": "contract",
            "Paperless Billing": "paperless_billing",
            "Payment Method": "payment_method",
            "Monthly Charge": "monthly_charge",
            "Total Charges": "total_charges",
        }
    )[
        [
            "customer_id",
            "tenure_in_months",
            "phone_service",
            "multiple_lines",
            "internet_service",
            "internet_type",
            "online_security",
            "online_backup",
            "device_protection",
            "tech_support",
            "streaming_tv",
            "streaming_movies",
            "contract",
            "paperless_billing",
            "payment_method",
            "monthly_charge",
            "total_charges",
        ]
    ]
    # dedupe: services file has one row per customer per quarter in some exports
    return df.drop_duplicates(subset="customer_id", keep="last")


def _read_status():
    df = load_excel("Telco_customer_churn_status.xlsx")
    df = df.rename(
        columns={
            "Customer ID": "customer_id",
            "Satisfaction Score": "satisfaction_score",
            "Customer Status": "customer_status",
            "Churn Label": "churn_label",
            "Churn Value": "churn_value",
            "Churn Score": "churn_score",
            "CLTV": "cltv",
            "Churn Category": "churn_category",
            "Churn Reason": "churn_reason",
        }
    )[
        [
            "customer_id",
            "satisfaction_score",
            "customer_status",
            "churn_label",
            "churn_value",
            "churn_score",
            "cltv",
            "churn_category",
            "churn_reason",
        ]
    ]
    return df.drop_duplicates(subset="customer_id", keep="last")


def build_combined_dataset():
    """Merges all four source files into one row per customer_id.

    Uses outer joins so a customer present in only some of the files still
    ends up in the combined dataset (with NULLs for the fields it's missing
    from), rather than being silently dropped.
    """
    df = _read_location()
    for other in (_read_demographics(), _read_services(), _read_status()):
        df = df.merge(other, on="customer_id", how="outer")
    return df


def _upsert(engine, df, table, pk_col):
    """Load into a staging table then upsert, so re-running is safe."""
    staging = f"_staging_{table}"
    df.to_sql(staging, engine, if_exists="replace", index=False)
    cols = list(df.columns)
    non_pk = [c for c in cols if c != pk_col]
    set_clause = ", ".join(f'{c} = EXCLUDED.{c}' for c in non_pk)
    col_list = ", ".join(cols)
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT INTO {table} ({col_list})
                SELECT {col_list} FROM {staging}
                ON CONFLICT ({pk_col}) DO UPDATE SET {set_clause}
                """
            )
        )
        conn.execute(text(f"DROP TABLE {staging}"))


def main():
    print(f"Connecting to {DB_HOST}:{DB_PORT}/{DB_NAME} ...")
    engine = create_engine(DB_URL)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        print(f"Could not connect to the database: {exc}")
        sys.exit(1)

    print("Reading and merging all four source files into one dataset...")
    combined = build_combined_dataset()
    print(f"Combined dataset: {len(combined)} customers, {len(combined.columns)} columns")

    _upsert(engine, combined, "customers", "customer_id")
    print(f"customers: {len(combined)} rows")

    print("Done.")


if __name__ == "__main__":
    main()
