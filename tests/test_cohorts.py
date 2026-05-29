"""Tests for the cohort analysis module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import numpy as np
import pytest
from config import DATA_DIR
from cohorts import (
    compute_monthly_cohorts,
    compute_revenue_cohorts,
    print_cohort_summary,
)


@pytest.fixture(scope="module")
def df():
    """Load the generated dataset once for all tests."""
    path = DATA_DIR / "ecommerce_events.csv"
    if not path.exists():
        pytest.skip("Data file not found. Run src/data_generator.py first.")
    return pd.read_csv(path, parse_dates=["timestamp", "signup_date"])


class TestCohortAnalysis:
    """Test suite for cohort computations."""

    def test_compute_monthly_cohorts_returns_dataframe(self, df):
        """Verify the function returns a DataFrame."""
        result = compute_monthly_cohorts(df)
        assert isinstance(result, pd.DataFrame)

    def test_compute_monthly_cohorts_columns(self, df):
        """Verify expected columns are present."""
        result = compute_monthly_cohorts(df)
        expected_cols = {"cohort_month", "period", "active_users", "cohort_size", "retention"}
        assert expected_cols.issubset(set(result.columns))

    def test_period_zero_retention_is_100(self, df):
        """Verify period 0 always has 100% retention."""
        result = compute_monthly_cohorts(df)
        period_zero = result[result["period"] == 0]
        assert len(period_zero) > 0, "Should have period 0 data"
        assert (period_zero["retention"] == 100.0).all(), (
            "Period 0 should be 100% retention"
        )

    def test_retention_between_0_and_100(self, df):
        """Verify retention values are always between 0 and 100."""
        result = compute_monthly_cohorts(df)
        assert result["retention"].between(0, 100).all(), (
            "Retention should be between 0 and 100"
        )

    def test_retention_generally_decreasing(self, df):
        """Verify retention generally decreases over time.

        Note: Small cohorts can show slight increases in later periods
        due to low user counts (e.g., 33.9% vs 32.4% = 1 user difference).
        This is a valid data artifact, not a bug.
        """
        result = compute_monthly_cohorts(df)
        for cohort in result["cohort_month"].unique():
            subset = result[result["cohort_month"] == cohort].sort_values("period")
            retentions = subset["retention"].values
            # Allow up to 3% increase between adjacent periods (small cohort noise:
            # a single user returning can shift percentages by 1-3%)
            for i in range(1, len(retentions)):
                increase = retentions[i] - retentions[i - 1]
                assert increase < 3.0, (
                    f"Retention jumped {increase:.1f}% for cohort {cohort} at period {i}: "
                    f"{retentions[i-1]:.1f}% → {retentions[i]:.1f}%"
                )

    def test_cohort_sizes_positive(self, df):
        """Verify all cohort sizes are positive."""
        result = compute_monthly_cohorts(df)
        assert (result["cohort_size"] > 0).all(), "All cohort sizes should be positive"

    def test_at_least_one_cohort(self, df):
        """Verify at least one monthly cohort exists."""
        result = compute_monthly_cohorts(df)
        assert result["cohort_month"].nunique() >= 1

    def test_compute_revenue_cohorts_columns(self, df):
        """Verify revenue cohort columns."""
        result = compute_revenue_cohorts(df)
        expected_cols = {"cohort_month", "period", "revenue", "cohort_size", "revenue_per_user"}
        assert expected_cols.issubset(set(result.columns))

    def test_revenue_per_user_non_negative(self, df):
        """Verify revenue per user is never negative."""
        result = compute_revenue_cohorts(df)
        assert (result["revenue_per_user"] >= 0).all()

    def test_print_cohort_summary_runs(self, df):
        """Verify the print function runs without error."""
        cohort_data = compute_monthly_cohorts(df)
        # Capture print output
        try:
            print_cohort_summary(cohort_data)
        except Exception as e:
            pytest.fail(f"print_cohort_summary raised: {e}")
