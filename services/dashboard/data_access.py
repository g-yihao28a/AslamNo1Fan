import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
import os

# Get the directory of the current Python file
BASE_DIR = Path(__file__).resolve().parent

# Locate the .env file 2 levels up
ENV_PATH = BASE_DIR.parent.parent / ".env"

load_dotenv()

GATEWAY_NAME = os.getenv("GATEWAY_NAME", "api-gateway-service")
GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 8008))
GATEWAY_URL = f"http://{GATEWAY_NAME}:{GATEWAY_PORT}"


@st.cache_data(ttl=60)
def load_customer_data():
    """Pulls the whole combined customer dataset through the API gateway
    (gateway -> database microservice -> Postgres), instead of connecting
    to Postgres directly."""
    try:
        response = requests.get(f"{GATEWAY_URL}/database/customers/full", timeout=30)
        # Raises an HTTPError if status code is 4xx or 5xx
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {response.status_code}: {response.text}")
        raise e
    except requests.exceptions.RequestException as e:
        print(f"Connection Error: {e}")
        raise e
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
