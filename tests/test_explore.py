"""Tests for the EDA module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import pytest
from config import DATA_DIR


@pytest.fixture(scope="module")
def df():
    """Load the generated dataset once for all tests."""
    path = DATA_DIR / "ecommerce_events.csv"
    if not path.exists():
        pytest.skip("Data file not found. Run src/data_generator.py first.")
    return pd.read_csv(path, parse_dates=["timestamp", "signup_date"])


class TestEDA:
    """Test suite for EDA functions."""

    def test_summary_stats_runs(self, df):
        """Verify summary_stats runs without error."""
        from explore import summary_stats
        try:
            summary_stats(df)
        except Exception as e:
            pytest.fail(f"summary_stats raised: {e}")

    def test_plot_functions_run(self, df):
        """Verify all plot functions run without error."""
        from explore import (
            plot_event_funnel, plot_daily_trends, plot_hourly_heatmap,
            plot_channel_performance, plot_device_breakdown,
            plot_top_cities, plot_new_vs_returning,
        )

        # Temporarily redirect matplotlib to Agg (should already be set)
        import matplotlib
        matplotlib.use("Agg")

        for name, func in [
            ("funnel", plot_event_funnel),
            ("daily_trends", plot_daily_trends),
            ("hourly_heatmap", plot_hourly_heatmap),
            ("channel_performance", plot_channel_performance),
            ("device_breakdown", plot_device_breakdown),
            ("top_cities", plot_top_cities),
            ("new_vs_returning", plot_new_vs_returning),
        ]:
            try:
                func(df)
            except Exception as e:
                pytest.fail(f"{name} raised: {e}")
