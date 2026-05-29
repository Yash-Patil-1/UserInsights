#!/usr/bin/env python3
"""Streamlit dashboard for UserInsights — Web Analytics & User Behavior Analysis.

Run: streamlit run dashboard.py
"""

from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

# ── Page Config ──────────────────────────────────────────────────

st.set_page_config(
    page_title="UserInsights Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data Loading ─────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent / "data"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"


@st.cache_data
def load_data():
    path = DATA_DIR / "ecommerce_events.csv"
    if not path.exists():
        st.error("Data file not found. Run `python src/data_generator.py` first.")
        st.stop()
    df = pd.read_csv(path, parse_dates=["timestamp", "signup_date"])
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    df["date"] = df["timestamp"].dt.date
    return df


@st.cache_data
def load_rfm():
    path = DATA_DIR / "rfm_segments.csv"
    if path.exists():
        return pd.read_csv(path)
    return None


@st.cache_data
def compute_cohort_data(df):
    """Compute monthly retention cohorts for display."""
    first_sessions = (
        df.groupby("user_id")["timestamp"]
        .min()
        .reset_index()
        .rename(columns={"timestamp": "first_session"})
    )
    first_sessions["cohort_month"] = first_sessions["first_session"].dt.to_period("M").astype(str)
    df = df.merge(first_sessions[["user_id", "cohort_month"]], on="user_id")
    df["activity_month"] = df["timestamp"].dt.to_period("M").astype(str)

    # Convert string periods back for computation
    cohort_data = []
    for cohort in sorted(df["cohort_month"].unique()):
        cohort_users = df[df["cohort_month"] == cohort]["user_id"].unique()
        cohort_size = len(cohort_users)
        for month in sorted(df[df["user_id"].isin(cohort_users)]["activity_month"].unique()):
            c = pd.Period(cohort, freq="M")
            m = pd.Period(month, freq="M")
            period = (m - c).n  # extract integer from MonthEnd offset
            active = df[(df["cohort_month"] == cohort) & (df["activity_month"] == month)]["user_id"].nunique()
            retention = round(active / cohort_size * 100, 1) if cohort_size > 0 else 0
            cohort_data.append({
                "cohort": cohort, "period": int(period),
                "active": active, "total": cohort_size, "retention": retention,
            })

    return pd.DataFrame(cohort_data)


# ── Color Scheme ─────────────────────────────────────────────────

COLORS = {
    "primary": "#2E86AB",
    "secondary": "#A23B72",
    "accent": "#F18F01",
    "success": "#3BB273",
    "danger": "#E85D75",
    "gray": "#95A5A6",
}


# ── Dashboard ────────────────────────────────────────────────────

def main():
    df = load_data()
    rfm = load_rfm()

    # ── Sidebar Filters ──
    st.sidebar.markdown(
        "<h1 style='font-size: 1.5rem; margin-bottom: 0.2rem;'>📊 UserInsights</h1>"
        "<p style='font-size: 0.8rem; color: #95A5A6;'>Web Analytics Dashboard</p>",
        unsafe_allow_html=True,
    )
    st.sidebar.divider()

    # Date range filter
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    # Channel filter
    channels = ["All"] + sorted(df["channel"].unique().tolist())
    selected_channel = st.sidebar.selectbox("Channel", channels)

    # Device filter
    devices = ["All"] + sorted(df["device"].unique().tolist())
    selected_device = st.sidebar.selectbox("Device", devices)

    # Segment filter (if RFM available)
    segment_options = ["All"]
    if rfm is not None:
        segment_options += sorted(rfm["Segment"].unique().tolist())
    selected_segment = st.sidebar.selectbox("Customer Segment", segment_options)

    # Apply filters
    mask = (df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)
    if selected_channel != "All":
        mask &= df["channel"] == selected_channel
    if selected_device != "All":
        mask &= df["device"] == selected_device
    if selected_segment != "All" and rfm is not None:
        seg_users = rfm[rfm["Segment"] == selected_segment]["user_id"].unique()
        mask &= df["user_id"].isin(seg_users)

    filtered = df[mask].copy()

    if len(filtered) == 0:
        st.warning("No data matches the selected filters. Try a broader selection.")
        return

    # ── Top KPI Cards ──
    total_users = filtered["user_id"].nunique()
    total_sessions = filtered["session_id"].nunique()
    total_purchases = (filtered["event_type"] == "purchase").sum()
    total_revenue = filtered[filtered["event_type"] == "purchase"]["revenue"].sum()
    purchase_rate = total_purchases / total_sessions * 100 if total_sessions > 0 else 0

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Active Users", f"{total_users:,}")
    with kpi2:
        st.metric("Sessions", f"{total_sessions:,}")
    with kpi3:
        st.metric("Purchases", f"{total_purchases:,}")
    with kpi4:
        st.metric("Revenue", f"Rs.{total_revenue:,.0f}")
    with kpi5:
        st.metric("Purchase Rate", f"{purchase_rate:.1f}%")

    st.divider()

    # ── Row 1: Funnel + Daily Trends ──
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.subheader("Conversion Funnel")
        funnel_steps = ["visit", "view_product", "add_to_cart", "checkout", "purchase"]
        funnel_vals = []
        for step in funnel_steps:
            funnel_vals.append(int(filtered[filtered["event_type"] == step]["session_id"].nunique()))

        fig_funnel = go.Figure()
        fig_funnel.add_trace(
            go.Funnel(
                y=funnel_steps,
                x=funnel_vals,
                textinfo="value+percent initial",
                marker=dict(
                    color=["#2E86AB", "#A23B72", "#F18F01", "#E85D75", "#3BB273"],
                    line=dict(width=1, color="white"),
                ),
            )
        )
        fig_funnel.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20),
                                 showlegend=False, hovermode="y")
        st.plotly_chart(fig_funnel, use_container_width=True)

    with col2:
        st.subheader("Daily Event Trends")
        daily = (
            filtered.groupby(filtered["timestamp"].dt.date)
            .agg(events=("event_type", "count"),
                 revenue=("revenue", "sum"))
            .reset_index()
        )
        daily.columns = ["date", "events", "revenue"]

        fig_daily = make_subplots(specs=[[{"secondary_y": True}]])
        fig_daily.add_trace(
            go.Bar(x=daily["date"], y=daily["events"],
                   name="Events", marker=dict(color=COLORS["primary"], opacity=0.6)),
            secondary_y=False,
        )
        fig_daily.add_trace(
            go.Scatter(x=daily["date"], y=daily["revenue"],
                       name="Revenue", mode="lines+markers",
                       line=dict(color=COLORS["accent"], width=3),
                       marker=dict(size=6)),
            secondary_y=True,
        )
        fig_daily.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20),
                                hovermode="x unified", showlegend=True,
                                legend=dict(orientation="h", y=1.1))
        fig_daily.update_yaxes(title_text="Events", secondary_y=False)
        fig_daily.update_yaxes(title_text="Revenue (Rs.)", secondary_y=True)
        st.plotly_chart(fig_daily, use_container_width=True)

    # ── Row 2: Cohort + Channel ──
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Monthly Retention Cohorts")
        cohort_df = compute_cohort_data(filtered)
        if len(cohort_df) > 0:
            pivot = cohort_df.pivot_table(
                index="cohort", columns="period", values="retention", aggfunc="first"
            )
            pivot = pivot.fillna(0)
            pivot.columns = [f"M{c}" for c in pivot.columns]

            fig_cohort = go.Figure(
                go.Heatmap(
                    z=pivot.values,
                    x=pivot.columns,
                    y=pivot.index,
                    colorscale="YlOrRd",
                    text=pivot.values.round(1).astype(str) + "%",
                    texttemplate="%{text}",
                    textfont={"size": 9},
                    hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
                    zmin=0, zmax=100,
                )
            )
            fig_cohort.update_layout(
                height=350, margin=dict(l=20, r=20, t=20, b=20),
                xaxis={"title": "Period"}, yaxis={"title": "Cohort", "autorange": "reversed"},
            )
            st.plotly_chart(fig_cohort, use_container_width=True)
        else:
            st.info("Not enough data for cohort analysis with current filters.")

    with col2:
        st.subheader("Channel Performance")
        ch = (
            filtered[filtered["event_type"].isin(["visit", "purchase"])]
            .groupby(["channel", "event_type"])["session_id"]
            .nunique()
            .reset_index()
        )
        ch_pivot = ch.pivot_table(index="channel", columns="event_type",
                                  values="session_id", aggfunc="first").fillna(0)
        if "visit" in ch_pivot and "purchase" in ch_pivot:
            ch_pivot["conversion"] = (ch_pivot["purchase"] / ch_pivot["visit"] * 100).round(1)
            ch_pivot = ch_pivot.sort_values("visit", ascending=True)

            fig_ch = go.Figure()
            fig_ch.add_trace(go.Bar(
                y=ch_pivot.index, x=ch_pivot["visit"],
                orientation="h", name="Visits",
                marker=dict(color=COLORS["primary"], opacity=0.6),
            ))
            fig_ch.add_trace(go.Bar(
                y=ch_pivot.index, x=ch_pivot["purchase"],
                orientation="h", name="Purchases",
                marker=dict(color=COLORS["success"]),
            ))
            fig_ch.update_layout(
                barmode="group", height=350, margin=dict(l=20, r=20, t=20, b=20),
                hovermode="y", legend=dict(orientation="h", y=1.1),
                xaxis={"title": "Sessions"}, yaxis={"title": None},
            )
            st.plotly_chart(fig_ch, use_container_width=True)

            # Show conversion rates as small text
            conv_text = " | ".join(
                f"<b>{ch}</b>: {row['conversion']:.1f}%"
                for ch, row in ch_pivot.iterrows()
            )
            st.markdown(f"<p style='font-size:0.8rem; color:#95A5A6; text-align:center;'>{conv_text}</p>",
                        unsafe_allow_html=True)
        else:
            st.info("Not enough channel data with current filters.")

    # ── Row 3: Hourly Heatmap + Device/Category ──
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("Hourly Activity Pattern")
        filtered["day_name"] = pd.Categorical(
            filtered["weekday"],
            categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            ordered=True,
        )
        hourly = filtered.groupby(["day_name", "hour"], observed=True).size().unstack(fill_value=0)

        fig_hourly = go.Figure(
            go.Heatmap(
                z=hourly.values,
                x=hourly.columns,
                y=hourly.index,
                colorscale="YlOrRd",
                hovertemplate="Day: %{y}<br>Hour: %{x}<br>Events: %{z}<extra></extra>",
            )
        )
        fig_hourly.update_layout(
            height=300, margin=dict(l=20, r=20, t=20, b=20),
            xaxis={"title": "Hour of Day", "dtick": 2},
            yaxis={"title": None},
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

    with col2:
        st.subheader("Device & Category Breakdown")
        # Device breakdown
        device_counts = (
            filtered[filtered["event_type"] == "purchase"]
            .groupby("device")["revenue"]
            .sum()
            .reset_index()
        )
        if len(device_counts) > 0:
            fig_dev = px.pie(
                device_counts, names="device", values="revenue",
                color_discrete_sequence=["#2E86AB", "#A23B72", "#F18F01"],
                hole=0.4,
            )
            fig_dev.update_layout(
                height=180, margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True, legend=dict(orientation="h", y=-0.2),
            )
            fig_dev.update_traces(textinfo="label+percent")
            st.plotly_chart(fig_dev, use_container_width=True)
        else:
            st.info("No purchase data for device breakdown.")

        # Top categories
        cat_rev = (
            filtered[filtered["event_type"] == "purchase"]
            .groupby("category")["revenue"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )
        if len(cat_rev) > 0:
            fig_cat = go.Figure(
                go.Bar(
                    y=cat_rev.index[::-1],
                    x=cat_rev.values[::-1],
                    orientation="h",
                    marker=dict(color=px.colors.sequential.Viridis_r[::2][:5]),
                )
            )
            fig_cat.update_layout(
                height=200, margin=dict(l=20, r=20, t=10, b=20),
                xaxis={"title": "Revenue (Rs.)"}, yaxis={"title": None},
            )
            st.plotly_chart(fig_cat, use_container_width=True)

    # ── Row 4: RFM Segmentation (if available) ──
    if rfm is not None:
        st.divider()
        st.subheader("RFM Customer Segments")

        # Filter RFM by dashboard filters
        filtered_users = filtered["user_id"].unique()
        rfm_filtered = rfm[rfm["user_id"].isin(filtered_users)].copy()

        if len(rfm_filtered) > 0:
            col1, col2 = st.columns([1, 1.5])

            with col1:
                seg_counts = rfm_filtered["Segment"].value_counts()
                segment_order = [
                    "Champions", "Loyal Customers", "Potential Loyalists",
                    "Recent Buyers", "Promising", "Needs Attention",
                    "At Risk", "Can't Lose Them", "Hibernating",
                    "Browsing Only", "Other",
                ]
                seg_counts = seg_counts.reindex([s for s in segment_order if s in seg_counts])

                seg_colors = {
                    "Champions": "#2ECC71", "Loyal Customers": "#27AE60",
                    "Potential Loyalists": "#3498DB", "Recent Buyers": "#85C1E9",
                    "Promising": "#F39C12", "Needs Attention": "#E67E22",
                    "At Risk": "#E74C3C", "Can't Lose Them": "#C0392B",
                    "Hibernating": "#95A5A6", "Browsing Only": "#BDC3C7",
                    "Other": "#7F8C8D",
                }

                fig_seg = go.Figure(
                    go.Bar(
                        x=seg_counts.index,
                        y=seg_counts.values,
                        marker=dict(color=[seg_colors.get(s, "#BDC3C7") for s in seg_counts.index]),
                        text=seg_counts.values,
                        textposition="outside",
                    )
                )
                fig_seg.update_layout(
                    height=350, margin=dict(l=20, r=20, t=20, b=60),
                    xaxis={"tickangle": -45},
                    yaxis={"title": "Users"},
                    showlegend=False,
                )
                st.plotly_chart(fig_seg, use_container_width=True)

            with col2:
                scored = rfm_filtered[rfm_filtered["purchases"] > 0]
                if len(scored) > 0:
                    sample = scored.sample(min(1500, len(scored)), random_state=42)
                    seg_colors_scatter = {k: v for k, v in seg_colors.items() if k != "Browsing Only"}
                    fig_rfm = px.scatter(
                        sample,
                        x="recency_days", y="revenue",
                        size="purchases", color="Segment",
                        color_discrete_map=seg_colors_scatter,
                        hover_data={"user_id": True, "RFM_Score": True},
                        labels={
                            "recency_days": "Recency (days)",
                            "revenue": "Revenue (Rs.)",
                            "purchases": "Purchases",
                        },
                    )
                    fig_rfm.update_traces(
                        marker=dict(line=dict(color="white", width=0.5)), opacity=0.7
                    )
                    fig_rfm.update_layout(
                        height=350, margin=dict(l=20, r=20, t=20, b=20),
                        hovermode="closest",
                    )
                    st.plotly_chart(fig_rfm, use_container_width=True)

    # ── Data Table ──
    st.divider()
    with st.expander("📋 Raw Data Preview", expanded=False):
        cols_to_show = ["timestamp", "event_type", "channel", "device", "city",
                        "category", "price", "revenue", "session_id"]
        preview_cols = [c for c in cols_to_show if c in filtered.columns]
        st.dataframe(
            filtered[preview_cols].sort_values("timestamp", ascending=False).head(100),
            use_container_width=True,
            height=300,
        )

    # ── Footer ──
    st.divider()
    st.markdown(
        "<p style='text-align: center; color: #95A5A6; font-size: 0.8rem;'>"
        "UserInsights — Web Analytics Dashboard | Built with Streamlit & Plotly</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
