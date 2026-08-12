import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

from config import config


@st.cache_resource
def get_engine():
    return create_engine(config.DB_URL)
def normalize_series(s: pd.Series, missing_label="_") -> pd.Series:
    # convert to string, strip, replace blanks with missing_label, lowercase, replace spaces with underscores
    s_norm = s.fillna("").astype(str).str.strip()
    s_norm = s_norm.replace("", missing_label)
    s_norm = s_norm.str.lower().str.replace(" ", "_", regex=False)
    return s_norm

@st.cache_data(ttl=60)
def load_customer_data():
    """Joins all four customer tables into one flat frame for the dashboard."""
    query = """
        SELECT
            loc.customer_id,
            loc.country, loc.state, loc.city, loc.latitude, loc.longitude,
            demo.gender, demo.age, demo.senior_citizen, demo.partner,
            demo.dependents, demo.number_of_dependents,
            svc.tenure_in_months, svc.phone_service, svc.multiple_lines,
            svc.internet_service, svc.internet_type, svc.online_security,
            svc.online_backup, svc.device_protection, svc.tech_support,
            svc.streaming_tv, svc.streaming_movies, svc.contract,
            svc.paperless_billing, svc.payment_method, svc.monthly_charge,
            svc.total_charges,
            st.satisfaction_score, st.customer_status, st.churn_label,
            st.churn_value, st.churn_score, st.cltv, st.churn_category,
            st.churn_reason
        FROM customer_location loc
        LEFT JOIN customer_demographics demo ON loc.customer_id = demo.customer_id
        LEFT JOIN customer_services svc ON loc.customer_id = svc.customer_id
        LEFT JOIN customer_status st ON loc.customer_id = st.customer_id
    """
    engine = get_engine()
    return pd.read_sql(query, engine)



@st.cache_data(ttl=30)
def load_inference_logs(limit=200):
    query = f"""
        SELECT inference_id, customer_id, churn_probability,
               predicted_churn, model_version, created_at
        FROM inference_logs
        ORDER BY created_at DESC
        LIMIT {limit}
    """
    engine = get_engine()
    try:
        return pd.read_sql(query, engine)
    except Exception:
        return pd.DataFrame()


# inside your tab_overview block, after df is loaded:

