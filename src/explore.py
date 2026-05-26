#!/usr/bin/env python3
"""Exploratory Data Analysis for UserInsights project.

Generates summary statistics and saves plots to the reports/ directory.
Run: python src/explore.py
"""

import sys
from pathlib import Path

# Ensure src is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

from config import DATA_DIR, REPORTS_DIR

plt.rcParams.update({
    "figure.figsize": (12, 6),
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "figure.dpi": 150,
})
sns.set_style("whitegrid")

OUTPUT_DIR = REPORTS_DIR / "eda_plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> pd.DataFrame:
    path = DATA_DIR / "ecommerce_events.csv"
    print(f"Loading data from {path}...")
    df = pd.read_csv(path, parse_dates=["timestamp", "signup_date"])
    print(f"Loaded {len(df):,} rows, {df.columns.size} columns")
    return df


def summary_stats(df: pd.DataFrame):
    """Print key summary statistics."""
    print("\n" + "=" * 55)
    print("DATA SUMMARY")
    print("=" * 55)

    print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
    print(f"Unique users: {df['user_id'].nunique():,}")
    print(f"Unique sessions: {df['session_id'].nunique():,}")
    print(f"Events per session: {df.groupby('session_id').size().mean():.1f} avg")

    print("\nEvent type distribution:")
    event_counts = df["event_type"].value_counts()
    for ev, cnt in event_counts.items():
        pct = cnt / len(df) * 100
        print(f"  {ev:20s}: {cnt:>6,} ({pct:5.1f}%)")

    purchase_df = df[df["event_type"] == "purchase"]
    total_revenue = purchase_df["revenue"].sum()
    print(f"\nTotal revenue: Rs.{total_revenue:,.2f}")
    print(f"Average order value: Rs.{purchase_df['revenue'].mean():,.2f}")
    print(f"Median order value: Rs.{purchase_df['revenue'].median():,.2f}")
    print(f"Purchase rate: {len(purchase_df) / df['session_id'].nunique() * 100:.1f}%")

    print("\nChannel distribution:")
    ch = df[df["event_type"] == "visit"]["channel"].value_counts()
    for c, cnt in ch.items():
        print(f"  {c:20s}: {cnt:>6,} ({cnt/ch.sum()*100:5.1f}%)")


def plot_event_funnel(df: pd.DataFrame):
    """Plot conversion funnel as a horizontal bar chart."""
    funnel = df["event_type"].value_counts()
    order = ["visit", "view_product", "add_to_cart", "checkout", "purchase"]
    funnel = funnel.reindex(order)

    fig, ax = plt.subplots()
    bars = ax.barh(funnel.index, funnel.values, color=plt.cm.Blues(0.3 + 0.15 * np.arange(5)))

    for bar, val in zip(bars, funnel.values):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height() / 2,
                f"{val:,} ({val / funnel['visit'] * 100:.1f}%)",
                va="center", fontsize=11)

    ax.set_xlabel("Event Count")
    ax.set_title("Conversion Funnel")
    ax.margins(x=0.15)
    sns.despine()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "funnel.png")
    plt.close(fig)
    print(f"  Saved: funnel.png")


def plot_daily_trends(df: pd.DataFrame):
    """Plot daily event and revenue trends."""
    daily = df.groupby("date").agg(
        events=("event_type", "count"),
        revenue=("revenue", "sum"),
        users=("user_id", "nunique"),
        purchases=("event_type", lambda x: (x == "purchase").sum()),
    )

    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

    axes[0].plot(daily.index, daily["events"], color="#2E86AB", linewidth=1.5)
    axes[0].set_ylabel("Events")
    axes[0].set_title("Daily Events")

    axes[1].plot(daily.index, daily["users"], color="#A23B72", linewidth=1.5)
    axes[1].set_ylabel("Active Users")
    axes[1].set_title("Daily Active Users")

    axes[2].plot(daily.index, daily["revenue"], color="#F18F01", linewidth=1.5)
    axes[2].set_ylabel("Revenue (Rs.)")
    axes[2].set_title("Daily Revenue")
    axes[2].tick_params(axis="x", rotation=45)

    sns.despine()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "daily_trends.png")
    plt.close(fig)
    print(f"  Saved: daily_trends.png")


def plot_hourly_heatmap(df: pd.DataFrame):
    """Plot hourly activity heatmap."""
    df["day_name"] = pd.Categorical(
        df["weekday"],
        categories=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        ordered=True,
    )
    hourly = df.groupby(["day_name", "hour"], observed=True).size().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(hourly, ax=ax, cmap="YlOrRd", cbar_kws={"label": "Events"}, linewidths=0.5)
    ax.set_title("Hourly Activity Heatmap (by Day of Week)")
    ax.set_ylabel("Day of Week")
    ax.set_xlabel("Hour of Day")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "hourly_heatmap.png")
    plt.close(fig)
    print(f"  Saved: hourly_heatmap.png")


