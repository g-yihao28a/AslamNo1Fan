import pandas as pd
import requests
import streamlit as st

from config import config

GATEWAY_URL = config.SERVICES["API_GATEWAY_URL"].rstrip("/")


@st.cache_data(ttl=60)
def load_customer_data():
    """Pulls the whole combined customer dataset through the API gateway
    (gateway -> database microservice -> Postgres), instead of connecting
    to Postgres directly."""
    response = requests.get(f"{GATEWAY_URL}/database/customers/full", timeout=30)
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload.get("customers", []))


@st.cache_data(ttl=30)
def load_inference_logs(limit=200):
    try:
        response = requests.get(
            f"{GATEWAY_URL}/database/logs",
            params={"limit": limit},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return pd.DataFrame(payload.get("logs", []))
    except requests.RequestException:
        return pd.DataFrame()
