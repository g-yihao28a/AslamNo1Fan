import requests
import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

from data_access import load_customer_data

from flask import Flask

app = Flask(__name__)

st.set_page_config(page_title="Telco Churn Dashboard", layout="wide")

st.title("📊 Telco Customer Churn Dashboard")

tab_overview,  tab_custom = st.tabs(
    ["Overview",  "Custom Charts"]
)
# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def has_cols(df, cols):
    """True if every column in `cols` exists in `df`."""
    return all(c in df.columns for c in cols)


def churn_rate_by(df, group_col):
    """Return a 2-col dataframe: group_col, churn_rate (%)."""
    out = df.groupby(group_col)["churn_value"].mean().reset_index()
    out["churn_value"] = out["churn_value"] * 100
    return out.rename(columns={"churn_value": "Churn rate (%)"})


def stacked_100_by(df, group_col, label_col="churn_label"):
    """Return counts of churned/retained per group_col, normalized to 100%."""
    counts = df.groupby([group_col, label_col]).size().reset_index(name="count")
    totals = counts.groupby(group_col)["count"].transform("sum")
    counts["pct"] = counts["count"] / totals * 100
    return counts


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
        # Keep an unfiltered live snapshot for the Custom Charts version selector.
        df_now = df.copy()

        st.sidebar.header("Filters")
        filter_columns = [ 'phone_service',
            'multiple_lines', 'internet_service', 'internet_type','online_security', 'online_backup', 
            'contract', 'paperless_billing', 'payment_method', 'gender','senior_citizen',    'dependents']


        # 2. Dictionary to hold user selections
        selected_filters = {}

        st.sidebar.header("Filter Data")

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

        # -------------------------------------------------------------
        # 1. Health & Trend Overview — KPI cards
        # -------------------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)
        total_customers = len(filtered)
        churn_rate = filtered["churn_value"].mean() * 100 if total_customers else 0

        col1.metric("Customers", f"{total_customers:,}")
        col2.metric("Churn rate", f"{churn_rate:.1f}%")

        if "cltv" in filtered.columns:
            avg_cltv = filtered["cltv"].mean() if total_customers else 0
            col3.metric("Avg. CLTV", f"{avg_cltv:,.0f}")
        else:
            col3.metric("Avg. CLTV", "n/a")

        if "tenure_in_months" in filtered.columns:
            avg_tenure = filtered["tenure_in_months"].mean() if total_customers else 0
            col4.metric("Avg. tenure (months)", f"{avg_tenure:.1f}")
        else:
            col4.metric("Avg. tenure (months)", "n/a")

        st.divider()

        # -------------------------------------------------------------
        # 2. Feature importance — loaded from a precomputed CSV if present
        #    (e.g. output of a feature_importance_results.csv run offline)
        # -------------------------------------------------------------
        try:
            fi = pd.read_csv("feature_importance_results.csv", index_col=0)
            if "Permutation" in fi.columns:
                top_fi = fi["Permutation"].sort_values(ascending=True).tail(10)
                fig_fi = px.bar(
                    top_fi,
                    x=top_fi.values,
                    y=top_fi.index,
                    orientation="h",
                    labels={"x": "Permutation importance", "y": "Feature"},
                    title="Top 10 features driving churn (permutation importance)",
                )
                st.plotly_chart(fig_fi, width='stretch')
                st.divider()
        except FileNotFoundError:
            pass  # feature importance file not generated yet — skip silently

        # -------------------------------------------------------------
        # 3. The "Commitment" story — Contract & Tenure
        # -------------------------------------------------------------
        st.subheader("📄 Commitment: Contract & Tenure")
        c1, c2 = st.columns(2)

        with c1:
            if has_cols(filtered, ["contract", "churn_label"]):
                stacked = stacked_100_by(filtered, "contract")
                fig = px.bar(
                    stacked,
                    x="contract",
                    y="pct",
                    color="churn_label",
                    barmode="stack",
                    labels={"pct": "Share (%)", "contract": "Contract", "churn_label": "Churned"},
                    title="Churn rate by contract type (100% stacked)",
                )
                st.plotly_chart(fig, width='stretch')
            else:
                st.caption("Contract data not available.")

        with c2:
            if has_cols(filtered, ["tenure_in_months", "churn_label"]):
                fig2 = px.histogram(
                    filtered,
                    x="tenure_in_months",
                    color="churn_label",
                    barmode="overlay",
                    nbins=30,
                    title="Tenure distribution by churn status",
                    labels={"tenure_in_months": "Tenure (months)"},
                )
                st.plotly_chart(fig2, width='stretch')
            else:
                st.caption("Tenure data not available.")

        st.divider()

        # -------------------------------------------------------------
        # 4. The "Financial Pressure" story — Monthly/Total Charges
        # -------------------------------------------------------------
        st.subheader("💰 Financial pressure: Charges")
        c3, c4 = st.columns(2)

        with c3:
            if has_cols(filtered, ["churn_label", "monthly_charge"]):
                fig3 = px.box(
                    filtered,
                    x="churn_label",
                    y="monthly_charge",
                    title="Monthly charges by churn status",
                    labels={"churn_label": "Churned", "monthly_charge": "Monthly charge"},
                )
                st.plotly_chart(fig3, width='stretch')
            else:
                st.caption("Monthly charge data not available.")

        with c4:
            if has_cols(filtered, ["tenure_in_months", "total_charges", "churn_label"]):
                fig3b = px.scatter(
                    filtered,
                    x="tenure_in_months",
                    y="total_charges",
                    color="churn_label",
                    opacity=0.6,
                    title="Tenure vs. total charges",
                    labels={
                        "tenure_in_months": "Tenure (months)",
                        "total_charges": "Total charges",
                        "churn_label": "Churned",
                    },
                )
                st.plotly_chart(fig3b, width='stretch')
            else:
                st.caption("Total charges data not available.")

        st.divider()

        # -------------------------------------------------------------
        # 5. The "Loyalty Catalyst" story — Referrals, Age
        # -------------------------------------------------------------
        st.subheader("🤝 Loyalty catalysts: Referrals & Age")
        c6, c5 = st.columns(2)


        with c6:
            if "age" in filtered.columns:
                bucketed = filtered.copy()
                bucketed["age_bracket"] = pd.cut(
                    bucketed["age"],
                    bins=[0, 30, 50, 120],
                    labels=["18-30", "31-50", "50+"],
                )
                fig6 = px.bar(
                    churn_rate_by(bucketed, "age_bracket"),
                    x="age_bracket",
                    y="Churn rate (%)",
                    title="Churn rate by age bracket",
                    labels={"age_bracket": "Age"},
                )
                st.plotly_chart(fig6, width='stretch')
            else:
                st.caption("Age data not available.")

        st.divider()

        # -------------------------------------------------------------
        # 6. The "Service & Billing Friction" story
        # -------------------------------------------------------------
        st.subheader("🧾 Service & billing friction")
        c7, c8 = st.columns(2)

        with c7:
            if has_cols(filtered, ["payment_method", "churn_label"]):
                stacked_pm = stacked_100_by(filtered, "payment_method")
                fig7 = px.bar(
                    stacked_pm,
                    x="payment_method",
                    y="pct",
                    color="churn_label",
                    barmode="stack",
                    labels={"pct": "Share (%)", "payment_method": "Payment method", "churn_label": "Churned"},
                    title="Churn rate by payment method (100% stacked)",
                )
                st.plotly_chart(fig7, width='stretch')
            else:
                st.caption("Payment method data not available.")

        with c8:
            if "internet_type" in filtered.columns:
                fig8 = px.bar(
                    churn_rate_by(filtered, "internet_type"),
                    x="internet_type",
                    y="Churn rate (%)",
                    title="Churn rate by internet type",
                    labels={"internet_type": "Internet type"},
                )
                st.plotly_chart(fig8, width='stretch')
            else:
                st.caption("Internet type data not available.")

        if "paperless_billing" in filtered.columns:
            pb = churn_rate_by(filtered, "paperless_billing")
            cols = st.columns(len(pb)) if len(pb) else []
            for col, (_, row) in zip(cols, pb.iterrows()):
                col.metric(f"Paperless billing = {row['paperless_billing']}", f"{row['Churn rate (%)']:.1f}%")

        st.divider()

        # -------------------------------------------------------------
        # 7. High-risk archetype — Contract x Referrals heatmap
        # -------------------------------------------------------------
        st.subheader("🔥 High-risk archetype")
        if has_cols(filtered, ["contract", "number_of_referrals"]):
            heat_df = filtered.copy()
            heat_df["referral_bucket"] = pd.cut(
                heat_df["number_of_referrals"],
                bins=[-1, 0, 2, float("inf")],
                labels=["0", "1-2", "3+"],
            )
            pivot = (
                heat_df.pivot_table(
                    index="contract",
                    columns="referral_bucket",
                    values="churn_value",
                    aggfunc="mean",
                    observed=True,
                )
                * 100
            )
            fig9 = px.imshow(
                pivot,
                text_auto=".1f",
                color_continuous_scale="Reds",
                labels=dict(x="Referrals", y="Contract", color="Churn rate (%)"),
                title="Churn rate (%): Contract type × Number of referrals",
            )
            st.plotly_chart(fig9, width='stretch')
            st.caption(
                "The hottest cell is your call list: e.g. month-to-month "
                "customers with zero referrals are typically the highest-risk segment."
            )
        else:
            st.caption("Contract and/or referral data not available for the heatmap.")

