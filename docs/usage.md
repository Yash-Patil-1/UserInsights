# Usage Guide

## Data Generation

Generate a synthetic e-commerce event dataset:

```bash
python src/data_generator.py
```

The generator creates 10,000 users with sessions spanning October 2025 – March 2026.
Events follow a realistic funnel: visit → view_product → add_to_cart → checkout → purchase.

**Output:** `data/ecommerce_events.csv` (34,000+ rows, 18 columns)

### Configuration

Edit `src/config.py` to control:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `NUM_USERS` | Total users to generate | 10,000 |
| `START_DATE` | Data start date | 2025-10-01 |
| `END_DATE` | Data end date | 2026-03-31 |
| `CHANNELS` | Traffic sources with weights | Organic Search (30%), Direct (20%), etc. |
| `DEVICE_TYPES` | Device mix | Desktop (50%), Mobile (40%), Tablet (10%) |
| `CONVERSION_PROBS` | Funnel stage probabilities | visit→view: 40%, view→cart: 20%, etc. |
| `CITIES` | Geographic distribution | Mumbai, Delhi, Bangalore, New York, London, etc. |
| `CATEGORIES` | Product categories | Electronics, Clothing, Home & Kitchen, Books, etc. |

## Exploratory Data Analysis

```bash
python src/explore.py
```

Generates 7 visualization PNGs in `reports/eda_plots/`:

| Plot | Description |
|------|-------------|
| `funnel.png` | Session-level conversion funnel bar chart |
| `daily_trends.png` | Daily events, active users, and revenue (3-panel) |
| `hourly_heatmap.png` | Day-of-week × hour activity heatmap |
| `channel_performance.png` | Visits/purchases/conversion by channel |
| `device_breakdown.png` | Purchase and revenue by device type |
| `top_cities.png` | Top 10 cities by revenue |
| `new_vs_returning.png` | New vs returning user behavior comparison |

## Cohort Analysis

```bash
python src/cohorts.py
```

Generates 3 interactive HTML files in `reports/`:

| File | Description |
|------|-------------|
| `retention_cohorts.html` | Monthly retention heatmap (% users returning) |
| `revenue_cohorts.html` | Revenue-per-user by cohort and period |
| `retention_curves.html` | Line chart comparing retention across cohorts |

## Funnel Analysis & RFM Segmentation

```bash
python src/segments.py
```

Generates 5 interactive HTML files plus a CSV:

| File | Description |
|------|-------------|
| `funnel_bar.html` | Funnel as horizontal bar chart |
| `funnel_sankey.html` | Funnel as interactive sankey diagram |
| `funnel_by_channel.html` | Channel-level conversion rate curves |
| `rfm_segments.html` | Segment distribution bar + score histogram |
| `rfm_scatter.html` | RFM scatter (recency vs revenue, sized by frequency) |
| `data/rfm_segments.csv` | Per-user RFM scores and segment labels |

### RFM Segments

10 customer segments are identified:

| Segment | Description | Action |
|---------|-------------|--------|
| **Champions** | High recency, high frequency, high spend | Reward & nurture |
| **Loyal Customers** | Regular purchasers with good spend | Upsell & cross-sell |
| **Potential Loyalists** | Moderate recency, frequency, and spend | Engage more |
| **Recent Buyers** | Purchased recently but infrequently | Convert to repeat |
| **Promising** | Show potential, need more engagement | Targeted campaigns |
| **Needs Attention** | Average metrics, room for improvement | Re-engagement |
| **At Risk** | Low recency, previously good spend | Win-back campaign |
| **Can't Lose Them** | Low recency, high spend historically | Urgent re-engagement |
| **Hibernating** | Low on all fronts | Long-term re-activation |
| **Browsing Only** | No purchases yet | Convert first purchase |

## Interactive Dashboard

```bash
streamlit run dashboard.py
```

Opens the dashboard at `http://localhost:8501`.

### Filters

The sidebar provides four filters that apply to all charts simultaneously:

- **Date Range** — Calendar picker (default: all data)
- **Channel** — Traffic source (All, Direct, Email, Organic Search, etc.)
- **Device** — Desktop, Mobile, or Tablet
- **Customer Segment** — Filter by RFM segment (requires RFM data)

### Panels

1. **KPI Cards** — Top metrics always visible at the top
2. **Conversion Funnel** — Interactive plotly funnel with % drop-off
3. **Daily Trends** — Dual-axis: bar = events, line = revenue
4. **Retention Cohorts** — Heatmap updates based on filter selections
5. **Channel Performance** — Grouped bar + conversion rate annotations
6. **Hourly Activity Heatmap** — Day × hour event density
7. **Device & Category Breakdown** — Revenue pie + top categories bar
8. **RFM Segments** — Segment distribution + scatter plot
9. **Raw Data Preview** — Expandable table with latest 100 rows

## Regenerating Reports

After changing configuration or code, regenerate all outputs:

```bash
# Regenerate data
python src/data_generator.py

# Regenerate all reports
python src/explore.py
python src/cohorts.py
python src/segments.py
```

## Examples

### Example 1: Full pipeline run

```bash
python src/data_generator.py && \
python src/explore.py && \
python src/cohorts.py && \
python src/segments.py && \
streamlit run dashboard.py
```

### Example 2: Analyze only specific channels

Generate the data, then use the dashboard filter to select individual channels without regenerating.

### Example 3: Customize the dataset

Edit `src/config.py` to change user count, date range, conversion probabilities, or geographic distribution, then regenerate.
