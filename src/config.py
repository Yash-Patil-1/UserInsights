"""Configuration constants for UserInsights."""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
REPORTS_DIR = PROJECT_DIR / "reports"
NOTEBOOKS_DIR = PROJECT_DIR / "notebooks"

# Data generation config
RANDOM_SEED = 42
NUM_USERS = 10000
START_DATE = "2025-10-01"
END_DATE = "2026-03-31"

EVENT_TYPES = ["visit", "view_product", "add_to_cart", "checkout", "purchase"]

CHANNELS = {
    "Organic Search": 0.30,
    "Direct": 0.20,
    "Social Media": 0.18,
    "Paid Search": 0.15,
    "Email": 0.10,
    "Referral": 0.07,
}

DEVICE_TYPES = {
    "Desktop": 0.50,
    "Mobile": 0.40,
    "Tablet": 0.10,
}

CITIES = [
    ("Mumbai", "India", 0.15),
    ("Delhi", "India", 0.12),
    ("Bangalore", "India", 0.10),
    ("Hyderabad", "India", 0.08),
    ("Chennai", "India", 0.07),
    ("Kolkata", "India", 0.06),
    ("Pune", "India", 0.05),
    ("Ahmedabad", "India", 0.04),
    ("New York", "USA", 0.08),
    ("San Francisco", "USA", 0.05),
    ("London", "UK", 0.05),
    ("Berlin", "Germany", 0.03),
    ("Toronto", "Canada", 0.03),
    ("Sydney", "Australia", 0.03),
    ("Dubai", "UAE", 0.03),
    ("Singapore", "Singapore", 0.03),
]

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home & Kitchen",
    "Books",
    "Sports & Outdoors",
    "Beauty",
    "Toys & Games",
    "Food & Grocery",
]

# Conversion probabilities by event type (conditional on preceding event)
# visit -> view_product -> add_to_cart -> checkout -> purchase
CONVERSION_PROBS = {
    "visit_to_view": 0.40,
    "view_to_cart": 0.20,
    "cart_to_checkout": 0.50,
    "checkout_to_purchase": 0.70,
}

# Average prices by category (min, max)
PRICE_RANGES = {
    "Electronics": (500, 150000),
    "Clothing": (299, 15000),
    "Home & Kitchen": (199, 50000),
    "Books": (99, 5000),
    "Sports & Outdoors": (299, 30000),
    "Beauty": (99, 5000),
    "Toys & Games": (149, 10000),
    "Food & Grocery": (10, 3000),
}