# ---------------------------------------------------------------------------
# Data Versioning — snapshots are created only when the live dataframe changes.
# This is independent from the Overview filters/charts.
# ---------------------------------------------------------------------------
# 1. State Initialization
if "df_versions" not in st.session_state:
    st.session_state.df_versions = []
if "df_version_times" not in st.session_state:
    st.session_state.df_version_times = []

# 2. Deduplicated Snapshot Append
if "df_now" in locals() and df_now is not None and not df_now.empty:
    add_version = (
        not st.session_state.df_versions
        or not df_now.equals(st.session_state.df_versions[-1])
    )
    if add_version:
        st.session_state.df_versions.append(df_now.copy())
        st.session_state.df_version_times.append(
            pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        )

# 3. Version History UI
with st.expander("🕓 Data version history", expanded=False):
    num_versions = len(st.session_state.df_versions)
    if num_versions >= 2:
        df_prev = st.session_state.df_versions[-2]
        df_curr = st.session_state.df_versions[-1]

        # Identify newly added rows
        df_added = df_curr.merge(df_prev, how="outer", indicator=True)
        df_added = df_added[df_added["_merge"] == "left_only"].drop(columns=["_merge"])

        st.caption(f"Showing comparison between latest 2 of {num_versions} captured versions.")
        st.write("Previous snapshot", df_prev)
        st.write("Current snapshot", df_curr)
        st.write("Newly added rows", df_added)
    else:
        st.write("Only one unique snapshot recorded so far.")


