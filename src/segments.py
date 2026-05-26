#!/usr/bin/env python3
"""Funnel analysis and RFM segmentation for UserInsights project.

Generates:
  - Conversion funnel (overall and segmented by channel)
  - Interactive sankey diagram of the funnel
  - RFM customer segmentation with segment labels (purchasers only)
  - Segment profile table and summary
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from config import DATA_DIR, REPORTS_DIR


def load_data() -> pd.DataFrame:
    path = DATA_DIR / "ecommerce_events.csv"
    if not path.exists():
        print(f"ERROR: Data file not found at {path}")
        print("Run src/data_generator.py first.")
        sys.exit(1)
    df = pd.read_csv(path, parse_dates=["timestamp", "signup_date"])
    print(f"Loaded {len(df):,} rows")
    return df


# ── Funnel Analysis ──────────────────────────────────────────────


def compute_funnel(df: pd.DataFrame) -> dict:
    """Compute overall and segmented conversion funnels."""
    funnel_steps = ["visit", "view_product", "add_to_cart", "checkout", "purchase"]

    # Overall funnel
    overall = {}
    for step in funnel_steps:
        overall[step] = int(df[df["event_type"] == step]["session_id"].nunique())

    # Funnel by channel (first-touch: channel of the visit event)
    visits = df[df["event_type"] == "visit"][["session_id", "channel"]].drop_duplicates("session_id")
    funnel_by_channel = {}
    for channel in sorted(visits["channel"].unique()):
        channel_sessions = set(visits[visits["channel"] == channel]["session_id"])
        funnel_by_channel[channel] = {}
        for step in funnel_steps:
            step_sessions = set(df[df["event_type"] == step]["session_id"])
            funnel_by_channel[channel][step] = len(channel_sessions & step_sessions)

    return {
        "steps": funnel_steps,
        "overall": overall,
        "by_channel": funnel_by_channel,
    }


def plot_funnel_bar_html(funnel: dict) -> Path:
    """Plot the overall funnel as a styled horizontal bar chart."""
    steps = funnel["steps"]
    values = [funnel["overall"][s] for s in steps]
    visit_count = values[0]

    labels = [
        f"{s}<br><span style='font-size:14px'>{v:,} ({v/visit_count*100:.1f}%)</span>"
        for s, v in zip(steps, values)
    ]
    colors = ["#2E86AB", "#A23B72", "#F18F01", "#E85D75", "#3BB273"]

    fig = go.Figure(
        go.Bar(
            x=values[::-1],
            y=labels[::-1],
            orientation="h",
            marker=dict(color=colors[::-1], line=dict(color="white", width=1)),
            text=[f"{v:,}" for v in values[::-1]],
            textposition="outside",
            hovertemplate="%{y}<br>Count: %{x:,}<extra></extra>",
        )
    )

    fig.update_layout(
        title={"text": "<b>Conversion Funnel</b>", "font": {"size": 20}},
        xaxis={"title": "Sessions", "zeroline": False},
        yaxis={"title": None, "autorange": "reversed"},
        height=400,
        margin={"l": 150, "r": 80, "t": 60, "b": 40},
        hovermode="y",
    )

    output_path = REPORTS_DIR / "funnel_bar.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return output_path


def plot_funnel_sankey_html(funnel: dict) -> Path:
    """Plot an interactive Sankey diagram of the conversion funnel."""
    steps = funnel["steps"]
    values = [funnel["overall"][s] for s in steps]
    n = len(steps)

    # Build dynamic label/source/target lists
    labels = []
    sources = []
    targets = []
    link_values = []
    link_colors = []

    funnel_colors = ["rgba(46, 134, 171, 0.3)", "rgba(162, 59, 114, 0.3)",
                     "rgba(241, 143, 1, 0.3)", "rgba(232, 93, 117, 0.3)"]
    dropoff_color = "rgba(200, 200, 200, 0.3)"

    for i in range(n - 1):
        from_label = f"{steps[i]}<br>({values[i]:,})"
        to_label = f"{steps[i+1]}<br>({values[i+1]:,})"

        if i == 0:
            labels.extend([from_label, to_label])
        else:
            labels.append(to_label)

        # Retained flow
        sources.append(i)
        targets.append(i + 1)
        link_values.append(values[i + 1])
        link_colors.append(funnel_colors[i] if i < len(funnel_colors) else dropoff_color)

        # Drop-off flow
        dropoff_label = f"Drop-off<br>({values[i] - values[i+1]:,})"
        labels.append(dropoff_label)
        sources.append(i)
        targets.append(len(labels) - 1)
        link_values.append(values[i] - values[i + 1])
        link_colors.append(dropoff_color)

    node_colors = ["#2E86AB", "#A23B72", "#F18F01", "#E85D75", "#3BB273"]
    while len(node_colors) < len(labels):
        node_colors.append("#CCCCCC")

    fig = go.Figure(
        go.Sankey(
            node=dict(
                pad=20, thickness=25,
                line=dict(color="black", width=0.5),
                label=labels,
                color=node_colors[: len(labels)],
                hovertemplate="%{label}<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=link_values,
                color=link_colors,
            ),
        )
    )

    fig.update_layout(
        title={"text": "<b>Conversion Funnel — Sankey Diagram</b>", "font": {"size": 20}},
        height=500,
        margin={"l": 50, "r": 50, "t": 60, "b": 40},
        font=dict(size=12),
    )

    output_path = REPORTS_DIR / "funnel_sankey.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return output_path


def plot_funnel_by_channel_html(funnel: dict) -> Path:
    """Plot conversion rates by channel as line curves."""
    steps = funnel["steps"]
    channels = list(funnel["by_channel"].keys())
    colors = px.colors.qualitative.Set2[: len(channels)]

    fig = go.Figure()
    for idx, channel in enumerate(channels):
        vals = [funnel["by_channel"][channel][s] for s in steps]
        visit_count = vals[0]
        pcts = [v / visit_count * 100 if v else 0 for v in vals]
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=pcts,
                mode="lines+markers",
                name=channel,
                line=dict(width=3, color=colors[idx]),
                marker=dict(size=10, color=colors[idx]),
                hovertemplate="%{x}<br>%{y:.1f}%<br>(%{customdata:,} visits)",
                customdata=vals,
            )
        )

    fig.update_layout(
        title={"text": "<b>Funnel Conversion Rate by Channel</b>", "font": {"size": 18}},
        xaxis={"title": "Funnel Step"},
        yaxis={"title": "Conversion Rate (% of visits)", "ticksuffix": "%"},
        hovermode="x unified",
        height=500,
        margin={"l": 80, "r": 30, "t": 60, "b": 80},
    )

    output_path = REPORTS_DIR / "funnel_by_channel.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return output_path


def print_funnel_summary(funnel: dict):
    """Print key funnel metrics."""
    print("\n" + "=" * 55)
    print("FUNNEL ANALYSIS SUMMARY")
    print("=" * 55)

    steps = funnel["steps"]
    overall = funnel["overall"]
    visits = overall["visit"]

    print(f"\nOverall Funnel (from {visits:,} visits):")
    for i, step in enumerate(steps):
        val = overall[step]
        pct = val / visits * 100
        drop = ""
        if i > 0:
            prev = overall[steps[i - 1]]
            step_drop = (prev - val) / prev * 100
            drop = f" (step drop-off: {step_drop:.1f}%)"
        print(f"  {step:25s}: {val:>6,} ({pct:5.1f}%){drop}")

    print(f"\nOverall conversion rate (visit -> purchase): {overall['purchase']/visits*100:.1f}%")

    print("\nChannel Conversion Rates (visit -> purchase):")
    for channel, data in sorted(funnel["by_channel"].items()):
        cr = data["purchase"] / data["visit"] * 100 if data["visit"] else 0
        print(f"  {channel:20s}: {cr:5.1f}%")


# ── RFM Segmentation ─────────────────────────────────────────────


def compute_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Recency, Frequency, Monetary scores for purchasing users.

    Only users with at least one purchase receive RFM scores.
    Non-purchasers are labeled as 'Browsing Only'.
    """
    now = df["timestamp"].max() + timedelta(days=1)

    # Separate purchasers and non-purchasers
    purchase_users = set(df[df["event_type"] == "purchase"]["user_id"].unique())
    purchasers_df = df[df["user_id"].isin(purchase_users)].copy()
    browsing_only = df[~df["user_id"].isin(purchase_users)]["user_id"].unique()

    print(f"\n  Purchasing users: {len(purchase_users):,}")
    print(f"  Browsing-only users: {len(browsing_only):,}")

    # For purchasers: per-user aggregates
    rfm = (
        purchasers_df.groupby("user_id")
        .agg(
            last_activity=("timestamp", "max"),
            sessions=("session_id", "nunique"),
            purchases=("event_type", lambda x: (x == "purchase").sum()),
            revenue=("revenue", "sum"),
            first_activity=("timestamp", "min"),
        )
        .reset_index()
    )

    # Last purchase date (from purchase events specifically)
    last_purchase = (
        purchasers_df[purchasers_df["event_type"] == "purchase"]
        .groupby("user_id")["timestamp"]
        .max()
        .reset_index()
        .rename(columns={"timestamp": "last_purchase"})
    )
    rfm = rfm.merge(last_purchase, on="user_id", how="left")

    # Recency: days since last purchase
    rfm["recency_days"] = (now - rfm["last_purchase"]).dt.days

    # Customer lifetime in days
    rfm["lifetime_days"] = (rfm["last_activity"] - rfm["first_activity"]).dt.days.clip(lower=0)

    # Score each dimension 1-5 using quintiles (only for purchasers)
    def score_column(series, reverse=False):
        """Assign 1-5 score based on quintiles. Reverse=True means higher is worse."""
        if series.nunique() < 2:
            return pd.Series([3] * len(series), index=series.index)
        try:
            quintiles = series.quantile([0.2, 0.4, 0.6, 0.8]).values
            if reverse:
                scores = pd.cut(
                    series,
                    bins=[-np.inf] + list(quintiles) + [np.inf],
                    labels=[5, 4, 3, 2, 1],
                )
            else:
                scores = pd.cut(
                    series,
                    bins=[-np.inf] + list(quintiles) + [np.inf],
                    labels=[1, 2, 3, 4, 5],
                )
            return scores.astype(int)
        except (ValueError, IndexError):
            return pd.Series([3] * len(series), index=series.index)

    rfm["R"] = score_column(rfm["recency_days"], reverse=True)
    rfm["F"] = score_column(rfm["purchases"])
    rfm["M"] = score_column(rfm["revenue"])
    rfm["RFM_Score"] = rfm["R"] + rfm["F"] + rfm["M"]

    # Segment labels based on RFM score
    def segment_label(row):
        r, f, m = row["R"], row["F"], row["M"]
        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 4 and f >= 3 and m >= 3:
            return "Loyal Customers"
        elif r >= 4 and f >= 1 and m >= 1:
            return "Recent Buyers"
        elif r >= 3 and f >= 3 and m >= 3:
            return "Potential Loyalists"
        elif r >= 3 and f >= 1 and m >= 1:
            return "Promising"
        elif r >= 2 and f >= 2 and m >= 2:
            return "Needs Attention"
        elif r <= 2 and f >= 2 and m >= 2:
            return "At Risk"
        elif r <= 2 and f <= 2 and m >= 3:
            return "Can't Lose Them"
        elif r <= 2 and f <= 2 and m <= 2:
            return "Hibernating"
        else:
            return "Other"

    rfm["Segment"] = rfm.apply(segment_label, axis=1)

    # Add browsing-only users as a special segment
    browsing_df = pd.DataFrame({
        "user_id": browsing_only,
        "recency_days": 0, "lifetime_days": 0,
        "sessions": 0, "purchases": 0, "revenue": 0,
        "R": 0, "F": 0, "M": 0, "RFM_Score": 0,
        "Segment": "Browsing Only",
    })

    rfm = pd.concat([rfm, browsing_df], ignore_index=True)
    return rfm


