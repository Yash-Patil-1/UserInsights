# Getting Started with UserInsights

## Prerequisites

- **Python 3.9+** — Download from [python.org](https://python.org)
- **pip** — Python package manager (included with Python 3.4+)
- **Git** — For cloning the repository (optional)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Yash-Patil-1/UserInsights.git
cd UserInsights
```

### 2. Create a virtual environment

Using a virtual environment keeps dependencies isolated per project.

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your terminal prompt should now show `(.venv)` at the beginning.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **pandas** — Data manipulation
- **numpy** — Numerical computing
- **matplotlib / seaborn** — Static visualizations
- **plotly** — Interactive visualizations
- **streamlit** — Interactive dashboard
- **jupyter** — Notebook support (optional)
- **scikit-learn** — Statistical scoring utilities

## Quick Demo

Run these commands in order to generate data and see all outputs:

```bash
# Step 1: Generate the synthetic dataset
python src/data_generator.py

# Step 2: Run exploratory data analysis
python src/explore.py

# Step 3: Compute cohort analysis
python src/cohorts.py

# Step 4: Run funnel analysis and RFM segmentation
python src/segments.py

# Step 5: Launch the interactive dashboard
streamlit run dashboard.py
```

## Verify Everything Works

After completing the steps above, check that:

1. **`data/ecommerce_events.csv`** exists and contains ~34,000+ rows
2. **`data/rfm_segments.csv`** exists with 10,000 user records
3. **`reports/`** contains HTML files (retention_cohorts.html, funnel_bar.html, rfm_segments.html, etc.)
4. **`reports/eda_plots/`** contains 7 PNG images
5. **Dashboard** opens in your browser at `http://localhost:8501`

## Next Steps

- Explore the **[Usage Guide](usage.md)** for detailed command reference
- Read the **[Architecture](architecture.md)** to understand the pipeline
- Check the **[Development Guide](development.md)** to learn how to extend the project
