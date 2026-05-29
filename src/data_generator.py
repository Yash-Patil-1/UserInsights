#!/usr/bin/env python3
"""Synthetic e-commerce event data generator for UserInsights project.

Generates realistic user session data with event sequences,
demographics, and purchase behavior over a 6-month period.
"""

import csv
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from config import (
    CATEGORIES,
    CHANNELS,
    CITIES,
    CONVERSION_PROBS,
    DATA_DIR,
    DEVICE_TYPES,
    END_DATE,
    NUM_USERS,
    PRICE_RANGES,
    RANDOM_SEED,
    START_DATE,
)

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def random_date(start: str, end: str) -> datetime:
    """Generate a random datetime between start and end."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    delta = end_dt - start_dt
    random_days = random.random() * delta.days
    random_hours = random.random() * 24
    random_minutes = random.random() * 60
    return start_dt + timedelta(
        days=random_days, hours=random_hours, minutes=random_minutes
    )


def weighted_choice(options: dict) -> str:
    """Pick a key from a dict of {option: weight}."""
    items = list(options.items())
    weights = [w for _, w in items]
    selected = random.choices(items, weights=weights, k=1)[0]
    return selected[0]


def generate_event_timestamps(base_time: datetime, num_events: int) -> list[datetime]:
    """Generate sequential timestamps for events within a session.

    Each event is 30 seconds to 15 minutes after the previous one.
    """
    timestamps = [base_time]
    for _ in range(1, num_events):
        gap = random.randint(30, 900)  # 30 sec to 15 min
        timestamps.append(timestamps[-1] + timedelta(seconds=gap))
    return timestamps


def generate_user_sessions(
    num_users: int = NUM_USERS,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
) -> list[dict]:
    """Generate synthetic e-commerce event data.

    Each user gets 1-8 sessions over the period.
    Each session follows a funnel: visit -> view_product -> add_to_cart -> checkout -> purchase
    with drop-off probabilities at each stage.
    """
    records: list[dict] = []
    user_signup_base = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=365)

    for user_id in range(1, num_users + 1):
        # User attributes (stable across sessions)
        channel = weighted_choice(CHANNELS)
        device = weighted_choice(DEVICE_TYPES)
        city, country, _ = random.choices(
            CITIES, weights=[w for _, _, w in CITIES], k=1
        )[0]

        # Signup date: some users are new, some are existing
        is_new_user = random.random() < 0.15
        signup_date = (
            random_date(start_date, end_date)
            if is_new_user
            else random_date(
                user_signup_base.strftime("%Y-%m-%d"), start_date
            )
        )

        # Number of sessions for this user (Zipf-like distribution)
        num_sessions = np.random.zipf(2.0)
        num_sessions = min(max(num_sessions, 1), 8)

        for session_idx in range(num_sessions):
            session_start = random_date(start_date, end_date)

            # Build event sequence through funnel
            funnel_steps = [
                ("visit", None, 0),
                ("view_product", "visit", 1),
                ("add_to_cart", "view_product", 1),
                ("checkout", "add_to_cart", 1),
                ("purchase", "checkout", 1),
            ]

            session_events = []
            for step_idx, (event_type, prev_event, multiplier) in enumerate(
                funnel_steps
            ):
                if step_idx == 0:
                    # Always start with a visit
                    session_events.append(event_type)
                else:
                    prob_key = {
                        "view_product": "visit_to_view",
                        "add_to_cart": "view_to_cart",
                        "checkout": "cart_to_checkout",
                        "purchase": "checkout_to_purchase",
                    }[event_type]
                    if random.random() < CONVERSION_PROBS[prob_key]:
                        session_events.append(event_type)
                    else:
                        break

            # Keep ALL sessions including bounces (single visit only)
            if len(session_events) < 2:
                # Bounced session — just the visit event, no category/price/revenue
                ts = generate_event_timestamps(session_start, 1)[0]
                records.append(
                    {
                        "user_id": user_id,
                        "session_id": f"{user_id}_{session_start.strftime('%Y%m%d%H%M%S')}",
                        "event_type": "visit",
                        "event_sequence": 1,
                        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": ts.strftime("%Y-%m-%d"),
                        "month": ts.strftime("%Y-%m"),
                        "weekday": ts.strftime("%A"),
                        "hour": ts.hour,
                        "channel": channel,
                        "device": device,
                        "city": city,
                        "country": country,
                        "category": "",
                        "price": 0.0,
                        "revenue": 0.0,
                        "new_user": is_new_user,
                        "signup_date": signup_date.strftime("%Y-%m-%d"),
                    }
                )
                continue

            # For multi-event sessions, assign a category and price
            category = random.choice(CATEGORIES)
            price_min, price_max = PRICE_RANGES[category]
            price = round(random.uniform(price_min, price_max), 2)

            # Generate timestamps
            event_timestamps = generate_event_timestamps(
                session_start, len(session_events)
            )

            for ev_idx, (ev_type, ts) in enumerate(zip(session_events, event_timestamps)):
                revenue = 0.0
                if ev_type == "purchase":
                    # Some purchases are multi-item
                    num_items = random.randint(1, 5)
                    revenue = round(price * num_items, 2)

                records.append(
                    {
                        "user_id": user_id,
                        "session_id": f"{user_id}_{session_start.strftime('%Y%m%d%H%M%S')}",
                        "event_type": ev_type,
                        "event_sequence": ev_idx + 1,
                        "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "date": ts.strftime("%Y-%m-%d"),
                        "month": ts.strftime("%Y-%m"),
                        "weekday": ts.strftime("%A"),
                        "hour": ts.hour,
                        "channel": channel,
                        "device": device,
                        "city": city,
                        "country": country,
                        "category": category if ev_type in ("view_product", "add_to_cart", "checkout", "purchase") else "",
                        "price": price if ev_type in ("view_product", "add_to_cart", "checkout", "purchase") else 0.0,
                        "revenue": revenue,
                        "new_user": is_new_user,
                        "signup_date": signup_date.strftime("%Y-%m-%d"),
                    }
                )

    return records


def main():
    """Generate the dataset and save to CSV."""
    print(f"Generating data for {NUM_USERS} users...")
    records = generate_user_sessions()

    # Sort by timestamp
    records.sort(key=lambda r: r["timestamp"])

    # Save
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = DATA_DIR / "ecommerce_events.csv"

    fieldnames = [
        "user_id", "session_id", "event_type", "event_sequence",
        "timestamp", "date", "month", "weekday", "hour",
        "channel", "device", "city", "country",
        "category", "price", "revenue",
        "new_user", "signup_date",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    users = set(r["user_id"] for r in records)
    sessions = set(r["session_id"] for r in records)
    purchases = [r for r in records if r["event_type"] == "purchase"]
    total_revenue = sum(r["revenue"] for r in purchases)

    print(f"\nDataset generated: {output_path}")
    print(f"  Total events: {len(records):,}")
    print(f"  Unique users: {len(users):,}")
    print(f"  Unique sessions: {len(sessions):,}")
    print(f"  Purchases: {len(purchases):,}")
    print(f"  Total revenue: Rs.{total_revenue:,.2f}")


if __name__ == "__main__":
    main()
