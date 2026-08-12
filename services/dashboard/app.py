import requests
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

from config import config as app_config
from data_access import load_customer_data, load_inference_logs, normalize_series
from feature_options import FEATURE_OPTIONS

from flask import Flask

app = Flask(__name__)

st.set_page_config(page_title="Telco Churn Dashboard", layout="wide")

st.title("📊 Telco Customer Churn Dashboard")

tab_overview, tab_predict, tab_logs, tab_custom1 = st.tabs(
    ["Overview", "Predict Churn", "Recent Predictions", "Custom Charts"]
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
        st.sidebar.header("Overview Filters")
        filter_columns = [ 'phone_service',
            'multiple_lines', 'internet_service', 'internet_type','online_security', 'online_backup', 
            'contract', 'paperless_billing', 'payment_method', 'gender','senior_citizen',    'dependents']
        for col in filter_columns:
            if col in df.columns:
                df[f"{col}_norm"] = normalize_series(df[col], missing_label="_missing_")

        # 2. Dictionary to hold user selections
        selected_filters = {}

        st.sidebar.caption("Use these filters to update the Overview KPIs and charts.")

        # 3. Loop: create a multiselect for each column
        for col in filter_columns:
            # Check if column exists to avoid errors
            if col in df.columns:
                options = sorted(df[col].dropna().unique())  # Get unique values, drop NaN
                default = options  # Default = select all (matches your original behavior)
                
                selected = st.sidebar.multiselect(
                    label=f"{col}",
                    options=options,
                    default=default
                )
                selected_filters[col] = selected
            else:
                st.sidebar.warning(f"Column '{col}' not found. Check spelling/case.")

        # 4. Apply ALL filters dynamically
        # Start with a mask that keeps every row
        mask = pd.Series(True, index=df.index)

        for col, selected_values in selected_filters.items():
            # Only apply the filter if the column exists and the user didn't deselect everything
            if col in df.columns and selected_values:
                mask &= df[col].isin(selected_values)

        # 5. Get your filtered DataFrame
        filtered = df[mask]

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
                f"{app_config.API_GATEWAY_URL}/api/ml/predict", json=payload, timeout=10
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

@app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "Dashboard is running"
    }, 200

