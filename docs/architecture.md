# Architecture

## Pipeline Overview

UserInsights follows a modular pipeline architecture with 5 stages:

```
┌─────────────┐    ┌──────────┐    ┌───────────┐    ┌────────────┐    ┌───────────┐
│  1. Data     │───▶│ 2. EDA   │───▶│ 3. Cohort │───▶│ 4. Funnel │───▶│ 5.       │
│  Generation  │    │          │    │  Analysis │    │ + RFM     │    │ Dashboard │
└─────────────┘    └──────────┘    └───────────┘    └────────────┘    └───────────┘
```

Each stage is independent — you can run any stage without running the previous ones (as long as the data exists).

## Stage 1: Data Generation

**Script:** `src/data_generator.py`

The synthetic data generator creates realistic e-commerce event data using:

- **Funnel simulation** — Each session follows a stochastic funnel where each conversion step has a configurable probability of dropping off
- **Zipf distribution** — Session count per user follows a power-law distribution (most users have few sessions, a few have many)
- **Weighted random selection** — Channels, devices, and cities are assigned based on realistic probability weights
- **Bounce rate inclusion** — 60% of visits result in bounces (no further action), matching real-world e-commerce patterns

### Algorithm

```
For each user (1..N):
    Assign stable attributes: channel, device, city, signup_date
    Generate 1-8 sessions (Zipf-distributed)
    
    For each session:
        Always start with "visit"
        With P(40%): continue to view_product
            With P(20%): continue to add_to_cart
                With P(50%): continue to checkout
                    With P(70%): complete purchase
        Assign timestamps (30s - 15min gaps between events)
```

### Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Synthetic over real data** | Guarantees reproducibility, avoids privacy concerns, includes all expected edge cases |
| **Weights in config** | Makes the generator tunable without code changes |
| **Zipf for session count** | Mirrors real user engagement distributions (Pareto principle) |
| **Included bounces** | Without bounces, funnel analysis would show unrealistically high conversion rates |

## Stage 2: Exploratory Data Analysis

**Script:** `src/explore.py`

Provides summary statistics and 7 visualization PNGs covering:
- **Data overview** — Row count, date range, unique users/sessions
- **Event distribution** — Counts and percentages per event type
- **Conversion funnel** — Drop-off at each stage
- **Temporal patterns** — Daily trends, hourly heatmap
- **Segmentation** — By channel, device, geography, new vs returning users

## Stage 3: Cohort Analysis

**Script:** `src/cohorts.py`

Computes monthly retention cohorts to answer: *"Do users acquired in different months behave differently?"*

### Methodology

1. **Define cohort** — A user's acquisition month = month of their first event
2. **Define period** — Number of months since acquisition (period 0 = acquisition month)
3. **Compute retention** — For each (cohort, period): % of cohort users active in that period
4. **Revenue cohorts** — Same structure but measures revenue per user instead of retention

### Outputs

- Retention heatmap (YlOrRd, 0-100% scale)
- Revenue-per-user heatmap (Greens)
- Retention line curves (one line per cohort)

## Stage 4: Funnel Analysis & RFM Segmentation

**Script:** `src/segments.py`

### Funnel Analysis

Tracks the 5-step customer journey at the session level:

```
Visit (100%) → View Product (40.1%) → Add to Cart (7.9%) → Checkout (4.0%) → Purchase (2.8%)
```

Segmented by channel to identify which traffic sources convert best.

### RFM Segmentation

Scores purchasing users on 3 dimensions (each 1-5):

| Dimension | Measure | Scoring |
|-----------|---------|---------|
| **Recency (R)** | Days since last purchase | More recent = higher score |
| **Frequency (F)** | Number of purchases | More purchases = higher score |
| **Monetary (M)** | Total revenue | Higher spend = higher score |

**Scoring method:** Quintile-based. Users are divided into 5 equal groups per dimension and assigned scores 1-5. Lower recency days = higher R score (inverted).

**Segment classification uses RFM score thresholds** to assign meaningful labels (Champions, At Risk, etc.). Users with no purchases are classified as "Browsing Only."

## Stage 5: Dashboard

**Script:** `dashboard.py`

A Streamlit-based interactive dashboard that ties all analyses together:

- **Caching** — `@st.cache_data` decorators prevent redundant computation on re-render
- **Filters** — UI controls emit boolean masks that compose with `&` operator
- **Visualizations** — All use Plotly for interactivity (hover, zoom, pan, export)

### Data Flow

```
User Input (filters)
    ↓
Load CSV → Apply masks → Compute aggregates → Render Plotly charts
    ↓
Cache layer prevents re-reading CSV on every interaction
```

## Data Model

### `ecommerce_events.csv` — Core Events Table

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | int | Unique user identifier |
| `session_id` | str | Unique session identifier (`{user_id}_{timestamp}`) |
| `event_type` | str | One of: visit, view_product, add_to_cart, checkout, purchase |
| `event_sequence` | int | Event order within session (1, 2, 3...) |
| `timestamp` | datetime | Event timestamp |
| `channel` | str | Traffic source (Organic Search, Direct, etc.) |
| `device` | str | Desktop, Mobile, or Tablet |
| `city` / `country` | str | Geographic location |
| `category` | str | Product category (for product-level events) |
| `price` | float | Product price (for product-level events) |
| `revenue` | float | Revenue (for purchase events only) |
| `new_user` | bool | Whether user signed up during data period |
| `signup_date` | date | User's signup date |

### `rfm_segments.csv` — RFM Scores

| Column | Description |
|--------|-------------|
| `user_id` | User identifier |
| `recency_days` | Days since last purchase |
| `purchases` | Total purchase count |
| `revenue` | Total revenue |
| `R` / `F` / `M` | Individual scores (1-5) |
| `RFM_Score` | Sum of R+F+M (3-15) |
| `Segment` | Customer segment label |

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **CSV as data store** | Simple, portable, no database required — suitable for a portfolio project |
| **HTML reports over screenshots** | Interactive reports let recruiters explore the data |
| **CLI scripts + Dashboard** | Supports both headless analysis (scripts) and visual exploration (dashboard) |
| **Config-driven generation** | Makes the project configurable without modifying source code |
| **Separate script per analysis** | Each script is independently runnable and testable |
