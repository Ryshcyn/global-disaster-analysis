# Global Disaster Analysis

[Chinese overview](README.md) · [English report](reports/case-study.en.md) · [Chinese report](reports/case-study.zh-CN.md)

An exploratory analysis of historical disaster records: distributions, reported economic loss concentration and data coverage.

**Python · Pandas · NumPy · Matplotlib · Plotly · Jupyter**

This project examines when and where disaster impacts are recorded, how reported losses are distributed, and how missing data constrains interpretation.
Data processing, statistical analysis, visualization and report writing were completed independently as a course project.

## Key Findings

The analysis covers **14,329 country-level impact records from 1970–2020**, spanning **228 countries or territories**.
One cross-border disaster can generate several country-level records, so record counts are not counts of distinct global events.

- Floods and storms account for **63.05%** of records.
- Economic loss is missing in **66.62%** of records; deaths are missing in **30.16%**.
- Among **4,783 records with observed economic loss**, the largest **486 (10.16%)** account for 80% of reported loss.
- Loss amounts are nominal USD. Findings describe the historical snapshot, not complete global impacts or causal effects.

![Concentration of reported economic loss](reports/figures/04_loss_concentration.png)

## Explore the Project

- [Full English report](reports/case-study.en.md): raw data structure, cleaning policy, eight figure-by-figure analyses, discussion and limitations.
- [Executed notebook](notebooks/disaster_analysis.ipynb): reproducible computation, tables and embedded charts.
- [Offline interactive country ranking](reports/figures/08_country_explorer.html): download and open in a browser. GitHub does not execute its embedded JavaScript.
- [Summary and input fingerprint](reports/summary.json), [aggregate tables](reports/tables/), and [analysis code](src/).

## Reproduce the Analysis

Python 3.12 is recommended. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Obtain a compatible legacy CSV under its source terms and place it at `data/raw/1970-2021_DISASTERS.csv`.
The recorded source is [ALL NATURAL DISASTERS 1900-2021 / EOSDIS on Kaggle](https://www.kaggle.com/datasets/brsdincer/all-natural-disasters-19002021-eosdis).
The local snapshot has 14,644 rows and 47 columns; current downloads have not been verified as byte-identical.
The [English report](reports/case-study.en.md) explains the required fields and observation grain.

```bash
python -m src.run
python -m unittest discover -s tests -v
python tools/execute_notebook.py
```

Both reports are generated from the same selected population. Use `--input /path/to/file.csv` with `python -m src.run` to supply another location.
A different source version may produce different results. Saved figures, tables and notebook outputs are readable without the raw file.

## Analytical Design

Country-impact IDs are checked for uniqueness and country-code consistency. Counts include unnamed records.
All modules use one 1970–2020 window. Missing impact values remain unknown; entirely missing groups do not become zero totals.
Monthly analysis uses calendar months without assuming a universal hemisphere-based season.
Loss concentration has an explicit observed-loss denominator, and annual monetary totals are shown alongside reporting coverage.

## Repository Structure

```text
src/          Validation, metrics, figures and bilingual report generation
notebooks/    Executed analysis notebook
reports/      Reports, summary, aggregate tables and figures
docs/         Supporting data and methodology documentation in Chinese
tests/        Regression tests for metric and missing-value behavior
tools/        Notebook execution and public archive packaging
data/raw/     Local input; ignored by Git and excluded from public archives
```

## Data and Limitations

Record definitions follow the [EM-DAT country-impact structure](https://doc.emdat.be/docs/data-structure-and-content/core-structure-of-the-database/).
Historical coverage, missing impacts, classification differences and unadjusted prices limit comparisons across countries and time.
This is a descriptive study, not a forecasting or insurance-pricing model.
Raw and row-level processed data are not distributed; third-party data remains subject to its original terms.
