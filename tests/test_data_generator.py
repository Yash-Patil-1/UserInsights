"""Tests for the data generator module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import pytest
from config import DATA_DIR, EVENT_TYPES, CHANNELS, DEVICE_TYPES, CATEGORIES
from data_generator import generate_user_sessions, random_date, weighted_choice


class TestDataGenerator:
    """Test suite for the synthetic data generator."""

    def test_generate_user_sessions_shape(self):
        """Verify the generator produces records with the expected schema."""
        records = generate_user_sessions(num_users=100)
        assert len(records) > 0, "Should generate at least some records"

        # Check all required fields present
        required_fields = [
            "user_id", "session_id", "event_type", "timestamp",
            "channel", "device", "city", "country",
            "category", "price", "revenue",
            "new_user", "signup_date",
        ]
        for field in required_fields:
            assert field in records[0], f"Missing field: {field}"

    def test_generate_user_sessions_event_types(self):
        """Verify all event types are valid."""
        records = generate_user_sessions(num_users=50)
        event_types = set(r["event_type"] for r in records)
        for et in event_types:
            assert et in EVENT_TYPES, f"Invalid event type: {et}"

    def test_generate_user_sessions_no_empty_events(self):
        """Verify no empty event types."""
        records = generate_user_sessions(num_users=50)
        for r in records:
            assert r["event_type"] != "", "Event type should not be empty"

    def test_funnel_sequence(self):
        """Verify events within a session follow the correct order:
        visit → view_product → add_to_cart → checkout → purchase.
        """
        records = generate_user_sessions(num_users=500)
        df = pd.DataFrame(records)

        for session_id in df["session_id"].unique()[:20]:
            session = df[df["session_id"] == session_id].sort_values("event_sequence")
            events = session["event_type"].tolist()
            expected_order = [e for e in EVENT_TYPES if e in events]
            assert events == expected_order, (
                f"Session {session_id}: expected {expected_order}, got {events}"
            )

    def test_channel_distribution(self):
        """Verify channels come from the configured set."""
        records = generate_user_sessions(num_users=100)
        channels = set(r["channel"] for r in records)
        for ch in channels:
            assert ch in CHANNELS, f"Unexpected channel: {ch}"

    def test_device_distribution(self):
        """Verify devices come from the configured set."""
        records = generate_user_sessions(num_users=100)
        devices = set(r["device"] for r in records)
        for d in devices:
            assert d in DEVICE_TYPES, f"Unexpected device: {d}"

    def test_category_assignment(self):
        """Verify product categories are from the configured list."""
        records = generate_user_sessions(num_users=200)
        categories = set(
            r["category"] for r in records if r["category"]
        )
        for cat in categories:
            assert cat in CATEGORIES, f"Unexpected category: {cat}"

    def test_revenue_non_negative(self):
        """Verify revenue is never negative."""
        records = generate_user_sessions(num_users=100)
        for r in records:
            assert r["revenue"] >= 0, f"Negative revenue: {r['revenue']}"

    def test_purchase_revenue_positive(self):
        """Verify purchase events have positive revenue."""
        records = generate_user_sessions(num_users=500)
        purchases = [r for r in records if r["event_type"] == "purchase"]
        if purchases:
            for p in purchases:
                assert p["revenue"] > 0, f"Purchase with zero revenue: {p}"

    def test_random_date(self):
        """Verify random_date generates dates within the expected range."""
        from datetime import datetime
        dt = random_date("2025-10-01", "2025-10-31")
        assert isinstance(dt, datetime)
        assert dt >= datetime(2025, 10, 1)
        assert dt <= datetime(2025, 10, 31)

    def test_weighted_choice(self):
        """Verify weighted_choice selects from the provided options."""
        options = {"A": 0.5, "B": 0.3, "C": 0.2}
        results = set()
        for _ in range(100):
            results.add(weighted_choice(options))
        assert results == {"A", "B", "C"}, "Should select all options over many trials"

    def test_conversion_rate_range(self):
        """Verify overall conversion rate is within reasonable bounds."""
        records = generate_user_sessions(num_users=3000)
        df = pd.DataFrame(records)
        visits = len(df[df["event_type"] == "visit"]["session_id"].unique())
        purchases = len(df[df["event_type"] == "purchase"]["session_id"].unique())
        if visits > 0:
            rate = purchases / visits * 100
            # Expected rate: 0.40 * 0.20 * 0.50 * 0.70 = 2.8%
            # Bounds: generous to account for random variation
            assert 0.5 <= rate <= 8.0, f"Conversion rate {rate:.1f}% out of expected range"
