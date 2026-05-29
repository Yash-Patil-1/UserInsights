#!/usr/bin/env python3
"""Cohort analysis for UserInsights project.

Computes monthly retention cohorts and generates an interactive
retention heatmap using Plotly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.graph_objects as go

from config import DATA_DIR, REPORTS_DIR


def load_data() -> pd.DataFrame:
    path = DATA_DIR / "ecommerce_events.csv"
    df = pd.read_csv(path, parse_dates=["timestamp", "signup_date"])
    print(f"Loaded {len(df):,} rows")
    return df


def compute_monthly_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly retention cohorts.

    - Cohort = month of first session (acquisition month)
    - Period = months since cohort month
    - Metric = % of users in cohort who have a session in that period
    """
    # Get each user's first session timestamp (acquisition date)
    first_sessions = (
        df.groupby("user_id")["timestamp"]
        .min()
        .reset_index()
        .rename(columns={"timestamp": "first_session"})
    )
    first_sessions["cohort_month"] = first_sessions["first_session"].dt.to_period("M")

    # Merge cohort month back
    df = df.merge(first_sessions[["user_id", "cohort_month"]], on="user_id")

    # Get activity month for each session
    df["activity_month"] = df["timestamp"].dt.to_period("M")

    # Compute period number (months since cohort)
    df["period"] = (df["activity_month"] - df["cohort_month"]).apply(lambda x: x.n)

    # Count unique users per cohort per period
    cohort_data = (
        df.groupby(["cohort_month", "period"])["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "active_users"})
    )

    # Get total users in each cohort (period 0)
    cohort_sizes = cohort_data[cohort_data["period"] == 0][
        ["cohort_month", "active_users"]
    ].rename(columns={"active_users": "cohort_size"})

    # Merge and compute retention rate
    cohort_data = cohort_data.merge(cohort_sizes, on="cohort_month")
    cohort_data["retention"] = (cohort_data["active_users"] / cohort_data["cohort_size"] * 100).round(1)

    return cohort_data


def compute_revenue_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    """Compute revenue per user per cohort period."""
    first_sessions = (
        df.groupby("user_id")["timestamp"]
        .min()
        .reset_index()
        .rename(columns={"timestamp": "first_session"})
    )
    first_sessions["cohort_month"] = first_sessions["first_session"].dt.to_period("M")
    df = df.merge(first_sessions[["user_id", "cohort_month"]], on="user_id")
    df["activity_month"] = df["timestamp"].dt.to_period("M")
    df["period"] = (df["activity_month"] - df["cohort_month"]).apply(lambda x: x.n)

    # Revenue per cohort per period
    rev = (
        df.groupby(["cohort_month", "period"])["revenue"]
        .sum()
        .reset_index()
    )

    cohort_sizes = (
        df[df["period"] == 0]
        .groupby("cohort_month")["user_id"]
        .nunique()
        .reset_index()
        .rename(columns={"user_id": "cohort_size"})
    )

    rev = rev.merge(cohort_sizes, on="cohort_month")
    rev["revenue_per_user"] = (rev["revenue"] / rev["cohort_size"]).round(2)

    return rev


def plot_retention_heatmap_html(cohort_data: pd.DataFrame) -> str:
    """Create an interactive retention heatmap and save as HTML.

    Returns: Path to saved HTML file.
    """
    pivot = cohort_data.pivot_table(
        index="cohort_month",
        columns="period",
        values="retention",
        aggfunc="first",
    )
    pivot.index = pivot.index.astype(str)
    pivot.columns = [f"Month {c}" for c in pivot.columns]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="YlOrRd",
            text=pivot.values.round(1).astype(str) + "%",
            texttemplate="%{text}",
            textfont={"size": 10},
            hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
            zmin=0,
            zmax=100,
        )
    )

    fig.update_layout(
        title={
            "text": "<b>Monthly Retention Cohorts</b><br><sup>Percentage of users who return each month post-acquisition</sup>",
            "font": {"size": 18},
        },
        xaxis={"title": "Period (Months Since Acquisition)"},
        yaxis={"title": "Acquisition Month (Cohort)", "autorange": "reversed"},
        width=900,
        height=500,
        margin={"l": 100, "r": 50, "t": 100, "b": 80},
    )

    output_path = REPORTS_DIR / "retention_cohorts.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return str(output_path)


