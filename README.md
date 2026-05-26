<div align="center">

# 📊 UserInsights — Web Analytics & User Behavior Analysis

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://python.org)
[![pandas](https://img.shields.io/badge/pandas-2.0%2B-150458?logo=pandas)](https://pandas.pydata.org)
[![Plotly](https://img.shields.io/badge/Plotly-5.15%2B-3F4F75?logo=plotly)](https://plotly.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**End-to-end customer analytics pipeline — from synthetic data generation to interactive dashboards.**

Analyze user behavior, cohort retention, conversion funnels, and RFM customer segments with real-time filters.

[Features](#-features) • [Quick Start](#-quick-start) • [Dashboard](#-dashboard) • [Project Structure](#-project-structure) • [Key Findings](#-key-findings) • [Documentation](#-documentation)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Synthetic Data Generator** | Generates realistic e-commerce event data (34K+ events, 10K users, 6 months) with configurable conversion probabilities |
| **Exploratory Data Analysis** | 7 automated plots covering funnel, daily trends, hourly heatmap, channel performance, device breakdown, and more |
| **Cohort Analysis** | Monthly retention cohorts with interactive heatmaps, revenue-per-user analysis, and retention curves |
| **Conversion Funnel** | 5-step funnel (visit → view → cart → checkout → purchase) with sankey diagrams and channel-level breakdowns |
| **RFM Segmentation** | Recency-Frequency-Monetary scoring with 10 customer segments — identifies Champions, Loyal Customers, At-Risk, etc. |
| **Interactive Dashboard** | Streamlit dashboard with real-time filters by date, channel, device, and customer segment |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Yash-Patil-1/UserInsights.git
cd UserInsights

# Create a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Generate Data

```bash
python src/data_generator.py
```

This creates `data/ecommerce_events.csv` with ~34,500 events across 10,000 users over a 6-month period.

### Run EDA

```bash
python src/explore.py
```

Generates 7 visualization PNGs in `reports/eda_plots/`.

### Run Cohort & Funnel Analysis

```bash
python src/cohorts.py
python src/segments.py
```

Creates interactive HTML reports in `reports/`.

### Launch Dashboard

```bash
streamlit run dashboard.py
```

Opens the interactive dashboard in your browser.

---

## 🎛️ Dashboard

The Streamlit dashboard provides real-time analytics with:

**Sidebar Filters:**
- 📅 Date range picker
- 📡 Channel selector (Organic Search, Paid Search, Social Media, etc.)
- 📱 Device selector (Desktop, Mobile, Tablet)
- 👥 Customer segment filter (Champions, Loyal Customers, etc.)

**Visualization Panels:**
- **KPI Cards** — Active Users, Sessions, Purchases, Revenue, Purchase Rate
- **Conversion Funnel** — Interactive plotly funnel chart with step-by-step drop-off
- **Daily Trends** — Dual-axis chart (events bar + revenue line)
- **Retention Cohorts** — Monthly retention heatmap (YlOrRd)
- **Channel Performance** — Grouped bar chart with conversion rate annotations
- **Hourly Activity** — Day-of-week × hour heatmap
- **Device Breakdown** — Donut chart by revenue
- **Top Categories** — Revenue by product category
- **RFM Segments** — Segment distribution bar + RFM scatter plot
- **Raw Data** — Expandable data table preview

---

## 📂 Project Structure

```
UserInsights/
├── dashboard.py              # Streamlit interactive dashboard
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT license
├── README.md                 # This file
│
├── src/
│   ├── config.py             # Configuration constants
│   ├── data_generator.py     # Synthetic e-commerce data generator
│   ├── explore.py            # EDA with matplotlib/seaborn plots
│   ├── cohorts.py            # Monthly retention & revenue cohort analysis
│   └── segments.py           # Funnel analysis & RFM customer segmentation
│
├── data/
│   ├── ecommerce_events.csv  # Generated dataset (34K+ events)
│   └── rfm_segments.csv      # Per-user RFM scores & segment labels
│
├── reports/                  # Generated outputs (gitignored)
│   ├── eda_plots/            # 7 PNG EDA charts
│   ├── retention_cohorts.html
│   ├── revenue_cohorts.html
│   ├── retention_curves.html
│   ├── funnel_bar.html
│   ├── funnel_sankey.html
│   ├── funnel_by_channel.html
│   ├── rfm_segments.html
│   └── rfm_scatter.html
│
└── docs/
    ├── getting_started.md    # Setup & quick demo guide
    ├── usage.md              # CLI & dashboard usage reference
    ├── architecture.md       # Pipeline & data model documentation
    └── development.md        # Contributing & development guide
```

---

## 🔍 Key Findings

| Metric | Value |
|--------|-------|
| **Overall Conversion Rate** | 2.8% (visit → purchase) |
| **Month-1 Retention** | 18.7% average (best cohort: Oct 2025 at 32.4%) |
| **Best Channel** | Paid Search (3.2% conversion) |
| **Worst Channel** | Social Media (2.4% conversion) |
| **Loyal Customers** | 151 users driving 45.3% of revenue |
| **Browsing-Only Users** | 94% of users (9,400 of 10,000) |
| **Avg Order Value** | Rs. 38,977 |
| **Total Revenue (6 months)** | Rs. 28.1M |

### Funnel Drop-off Points

| Step Transition | Drop-off Rate |
|----------------|:------------:|
| Visit → View Product | 59.9% |
| View Product → Add to Cart | 80.4% |
| Add to Cart → Checkout | 48.7% |
| Checkout → Purchase | 30.5% |

The biggest drop-off is **View Product → Add to Cart** (80.4%), suggesting pricing or product page improvements could have the largest impact on conversion.

---

## 📚 Documentation

- **[Getting Started](docs/getting_started.md)** — Prerequisites, installation, quick demo
- **[Usage Guide](docs/usage.md)** — Full CLI reference, dashboard guide, examples
- **[Architecture](docs/architecture.md)** — Pipeline stages, data models, design decisions
- **[Development](docs/development.md)** — Dev setup, testing, adding features, contributing

---

## 🛠️ Tech Stack

| Category | Tools |
|----------|-------|
| **Data Processing** | pandas, numpy |
| **Visualization** | matplotlib, seaborn, plotly |
| **Dashboard** | streamlit |
| **Synthetic Data** | numpy (zipf), random |
| **Statistical Analysis** | scikit-learn (quintile scoring) |

---

<div align="center">

Built by [Yash Patil](https://github.com/Yash-Patil-1) — Data Analyst

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?logo=linkedin)](https://linkedin.com/in/yash-patil-997357330)

</div>
