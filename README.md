# HD & LOW — US Comp Sales Forecast

A Streamlit dashboard that forecasts Home Depot (HD) and Lowe's (LOW) US
comparable sales for the next four fiscal quarters, using only publicly
available data (Census retail sales, Freddie Mac mortgage rates, NAR
existing home sales, Census new home sales, BLS CPI, University of
Michigan consumer sentiment, Census building permits, and the Harvard
Leading Indicator of Remodeling Activity).

## What's here

- `app.py` — the Streamlit app (5 tabs: Overview & Methodology, Comp Sales
  Trend, Industry Trends, Macro Trends, Data Explorer).
- `data_loader.py` — cached loaders that read pre-computed values out of
  `data/HD_LOW_Quarterly_Data.xlsx`.
- `data/HD_LOW_Quarterly_Data.xlsx` — the source workbook. All formulas
  have been recalculated and baked into cached values (via LibreOffice
  headless), so the app can read it with pandas/openpyxl alone — no
  spreadsheet engine required at runtime.
- `requirements.txt` — pinned dependencies for Streamlit Community Cloud.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Important: keeping the data file in sync

If `HD_LOW_Quarterly_Data.xlsx` is ever regenerated or edited (e.g. new
quarterly actuals, updated regression), it MUST be re-recalculated so the
formula results are baked into static values before being placed in
`data/`. Streamlit Community Cloud has no Excel/LibreOffice available to
recalculate formulas at runtime — if a stale/unrecalculated file is
deployed, cells that hold formulas (rather than cached values) will read
back as blank or `None`.

## Methodology summary

Point estimates use simple linear regressions of quarterly comp sales
against a single macro predictor (30-year mortgage rate or consumer
sentiment, chosen per the correlation analysis in the Macro Trends tab),
trained on FY2022 onward to exclude the pandemic-era demand distortion.
See the Overview & Methodology tab in the app, and the accompanying 2-page
synopsis, for the full explanation, limitations, and suggested
supplementary datasets.
