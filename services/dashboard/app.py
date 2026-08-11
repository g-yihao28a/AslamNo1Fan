import requests
import streamlit as st
import plotly.express as px

from config import config
from data_access import load_customer_data, load_inference_logs
from feature_options import FEATURE_OPTIONS

st.set_page_config(page_title="Telco Churn Dashboard", layout="wide")

st.title("📊 Telco Customer Churn Dashboard")

tab_overview, tab_predict, tab_logs = st.tabs(
    ["Overview", "Predict Churn", "Recent Predictions"]
)

# ---------------------------------------------------------------------------
# Overview tab: interactive filters + KPIs + charts, all backed by live DB data
# ---------------------------------------------------------------------------
with tab_overview:
    try:
        df = load_customer_data()
    except Exception as exc:
        st.error(
            "Could not load data from the database. Has it been seeded yet? "
            f"({exc})"
        )
        df = None

    if df is not None and not df.empty:
        st.sidebar.header("Filters")
        contract_filter = st.sidebar.multiselect(
            "Contract type",
            options=sorted(df["contract"].dropna().unique()),
            default=sorted(df["contract"].dropna().unique()),
        )
        internet_filter = st.sidebar.multiselect(
            "Internet service",
            options=sorted(df["internet_service"].dropna().unique()),
            default=sorted(df["internet_service"].dropna().unique()),
        )

        filtered = df[
            df["contract"].isin(contract_filter)
            & df["internet_service"].isin(internet_filter)
        ]

        col1, col2, col3, col4 = st.columns(4)
        total_customers = len(filtered)
        churn_rate = (
            filtered["churn_value"].mean() * 100 if total_customers else 0
        )
        avg_cltv = filtered["cltv"].mean() if total_customers else 0
        avg_tenure = filtered["tenure_in_months"].mean() if total_customers else 0

        col1.metric("Customers", f"{total_customers:,}")
        col2.metric("Churn rate", f"{churn_rate:.1f}%")
        col3.metric("Avg. CLTV", f"{avg_cltv:,.0f}")
        col4.metric("Avg. tenure (months)", f"{avg_tenure:.1f}")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            churn_by_contract = (
                filtered.groupby("contract")["churn_value"]
                .mean()
                .reset_index()
            )
            churn_by_contract["churn_value"] *= 100
            fig = px.bar(
                churn_by_contract,
                x="contract",
                y="churn_value",
                labels={"churn_value": "Churn rate (%)", "contract": "Contract"},
                title="Churn rate by contract type",
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig2 = px.histogram(
                filtered,
                x="tenure_in_months",
                color="churn_label",
                barmode="overlay",
                nbins=30,
                title="Tenure distribution by churn status",
                labels={"tenure_in_months": "Tenure (months)"},
            )
            st.plotly_chart(fig2, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            fig3 = px.box(
                filtered,
                x="churn_label",
                y="monthly_charge",
                title="Monthly charges by churn status",
                labels={"churn_label": "Churned", "monthly_charge": "Monthly charge"},
            )
            st.plotly_chart(fig3, use_container_width=True)

        with c4:
            churn_by_internet = (
                filtered.groupby("internet_service")["churn_value"]
                .mean()
                .reset_index()
            )
            churn_by_internet["churn_value"] *= 100
            fig4 = px.bar(
                churn_by_internet,
                x="internet_service",
                y="churn_value",
                labels={
                    "churn_value": "Churn rate (%)",
                    "internet_service": "Internet service",
                },
                title="Churn rate by internet service",
            )
            st.plotly_chart(fig4, use_container_width=True)
    elif df is not None:
        st.info(
            "The database is empty. Run the loader job to import the "
            "telco churn Excel data (see ReadMe.md)."
        )

# ---------------------------------------------------------------------------
# Predict tab: interactive form that calls the ML engine (through the gateway)
# ---------------------------------------------------------------------------
with tab_predict:
    st.subheader("Score a customer")
    st.caption("Sends the inputs to the ML engine's /predict endpoint live.")

    with st.form("predict_form"):
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
        try:
            resp = requests.post(
                f"{config.API_GATEWAY_URL}/api/ml/predict", json=payload, timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                prob = result["churn_probability"]
                st.metric("Churn probability", f"{prob * 100:.1f}%")
                if result["predicted_churn"]:
                    st.error("Prediction: likely to churn")
                else:
                    st.success("Prediction: likely to stay")
            else:
                st.warning(f"ML engine returned an error: {resp.json()}")
        except requests.RequestException as exc:
            st.error(f"Could not reach the ML engine via the API gateway: {exc}")

# ---------------------------------------------------------------------------
# Logs tab: recent predictions written to inference_logs by the ML engine
# ---------------------------------------------------------------------------
with tab_logs:
    st.subheader("Recent prediction history")
    logs = load_inference_logs()
    if logs.empty:
        st.info("No predictions logged yet. Try the Predict Churn tab.")
    else:
        st.dataframe(logs, use_container_width=True)