def plot_rfm_segments_html(rfm: pd.DataFrame) -> Path:
    """Plot RFM segment distribution as bar and score histogram."""
    segment_order = [
        "Champions", "Loyal Customers", "Potential Loyalists",
        "Recent Buyers", "Promising", "Needs Attention",
        "At Risk", "Can't Lose Them", "Hibernating",
        "Browsing Only", "Other",
    ]

    seg_counts = rfm["Segment"].value_counts()
    seg_counts = seg_counts.reindex([s for s in segment_order if s in seg_counts])

    colors = {
        "Champions": "#2ECC71",
        "Loyal Customers": "#27AE60",
        "Potential Loyalists": "#3498DB",
        "Recent Buyers": "#85C1E9",
        "Promising": "#F39C12",
        "Needs Attention": "#E67E22",
        "At Risk": "#E74C3C",
        "Can't Lose Them": "#C0392B",
        "Hibernating": "#95A5A6",
        "Browsing Only": "#BDC3C7",
        "Other": "#7F8C8D",
    }

    # Filter to scored users only for histogram
    scored = rfm[rfm["RFM_Score"] > 0]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Customer Segments", "RFM Score Distribution (Purchasers)"),
        specs=[[{"type": "bar"}, {"type": "histogram"}]],
    )

    fig.add_trace(
        go.Bar(
            x=seg_counts.index,
            y=seg_counts.values,
            marker=dict(color=[colors.get(s, "#BDC3C7") for s in seg_counts.index]),
            text=seg_counts.values,
            textposition="outside",
            hovertemplate="%{x}<br>Users: %{y:,}<extra></extra>",
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Histogram(
            x=scored["RFM_Score"],
            nbinsx=13,
            marker=dict(color="#3498DB", line=dict(color="white", width=1)),
            hovertemplate="RFM Score: %{x}<br>Users: %{y:,}<extra></extra>",
        ),
        row=1, col=2,
    )

    fig.update_layout(
        title={"text": "<b>RFM Customer Segmentation</b>", "font": {"size": 20}},
        height=450,
        showlegend=False,
        margin={"l": 60, "r": 30, "t": 80, "b": 80},
    )
    fig.update_xaxes(row=1, col=1, tickangle=45)
    fig.update_xaxes(row=1, col=2, title="RFM Score")
    fig.update_yaxes(row=1, col=1, title="Users")

    output_path = REPORTS_DIR / "rfm_segments.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return output_path


def plot_rfm_scatter_html(rfm: pd.DataFrame) -> Path:
    """Plot RFM scatter: Recency vs Monetary, sized by Frequency, colored by Segment."""
    scored = rfm[rfm["RFM_Score"] > 0]
    sample = scored.sample(min(2000, len(scored)), random_state=42)

    segment_colors = {
        "Champions": "#2ECC71",
        "Loyal Customers": "#27AE60",
        "Potential Loyalists": "#3498DB",
        "Recent Buyers": "#85C1E9",
        "Promising": "#F39C12",
        "Needs Attention": "#E67E22",
        "At Risk": "#E74C3C",
        "Can't Lose Them": "#C0392B",
        "Hibernating": "#95A5A6",
    }

    fig = px.scatter(
        sample,
        x="recency_days",
        y="revenue",
        size="purchases",
        color="Segment",
        color_discrete_map=segment_colors,
        hover_data={"user_id": True, "sessions": True, "RFM_Score": True},
        labels={
            "recency_days": "Recency (days since last purchase)",
            "revenue": "Total Revenue (Rs.)",
            "purchases": "Purchase Count",
        },
        title="<b>RFM Scatter: Recency vs Monetary (sized by Frequency)</b>",
    )

    fig.update_traces(marker=dict(line=dict(color="white", width=0.5)), opacity=0.7)
    fig.update_layout(height=600, hovermode="closest",
                      margin={"l": 80, "r": 30, "t": 60, "b": 80})

    output_path = REPORTS_DIR / "rfm_scatter.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return output_path


def print_rfm_summary(rfm: pd.DataFrame):
    """Print RFM segment summary."""
    print("\n" + "=" * 55)
    print("RFM SEGMENTATION SUMMARY")
    print("=" * 55)

    print(f"\nTotal users: {len(rfm):,}")
    print(f"Users with purchases (scored): {rfm[rfm['purchases'] > 0].shape[0]:,}")
    print(f"Total purchases: {rfm['purchases'].sum():,.0f}")
    print(f"Total revenue: Rs.{rfm['revenue'].sum():,.2f}")

    segment_order = [
        "Champions", "Loyal Customers", "Potential Loyalists",
        "Recent Buyers", "Promising", "Needs Attention",
        "At Risk", "Can't Lose Them", "Hibernating",
        "Browsing Only", "Other",
    ]

    print(f"\n{'Segment':25s} {'Users':>8s} {'%':>6s} {'Avg Rev':>10s} {'Avg Purch':>10s}")
    print("-" * 60)
    for seg in segment_order:
        subset = rfm[rfm["Segment"] == seg]
        if len(subset) == 0:
            continue
        pct = len(subset) / len(rfm) * 100
        avg_rev = subset["revenue"].mean()
        avg_purch = subset["purchases"].mean()
        print(f"{seg:25s} {len(subset):>8,} {pct:>5.1f}% Rs.{avg_rev:>7,.0f} {avg_purch:>9.1f}")

    # Revenue contribution by segment (exclude Browsing Only)
    has_rev = rfm[rfm["revenue"] > 0]
    print(f"\nRevenue Contribution by Segment:")
    seg_rev = has_rev.groupby("Segment")["revenue"].sum().sort_values(ascending=False)
    total_rev = seg_rev.sum()
    for seg, rev in seg_rev.items():
        print(f"  {seg:25s}: Rs.{rev:>10,.2f} ({rev/total_rev*100:5.1f}%)")


def main():
    df = load_data()

    # ── Funnel Analysis ──
    print("\nComputing funnel analysis...")
    funnel = compute_funnel(df)
    print_funnel_summary(funnel)

    print("\nGenerating funnel plots...")
    plot_funnel_bar_html(funnel)
    plot_funnel_sankey_html(funnel)
    plot_funnel_by_channel_html(funnel)

    # ── RFM Segmentation ──
    print("\nComputing RFM segmentation...")
    rfm = compute_rfm(df)
    print_rfm_summary(rfm)

    print("\nGenerating RFM plots...")
    plot_rfm_segments_html(rfm)
    plot_rfm_scatter_html(rfm)

    # Save RFM data
    rfm_path = DATA_DIR / "rfm_segments.csv"
    rfm.to_csv(rfm_path, index=False)
    print(f"\n  Saved: {rfm_path}")

    print(f"\nAll Phase 3 outputs saved to: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