# ---------------------------------------------------------------------------
# Custom Charts tab: version-aware self-service charts.
# The controls live inside this tab so they do not conflict with the Overview
# sidebar filters. Overview visuals above remain unchanged.
# ---------------------------------------------------------------------------
with tab_custom:
    st.subheader("📈 Custom Charts")
    st.caption(
        "Choose a saved data version, chart type, columns, and aggregation "
        "method. Saved charts continue to use the version they were created from."
    )

    if not st.session_state.df_versions:
        st.info("No data versions are available yet.")
    else:
        # -------------------------------------------------------------------
        # Data version selector
        # -------------------------------------------------------------------
        version_labels = []
        for i, timestamp in enumerate(st.session_state.df_version_times):
            if i == len(st.session_state.df_versions) - 1:
                version_labels.append(f"Current data — {timestamp}")
            else:
                version_labels.append(f"Version {i + 1} — {timestamp}")

        selected_version = st.selectbox(
            "Data version",
            range(len(st.session_state.df_versions)),
            format_func=lambda i: version_labels[i],
            key="custom_data_version",
        )

        selected_df = st.session_state.df_versions[selected_version].copy()

        st.caption(
            f"Selected version: {len(selected_df):,} rows × "
            f"{len(selected_df.columns):,} columns"
        )

        with st.expander("View selected data", expanded=False):
            st.dataframe(selected_df, use_container_width=True)

        # -------------------------------------------------------------------
        # Chart state
        # -------------------------------------------------------------------
        if "custom_charts" not in st.session_state:
            st.session_state.custom_charts = []

        numeric_cols = selected_df.select_dtypes(include=np.number).columns.tolist()
        all_cols = selected_df.columns.tolist()

        if not numeric_cols:
            st.warning("No numeric columns are available for custom charts.")
        else:
            st.divider()
            st.subheader("➕ Create a chart")

            chart_type = st.selectbox(
                "Chart type",
                [
                    "Bar Chart",
                    "Line Chart",
                    "Histogram",
                    "Box Plot",
                    "Scatter Plot",
                    "Pie Chart",
                    "Heatmap",
                ],
                key="custom_chart_type",
            )

            # ---------------------------------------------------------------
            # Bar / Line / Pie: these support aggregation.
            # ---------------------------------------------------------------
            if chart_type in {"Bar Chart", "Line Chart", "Pie Chart"}:
                c1, c2 = st.columns(2)

                with c1:
                    x_col = st.selectbox(
                        "Category / X-axis",
                        all_cols,
                        key="custom_x_col",
                    )

                with c2:
                    y_col = st.selectbox(
                        "Value column",
                        numeric_cols,
                        key="custom_y_col",
                    )

                aggregation = st.selectbox(
                    "How should values be handled?",
                    ["Mean", "Total (Sum)", "Count", "Minimum", "Maximum"],
                    key="custom_aggregation",
                )

                aggregation_map = {
                    "Mean": "mean",
                    "Total (Sum)": "sum",
                    "Count": "count",
                    "Minimum": "min",
                    "Maximum": "max",
                }

                agg_function = aggregation_map[aggregation]

                if agg_function == "count":
                    chart_df = (
                        selected_df.groupby(x_col, dropna=False)[y_col]
                        .count()
                        .reset_index(name="value")
                    )
                else:
                    chart_df = (
                        selected_df.groupby(x_col, dropna=False)[y_col]
                        .agg(agg_function)
                        .reset_index(name="value")
                    )

                if chart_type == "Bar Chart":
                    fig = px.bar(
                        chart_df,
                        x=x_col,
                        y="value",
                        title=f"{aggregation} of {y_col} by {x_col}",
                        labels={"value": aggregation, x_col: x_col},
                    )
                elif chart_type == "Line Chart":
                    fig = px.line(
                        chart_df,
                        x=x_col,
                        y="value",
                        markers=True,
                        title=f"{aggregation} of {y_col} by {x_col}",
                        labels={"value": aggregation, x_col: x_col},
                    )
                else:
                    fig = px.pie(
                        chart_df,
                        names=x_col,
                        values="value",
                        title=f"{aggregation} of {y_col} by {x_col}",
                    )

                chart_config = {
                    "type": chart_type,
                    "version": selected_version,
                    "version_label": version_labels[selected_version],
                    "x": x_col,
                    "y": y_col,
                    "aggregation": aggregation,
                }

            # ---------------------------------------------------------------
            # Histogram: distribution, so no Mean/Sum selector is needed.
            # ---------------------------------------------------------------
            elif chart_type == "Histogram":
                value_col = st.selectbox(
                    "Value column",
                    numeric_cols,
                    key="custom_hist_value",
                )
                bins = st.slider(
                    "Number of bins",
                    5,
                    100,
                    30,
                    key="custom_hist_bins",
                )

                fig = px.histogram(
                    selected_df,
                    x=value_col,
                    nbins=bins,
                    title=f"Distribution of {value_col}",
                )

                chart_config = {
                    "type": chart_type,
                    "version": selected_version,
                    "version_label": version_labels[selected_version],
                    "value": value_col,
                    "bins": bins,
                }

            # ---------------------------------------------------------------
            # Box plot: preserves the full distribution.
            # ---------------------------------------------------------------
            elif chart_type == "Box Plot":
                c1, c2 = st.columns(2)
                with c1:
                    value_col = st.selectbox(
                        "Value column",
                        numeric_cols,
                        key="custom_box_value",
                    )
                with c2:
                    group_col = st.selectbox(
                        "Group by (optional)",
                        [None] + all_cols,
                        key="custom_box_group",
                    )

                fig = px.box(
                    selected_df,
                    x=group_col,
                    y=value_col,
                    title=(
                        f"{value_col} by {group_col}"
                        if group_col
                        else f"Distribution of {value_col}"
                    ),
                )

                chart_config = {
                    "type": chart_type,
                    "version": selected_version,
                    "version_label": version_labels[selected_version],
                    "value": value_col,
                    "group": group_col,
                }

            # ---------------------------------------------------------------
            # Scatter: each row is an observation, so no aggregation.
            # ---------------------------------------------------------------
            elif chart_type == "Scatter Plot":
                c1, c2 = st.columns(2)
                with c1:
                    scatter_x = st.selectbox(
                        "X-axis",
                        numeric_cols,
                        key="custom_scatter_x",
                    )
                with c2:
                    scatter_y = st.selectbox(
                        "Y-axis",
                        numeric_cols,
                        key="custom_scatter_y",
                    )

                scatter_color = st.selectbox(
                    "Color by (optional)",
                    [None] + all_cols,
                    key="custom_scatter_color",
                )

                fig = px.scatter(
                    selected_df,
                    x=scatter_x,
                    y=scatter_y,
                    color=scatter_color,
                    title=f"{scatter_y} vs {scatter_x}",
                )

                chart_config = {
                    "type": chart_type,
                    "version": selected_version,
                    "version_label": version_labels[selected_version],
                    "x": scatter_x,
                    "y": scatter_y,
                    "color": scatter_color,
                }

            # ---------------------------------------------------------------
            # Heatmap: correlation matrix, no aggregation selector.
            # ---------------------------------------------------------------
            else:  # Heatmap
                heat_cols = st.multiselect(
                    "Numeric columns for correlation",
                    numeric_cols,
                    default=numeric_cols,
                    key="custom_heat_cols",
                )

                if len(heat_cols) < 2:
                    st.warning("Select at least two numeric columns for a heatmap.")
                    fig = None
                else:
                    corr = selected_df[heat_cols].corr()
                    fig = px.imshow(
                        corr,
                        text_auto=".2f",
                        color_continuous_scale="RdBu_r",
                        zmin=-1,
                        zmax=1,
                        title="Correlation heatmap",
                    )

                chart_config = {
                    "type": chart_type,
                    "version": selected_version,
                    "version_label": version_labels[selected_version],
                    "cols": heat_cols,
                }

            # ---------------------------------------------------------------
            # Preview + save
            # ---------------------------------------------------------------
            st.divider()
            st.subheader("Chart Preview")

            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

                if st.button(
                    "➕ Add this chart to dashboard",
                    type="primary",
                    key="add_custom_chart",
                ):
                    existing_ids = [
                        c.get("id", 0)
                        for c in st.session_state.custom_charts
                    ]
                    chart_config["id"] = max(existing_ids, default=-1) + 1
                    st.session_state.custom_charts.append(chart_config)
                    st.success("Chart added to your dashboard.")
            else:
                st.info("Create a valid chart configuration to see the preview.")

        # ===================================================================
        # SAVED DASHBOARD
        # ===================================================================
        st.divider()
        st.subheader(
            f"📊 My Dashboard ({len(st.session_state.custom_charts)} charts)"
        )

        if not st.session_state.custom_charts:
            st.info("No custom charts added yet.")
        else:
            for i in range(0, len(st.session_state.custom_charts), 2):
                row_charts = st.session_state.custom_charts[i:i + 2]
                cols = st.columns(len(row_charts))

                for col, cfg in zip(cols, row_charts):
                    with col:
                        # A saved chart points to its original snapshot.
                        version_index = cfg.get("version", 0)
                        if version_index >= len(st.session_state.df_versions):
                            st.warning("The data version for this chart is unavailable.")
                            continue

                        chart_df = st.session_state.df_versions[version_index].copy()
                        t = cfg["type"]

                        if t in {"Bar Chart", "Line Chart", "Pie Chart"}:
                            aggregation_map = {
                                "Mean": "mean",
                                "Total (Sum)": "sum",
                                "Count": "count",
                                "Minimum": "min",
                                "Maximum": "max",
                            }
                            agg = aggregation_map[cfg["aggregation"]]

                            if agg == "count":
                                plot_df = (
                                    chart_df.groupby(cfg["x"], dropna=False)[cfg["y"]]
                                    .count()
                                    .reset_index(name="value")
                                )
                            else:
                                plot_df = (
                                    chart_df.groupby(cfg["x"], dropna=False)[cfg["y"]]
                                    .agg(agg)
                                    .reset_index(name="value")
                                )

                            title = (
                                f"{cfg['aggregation']} of {cfg['y']} by {cfg['x']}"
                            )

                            if t == "Bar Chart":
                                fig = px.bar(plot_df, x=cfg["x"], y="value", title=title)
                            elif t == "Line Chart":
                                fig = px.line(
                                    plot_df,
                                    x=cfg["x"],
                                    y="value",
                                    markers=True,
                                    title=title,
                                )
                            else:
                                fig = px.pie(
                                    plot_df,
                                    names=cfg["x"],
                                    values="value",
                                    title=title,
                                )

                        elif t == "Histogram":
                            fig = px.histogram(
                                chart_df,
                                x=cfg["value"],
                                nbins=cfg["bins"],
                                title=f"Distribution of {cfg['value']}",
                            )

                        elif t == "Box Plot":
                            fig = px.box(
                                chart_df,
                                x=cfg.get("group"),
                                y=cfg["value"],
                                title=(
                                    f"{cfg['value']} by {cfg['group']}"
                                    if cfg.get("group")
                                    else f"Distribution of {cfg['value']}"
                                ),
                            )

                        elif t == "Scatter Plot":
                            fig = px.scatter(
                                chart_df,
                                x=cfg["x"],
                                y=cfg["y"],
                                color=cfg.get("color"),
                                title=f"{cfg['y']} vs {cfg['x']}",
                            )

                        else:  # Heatmap
                            heat_cols = cfg.get("cols", [])
                            if len(heat_cols) < 2:
                                st.warning("Not enough columns for this heatmap.")
                                continue
                            fig = px.imshow(
                                chart_df[heat_cols].corr(),
                                text_auto=".2f",
                                color_continuous_scale="RdBu_r",
                                zmin=-1,
                                zmax=1,
                                title="Correlation heatmap",
                            )

                        st.plotly_chart(fig, use_container_width=True)
                        st.caption(f"Data source: {cfg.get('version_label', 'Saved version')}")

                        if st.button(
                            "🗑️ Remove",
                            key=f"remove_custom_chart_{cfg['id']}",
                        ):
                            st.session_state.custom_charts = [
                                c
                                for c in st.session_state.custom_charts
                                if c.get("id") != cfg["id"]
                            ]
                            st.rerun()