def plot_channel_performance(df: pd.DataFrame):
    """Plot channel-level conversion and revenue."""
    channel_stats = (
        df.groupby("channel")
        .agg(
            visits=("event_type", lambda x: (x == "visit").sum()),
            purchases=("event_type", lambda x: (x == "purchase").sum()),
            revenue=("revenue", "sum"),
        )
        .reset_index()
    )
    channel_stats["conversion_rate"] = channel_stats["purchases"] / channel_stats["visits"] * 100
    channel_stats = channel_stats.sort_values("visits", ascending=True)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Visits & Purchases
    axes[0].barh(channel_stats["channel"], channel_stats["visits"], color="#2E86AB", alpha=0.7, label="Visits")
    axes[0].barh(channel_stats["channel"], channel_stats["purchases"], color="#F18F01", alpha=0.9, label="Purchases")
    axes[0].set_xlabel("Count")
    axes[0].set_title("Visits vs Purchases by Channel")
    axes[0].legend()

    # Conversion rate
    colors = plt.cm.Blues(channel_stats["conversion_rate"] / channel_stats["conversion_rate"].max() * 0.7 + 0.3)
    axes[1].barh(channel_stats["channel"], channel_stats["conversion_rate"], color=colors)
    axes[1].set_xlabel("Conversion Rate (%)")
    axes[1].set_title("Purchase Conversion Rate by Channel")
    for i, v in enumerate(channel_stats["conversion_rate"]):
        axes[1].text(v + 0.1, i, f"{v:.1f}%", va="center")

    sns.despine()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "channel_performance.png")
    plt.close(fig)
    print(f"  Saved: channel_performance.png")


def plot_device_breakdown(df: pd.DataFrame):
    """Plot device type distribution."""
    device_stats = (
        df[df["event_type"] == "purchase"]
        .groupby("device")
        .agg(
            purchases=("event_type", "count"),
            revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    colors = ["#2E86AB", "#A23B72", "#F18F01"]
    axes[0].pie(
        device_stats.set_index("device")["purchases"],
        labels=device_stats["device"],
        autopct="%1.1f%%",
        colors=colors,
        startangle=90,
    )
    axes[0].set_title("Purchases by Device")

    axes[1].bar(device_stats["device"], device_stats["revenue"], color=colors)
    axes[1].set_ylabel("Revenue (Rs.)")
    axes[1].set_title("Revenue by Device")

    sns.despine()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "device_breakdown.png")
    plt.close(fig)
    print(f"  Saved: device_breakdown.png")


def plot_top_cities(df: pd.DataFrame):
    """Plot top cities by revenue."""
    city_rev = (
        df[df["event_type"] == "purchase"]
        .groupby("city")["revenue"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(city_rev)))
    bars = ax.barh(city_rev.index[::-1], city_rev.values[::-1], color=colors[::-1])
    ax.set_xlabel("Revenue (Rs.)")
    ax.set_title("Top 10 Cities by Revenue")
    for bar, val in zip(bars, city_rev.values[::-1]):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height() / 2,
                f"Rs.{val:,.0f}", va="center", fontsize=9)
    sns.despine()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "top_cities.png")
    plt.close(fig)
    print(f"  Saved: top_cities.png")


def plot_new_vs_returning(df: pd.DataFrame):
    """Compare new vs returning user behavior."""
    user_stats = (
        df.groupby("user_id")
        .agg(
            first_event=("timestamp", "min"),
            sessions=("session_id", "nunique"),
            total_revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    first_signup = df[["user_id", "signup_date"]].drop_duplicates()
    user_stats = user_stats.merge(first_signup, on="user_id")

    # Users who signed up before data collection period
    data_start = df["timestamp"].min()
    user_stats["is_new"] = user_stats["signup_date"] >= data_start

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    new_users = user_stats[user_stats["is_new"]]
    returning_users = user_stats[~user_stats["is_new"]]

    # Average sessions per user
    avg_sessions = pd.Series({
        "New Users": new_users["sessions"].mean(),
        "Returning Users": returning_users["sessions"].mean(),
    })
    axes[0].bar(avg_sessions.index, avg_sessions.values, color=["#F18F01", "#2E86AB"])
    axes[0].set_ylabel("Avg Sessions")
    axes[0].set_title("Avg Sessions per User")

    # Revenue comparison
    avg_revenue = pd.Series({
        "New Users": new_users["total_revenue"].mean(),
        "Returning Users": returning_users["total_revenue"].mean(),
    })
    axes[1].bar(avg_revenue.index, avg_revenue.values, color=["#F18F01", "#2E86AB"])
    axes[1].set_ylabel("Avg Revenue (Rs.)")
    axes[1].set_title("Avg Revenue per User")

    sns.despine()
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "new_vs_returning.png")
    plt.close(fig)
    print(f"  Saved: new_vs_returning.png")


def main():
    df = load_data()
    summary_stats(df)
    print("\nGenerating plots...\n")
    plot_event_funnel(df)
    plot_daily_trends(df)
    plot_hourly_heatmap(df)
    plot_channel_performance(df)
    plot_device_breakdown(df)
    plot_top_cities(df)
    plot_new_vs_returning(df)
    print(f"\nAll plots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
