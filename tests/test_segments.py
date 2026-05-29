"""Tests for the funnel and RFM segmentation module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import numpy as np
import pytest
from config import DATA_DIR
from segments import compute_funnel, compute_rfm, print_funnel_summary, print_rfm_summary


@pytest.fixture(scope="module")
def df():
    """Load the generated dataset once for all tests."""
    path = DATA_DIR / "ecommerce_events.csv"
    if not path.exists():
        pytest.skip("Data file not found. Run src/data_generator.py first.")
    return pd.read_csv(path, parse_dates=["timestamp", "signup_date"])


class TestFunnelAnalysis:
    """Test suite for funnel analysis."""

    def test_compute_funnel_returns_dict(self, df):
        """Verify the function returns a dict."""
        result = compute_funnel(df)
        assert isinstance(result, dict)

    def test_funnel_has_expected_keys(self, df):
        """Verify expected keys are present."""
        result = compute_funnel(df)
        assert "steps" in result
        assert "overall" in result
        assert "by_channel" in result

    def test_funnel_steps_in_order(self, df):
        """Verify funnel steps are in the correct order."""
        result = compute_funnel(df)
        expected = ["visit", "view_product", "add_to_cart", "checkout", "purchase"]
        assert result["steps"] == expected

    def test_funnel_counts_non_increasing(self, df):
        """Verify funnel counts are non-increasing (each step <= previous)."""
        result = compute_funnel(df)
        values = [result["overall"][s] for s in result["steps"]]
        for i in range(1, len(values)):
            assert values[i] <= values[i - 1], (
                f"Funnel increased at step {i}: {values[i-1]} → {values[i]}"
            )

    def test_funnel_all_channels_present(self, df):
        """Verify all configured channels appear in the by_channel breakdown."""
        from config import CHANNELS
        result = compute_funnel(df)
        for channel in CHANNELS:
            assert channel in result["by_channel"], f"Missing channel: {channel}"

    def test_print_funnel_summary_runs(self, df):
        """Verify the print function runs without error."""
        funnel = compute_funnel(df)
        try:
            print_funnel_summary(funnel)
        except Exception as e:
            pytest.fail(f"print_funnel_summary raised: {e}")


class TestRFMSegmentation:
    """Test suite for RFM segmentation."""

    def test_compute_rfm_returns_dataframe(self, df):
        """Verify the function returns a DataFrame."""
        result = compute_rfm(df)
        assert isinstance(result, pd.DataFrame)

    def test_rfm_columns(self, df):
        """Verify expected columns are present."""
        result = compute_rfm(df)
        expected = {"user_id", "R", "F", "M", "RFM_Score", "Segment"}
        assert expected.issubset(set(result.columns))

    def test_rfm_total_users(self, df):
        """Verify total users in RFM output matches."""
        result = compute_rfm(df)
        expected_users = df["user_id"].nunique()
        assert len(result) == expected_users, (
            f"Expected {expected_users} users, got {len(result)}"
        )

    def test_rfm_score_range(self, df):
        """Verify R, F, M scores are 1-5 for purchasing users."""
        result = compute_rfm(df)
        scored = result[result["purchases"] > 0]
        if len(scored) > 0:
            for col in ["R", "F", "M"]:
                assert scored[col].between(1, 5).all(), (
                    f"{col} scores should be between 1 and 5"
                )

    def test_rfm_total_score_range(self, df):
        """Verify RFM_Score is 3-15 for purchasing users."""
        result = compute_rfm(df)
        scored = result[result["purchases"] > 0]
        if len(scored) > 0:
            assert scored["RFM_Score"].between(3, 15).all(), (
                "RFM_Score should be 3-15"
            )

    def test_browsing_only_users(self, df):
        """Verify browsing-only users exist and have no purchases."""
        result = compute_rfm(df)
        browsing = result[result["Segment"] == "Browsing Only"]
        assert len(browsing) > 0, "Should have browsing-only users"
        assert (browsing["purchases"] == 0).all()

    def test_known_segments_present(self, df):
        """Verify common segments exist."""
        result = compute_rfm(df)
        segments = set(result["Segment"].unique())
        common_segments = {"Loyal Customers", "Browsing Only", "Other"}
        assert common_segments.issubset(segments), (
            f"Missing common segments. Found: {segments}"
        )

    def test_all_segments_have_valid_names(self, df):
        """Verify all segment names are from the known list."""
        result = compute_rfm(df)
        valid_segments = {
            "Champions", "Loyal Customers", "Potential Loyalists",
            "Recent Buyers", "Promising", "Needs Attention",
            "At Risk", "Can't Lose Them", "Hibernating",
            "Browsing Only", "Other",
        }
        for seg in result["Segment"].unique():
            assert seg in valid_segments, f"Unknown segment: {seg}"

    def test_print_rfm_summary_runs(self, df):
        """Verify the print function runs without error."""
        rfm = compute_rfm(df)
        try:
            print_rfm_summary(rfm)
        except Exception as e:
            pytest.fail(f"print_rfm_summary raised: {e}")