def plot_revenue_heatmap_html(rev_data: pd.DataFrame) -> str:
    """Create an interactive revenue-per-user cohort heatmap."""
    pivot = rev_data.pivot_table(
        index="cohort_month",
        columns="period",
        values="revenue_per_user",
        aggfunc="first",
    )
    pivot.index = pivot.index.astype(str)
    pivot.columns = [f"Month {c}" for c in pivot.columns]

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale="Greens",
            text=pivot.values.round(0).astype(int).astype(str),
            texttemplate="Rs.%{text}",
            textfont={"size": 10},
            hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Rev/User: Rs.%{z:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title={
            "text": "<b>Revenue Per User by Cohort</b><br><sup>Average revenue generated per acquired user</sup>",
            "font": {"size": 18},
        },
        xaxis={"title": "Period (Months Since Acquisition)"},
        yaxis={"title": "Acquisition Month (Cohort)", "autorange": "reversed"},
        width=900,
        height=500,
        margin={"l": 100, "r": 50, "t": 100, "b": 80},
    )

    output_path = REPORTS_DIR / "revenue_cohorts.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return str(output_path)


def plot_retention_lines(cohort_data: pd.DataFrame) -> str:
    """Plot retention curves over time for each cohort."""
    fig = go.Figure()

    for cohort in sorted(cohort_data["cohort_month"].unique()):
        subset = cohort_data[cohort_data["cohort_month"] == cohort]
        fig.add_trace(
            go.Scatter(
                x=subset["period"],
                y=subset["retention"],
                mode="lines+markers",
                name=str(cohort),
                line=dict(width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(
        title="<b>Retention Curves by Cohort</b>",
        xaxis={"title": "Months Since Acquisition", "dtick": 1},
        yaxis={"title": "Retention Rate (%)", "range": [0, 100]},
        legend={"title": "Cohort", "font": {"size": 10}},
        width=900,
        height=500,
        margin={"l": 80, "r": 30, "t": 60, "b": 80},
        hovermode="x unified",
    )

    output_path = REPORTS_DIR / "retention_curves.html"
    fig.write_html(str(output_path))
    print(f"  Saved: {output_path}")
    return str(output_path)


def print_cohort_summary(cohort_data: pd.DataFrame):
    """Print key cohort metrics."""
    print("\n" + "=" * 55)
    print("COHORT ANALYSIS SUMMARY")
    print("=" * 55)

    # Overall retention at Month 0 and Month 1
    m0 = cohort_data[cohort_data["period"] == 0]
    m1 = cohort_data[cohort_data["period"] == 1]

    print(f"\nCohorts: {m0['cohort_month'].nunique()} monthly cohorts")
    print(f"Total users acquired: {m0['cohort_size'].sum():,}")
    print(f"Avg Month-0 retention: {m0['retention'].mean():.1f}%")
    if len(m1) > 0:
        print(f"Avg Month-1 retention: {m1['retention'].mean():.1f}%")
        print(f"Month-0 to Month-1 drop: {100 - m1['retention'].mean():.1f}%")

    # Best and worst performing cohorts
    if len(m1) > 0:
        best = m1.loc[m1["retention"].idxmax()]
        worst = m1.loc[m1["retention"].idxmin()]
        print(f"\nBest Month-1 retention: {best['cohort_month']} ({best['retention']:.1f}%)")
        print(f"Worst Month-1 retention: {worst['cohort_month']} ({worst['retention']:.1f}%)")


def main():
    df = load_data()
    print("\nComputing retention cohorts...")
    cohort_data = compute_monthly_cohorts(df)
    print_cohort_summary(cohort_data)

    print("\nComputing revenue cohorts...")
    rev_data = compute_revenue_cohorts(df)

    print("\nGenerating plots...")
    retention_html = plot_retention_heatmap_html(cohort_data)
    revenue_html = plot_revenue_heatmap_html(rev_data)
    curves_html = plot_retention_lines(cohort_data)

    print(f"\nAll cohort outputs saved to: {REPORTS_DIR}")
    print(f"  1. {retention_html}")
    print(f"  2. {revenue_html}")
    print(f"  3. {curves_html}")


if __name__ == "__main__":
    main()