# ---------------------------------------------------------------------------
# Custom Charts tab: user-defined Plotly dashboards
# ---------------------------------------------------------------------------
with tab_custom1:
    st.subheader("Custom Charts")
    st.caption(
        "Build your own charts from the customer dataset. "
        "Chart controls are kept inside this tab so they do not conflict "
        "with the Overview filters."
    )

    try:
        custom_df = load_customer_data()
    except Exception as exc:
        st.error(
            "Could not load data from the database. Has it been seeded yet? "
            f"({exc})"
        )
        custom_df = None

    if custom_df is not None and not custom_df.empty:
        if "charts" not in st.session_state:
            st.session_state.charts = []

        numeric_cols = custom_df.select_dtypes(include=np.number).columns.tolist()
        all_cols = custom_df.columns.tolist()

        if not numeric_cols:
            st.warning("No numeric columns are available for custom charts.")
        else:
            # Keep chart creation controls in the main content area.
            with st.expander("➕ Add a chart", expanded=not st.session_state.charts):
                chart_type = st.selectbox(
                    "Chart type",
                    ["Histogram", "Box Plot", "Scatter", "Heatmap", "Bar"],
                    key="custom_chart_type",
                )

                chart_config = {"type": chart_type}

                if chart_type == "Histogram":
                    c1, c2 = st.columns(2)
                    with c1:
                        chart_config["x"] = st.selectbox(
                            "Column", numeric_cols, key="custom_hist_x"
                        )
                    with c2:
                        chart_config["bins"] = st.slider(
                            "Bins", 5, 100, 30, key="custom_hist_bins"
                        )

                elif chart_type == "Box Plot":
                    c1, c2 = st.columns(2)
                    with c1:
                        chart_config["y"] = st.selectbox(
                            "Value column", numeric_cols, key="custom_box_y"
                        )
                    with c2:
                        chart_config["x"] = st.selectbox(
                            "Group by (optional)",
                            [None] + all_cols,
                            key="custom_box_x",
                        )

                elif chart_type == "Scatter":
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        chart_config["x"] = st.selectbox(
                            "X", numeric_cols, key="custom_scatter_x"
                        )
                    with c2:
                        chart_config["y"] = st.selectbox(
                            "Y", numeric_cols, key="custom_scatter_y"
                        )
                    with c3:
                        chart_config["color"] = st.selectbox(
                            "Color by (optional)",
                            [None] + all_cols,
                            key="custom_scatter_color",
                        )

                elif chart_type == "Heatmap":
                    chart_config["cols"] = st.multiselect(
                        "Columns for correlation",
                        numeric_cols,
                        default=numeric_cols,
                        key="custom_heatmap_cols",
                    )

                elif chart_type == "Bar":
                    c1, c2 = st.columns(2)
                    with c1:
                        chart_config["x"] = st.selectbox(
                            "Category", all_cols, key="custom_bar_x"
                        )
                    with c2:
                        chart_config["y"] = st.selectbox(
                            "Value", numeric_cols, key="custom_bar_y"
                        )

                if st.button("Add chart", type="primary", key="add_custom_chart"):
                    chart_config["id"] = (
                        max((c["id"] for c in st.session_state.charts), default=-1) + 1
                    )
                    st.session_state.charts.append(chart_config)
                    st.rerun()

        def render_chart(cfg):
            chart_type = cfg["type"]

            if chart_type == "Histogram":
                return px.histogram(
                    custom_df, x=cfg["x"], nbins=cfg["bins"],
                    title=f"{cfg['x']} distribution"
                )

            if chart_type == "Box Plot":
                return px.box(
                    custom_df, x=cfg["x"], y=cfg["y"],
                    title=f"{cfg['y']} by {cfg['x']}" if cfg["x"] else f"{cfg['y']} distribution"
                )

            if chart_type == "Scatter":
                return px.scatter(
                    custom_df, x=cfg["x"], y=cfg["y"], color=cfg["color"],
                    title=f"{cfg['y']} vs {cfg['x']}"
                )

            if chart_type == "Heatmap":
                if len(cfg["cols"]) < 2:
                    return None
                corr = custom_df[cfg["cols"]].corr()
                return px.imshow(
                    corr,
                    text_auto=True,
                    title="Correlation heatmap",
                    aspect="auto",
                )

            if chart_type == "Bar":
                return px.bar(
                    custom_df, x=cfg["x"], y=cfg["y"],
                    title=f"{cfg['y']} by {cfg['x']}"
                )

            return None

        st.divider()

        if not st.session_state.charts:
            st.info("No custom charts yet. Use “Add a chart” above to get started.")
        else:
            st.subheader(f"Your dashboard ({len(st.session_state.charts)} chart"
                         f"{'' if len(st.session_state.charts) == 1 else 's'})")

            # Two charts per row gives a balanced wide-screen dashboard.
            for i in range(0, len(st.session_state.charts), 2):
                row_charts = st.session_state.charts[i:i + 2]
                cols = st.columns(2)

                for col, chart_cfg in zip(cols, row_charts):
                    with col:
                        fig = render_chart(chart_cfg)

                        if fig is None:
                            st.warning(
                                "Select at least two numeric columns for the heatmap."
                            )
                        else:
                            st.plotly_chart(
                                fig,
                                use_container_width=True,
                                key=f"chart_{chart_cfg['id']}",
                            )

                        if st.button(
                            "🗑️ Remove",
                            key=f"remove_chart_{chart_cfg['id']}",
                        ):
                            st.session_state.charts = [
                                c for c in st.session_state.charts
                                if c["id"] != chart_cfg["id"]
                            ]
                            st.rerun()
    elif custom_df is not None:
        st.info(
            "The database is empty. Run the loader job to import the "
            "telco churn Excel data (see ReadMe.md)."
        )

