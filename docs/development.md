# Development Guide

## Development Setup

```bash
# Clone and enter the project
git clone https://github.com/Yash-Patil-1/UserInsights.git
cd UserInsights

# Create virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install with dev dependencies
pip install -r requirements.txt
```

## Project Conventions

### Code Style

- **Python 3.9+** — Use f-strings, type hints, and walrus operator where appropriate
- **PEP 8** — Follow standard Python style (4-space indentation, 88 char line limit)
- **Docstrings** — All modules and functions should have docstrings describing purpose, parameters, and returns
- **Imports** — Standard library → third-party → local (grouped with blank lines)

### File Organization

- **`src/`** — All source scripts (runnable via `python src/<name>.py`)
- **`data/`** — Generated data files (gitignored except for `.gitkeep`)
- **`reports/`** — Generated visualizations (gitignored)
- **`docs/`** — Project documentation (committed)
- **Root** — `dashboard.py`, `requirements.txt`, config files

### Naming

- **Scripts** — Lowercase with underscores (`data_generator.py`, `cohorts.py`)
- **Functions** — Lowercase with underscores (`compute_rfm()`, `plot_funnel_bar_html()`)
- **Constants** — Uppercase with underscores (`DATA_DIR`, `NUM_USERS`)

## Adding a New Analysis Script

1. **Create the script** in `src/` with a clear name (e.g., `src/geo_analysis.py`)
2. **Import config** — Use `from config import DATA_DIR, REPORTS_DIR`
3. **Follow the pattern**:
   ```python
   def load_data() -> pd.DataFrame: ...
   def compute_metrics(df) -> dict: ...
   def plot_results(metrics) -> Path: ...
   def print_summary(metrics): ...
   ```
4. **Update `docs/usage.md`** — Add the new command and output description
5. **Update `README.md`** — Add to the features table and project structure

## Adding a New Dashboard Panel

1. **Edit `dashboard.py`** — Add a new `st.subheader()` + visualization block
2. **Use Plotly** — All dashboard visualizations use plotly for interactivity
3. **Respect filters** — Use the `filtered` DataFrame so the new panel responds to sidebar filters
4. **Handle empty data** — Check `if len(filtered) > 0` or `if len(data) > 0` before rendering

## Modifying the Data Generator

1. **Edit `src/config.py`** — Add or modify constants (new categories, channels, probabilities)
2. **Edit `src/data_generator.py`** — Modify the generation logic if needed
3. **Regenerate data** — Run `python src/data_generator.py`
4. **Regenerate all reports** — Run the full analysis pipeline to verify impacts

## Testing

Currently, the project does not include automated unit tests. To add tests:

1. Create a `tests/` directory in the project root
2. Add `__init__.py` to make it a package
3. Create test files with `pytest` naming convention (e.g., `test_cohorts.py`)
4. Run tests with:
   ```bash
   pytest tests/ -v
   ```

### Suggested Test Coverage Areas

- **Data generator** — Verify output schema, row count ranges, event type distribution
- **Cohort computation** — Validate retention values are between 0-100, period 0 = 100%
- **RFM scoring** — Verify score ranges (1-5), segment classification rules
- **Funnel analysis** — Confirm funnel step ordering and non-increasing counts
- **Dashboard data loading** — Test filter mask composition

## How to Add a New Analysis Dimension (Example)

If you want to add a new analytical dimension to the project:

1. **Add config** in `src/config.py` — e.g., age groups, marketing campaigns
2. **Extend data generator** — Add the new field to the generated events
3. **Create analysis script** — Compute relevant metrics for the new dimension
4. **Add dashboard panel** — Visualize the new findings in the Streamlit dashboard

## Building for Distribution

```bash
# Install build tools
pip install build

# Build wheel and source distribution
python -m build

# Output in dist/
```

## Versioning

The project uses semantic versioning. Current version: **1.0.0**

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Verify all scripts run without errors
5. Update documentation if needed
6. Submit a pull request

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Activate virtual environment, run `pip install -r requirements.txt` |
| Data file missing | Run `python src/data_generator.py` first |
| Plotly not rendering | Check `pip list | grep plotly` — install with `pip install plotly` |
| Dashboard not updating | Check filter selections, ensure data file exists at `data/ecommerce_events.csv` |
| UnicodeEncodeError in terminal | Use PowerShell or set `PYTHONIOENCODING=utf-8` |
