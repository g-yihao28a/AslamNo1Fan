import uuid

import requests
import streamlit as st
from config import config
import data_access


st.set_page_config(page_title="Telco Churn Prediction", layout="wide")

st.title("Telco Customer Churn Prediction")

tab_predict, tab_logs = st.tabs(
    ["Predict Churn", "Recent Predictions"]
)

FEATURE_OPTIONS = config.FEATURE_OPTIONS

# Predict tab: interactive form that calls the ML engine
with tab_predict:
    st.subheader("Score a customer")
    st.caption("Sends the inputs to the ML engine's /predict endpoint live.")

    with st.form("predict_form"):
        customer_id = st.text_input(
            "Customer ID",
            value=f"MANUAL-{uuid.uuid4().hex[:8].upper()}",
            help="Used to save this prediction to Recent Predictions. "
                 "Leave the auto-generated value, or enter a real customer ID.",
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            tenure = st.slider("Tenure (months)", 0, 72, 12)
            monthly_charges = st.slider("Monthly charges", 0.0, 150.0, 65.0)
            total_charges = st.number_input("Total charges", 0.0, 10000.0, 780.0)
            gender = st.selectbox("Gender", FEATURE_OPTIONS["Gender"])
        with col2:
            senior = st.selectbox("Senior citizen", FEATURE_OPTIONS["Senior Citizen"])
            partner = st.selectbox("Partner", FEATURE_OPTIONS["Partner"])
            dependents = st.selectbox("Dependents", FEATURE_OPTIONS["Dependents"])
            contract = st.selectbox("Contract", FEATURE_OPTIONS["Contract"])
        with col3:
            internet = st.selectbox(
                "Internet service", FEATURE_OPTIONS["Internet Service"]
            )
            payment = st.selectbox(
                "Payment method", FEATURE_OPTIONS["Payment Method"]
            )
            paperless = st.selectbox(
                "Paperless billing", FEATURE_OPTIONS["Paperless Billing"]
            )
            phone = st.selectbox("Phone service", FEATURE_OPTIONS["Phone Service"])

        submitted = st.form_submit_button("Predict churn risk")

    if submitted:
        payload = {
            "customer_id": customer_id,
            "Tenure Months": tenure,
            "Monthly Charges": monthly_charges,
            "Total Charges": total_charges,
            "Gender": gender,
            "Senior Citizen": senior,
            "Partner": partner,
            "Dependents": dependents,
            "Phone Service": phone,
            "Multiple Lines": "No",
            "Internet Service": internet,
            "Online Security": "No",
            "Online Backup": "No",
            "Device Protection": "No",
            "Tech Support": "No",
            "Streaming TV": "No",
            "Streaming Movies": "No",
            "Contract": contract,
            "Paperless Billing": paperless,
            "Payment Method": payment,
        }

        # API Request to ML service to do prediction
        try:
            resp = requests.post(
                f"{config.SERVICES['ML_ENGINE_URL']}/predict", json=payload, timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                prob = result["churn_probability"]
                st.metric("Churn probability", f"{prob * 100:.1f}%")
                if result["predicted_churn"]:
                    st.error("Prediction: likely to churn")
                else:
                    st.success("Prediction: likely to stay")
                # Invalidate the cached logs so "Recent Predictions" shows
                # this prediction immediately instead of waiting out the
                # 30s cache TTL.
                data_access.load_inference_logs.clear()
            else:
                st.warning(f"ML engine returned an error: {resp.json()}")
        except requests.RequestException as exc:
            st.error(f"Could not reach the ML engine via the API gateway: {exc}")

# Logs tab: recent predictions written to inference_logs by the ML engine
with tab_logs:
    st.subheader("Recent prediction history")
    logs = data_access.load_inference_logs()
    if logs.empty:
        st.info("No predictions logged yet. Try the Predict Churn tab.")
    else:
        st.dataframe(logs, use_container_width=True)



